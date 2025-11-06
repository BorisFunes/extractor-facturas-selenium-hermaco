from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import glob
import json
from pathlib import Path
from datetime import datetime
import shutil

# Configuración de carpetas
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "descargas_erp")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Crear carpeta de backup con fecha actual
fecha_backup = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_FOLDER = os.path.join(os.getcwd(), f"backup_{fecha_backup}")
os.makedirs(BACKUP_FOLDER, exist_ok=True)

print(f"📁 Carpeta de backup creada: {BACKUP_FOLDER}")

# Configuración de Chrome para descargas automáticas
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": DOWNLOAD_FOLDER,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True,
    "safebrowsing.enabled": True,
}
chrome_options.add_experimental_option("prefs", prefs)

# Inicializar el navegador
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=chrome_options
)

# Listas para tracking
registros_fallidos = []
facturas_anuladas = []
ultimo_dte_exitoso = None
pagina_ultimo_dte_exitoso = None


def guardar_backup_ultimo_exitoso():
    """Guarda una copia del último DTE exitoso en la carpeta de backup"""
    if ultimo_dte_exitoso:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_backup = os.path.join(
            BACKUP_FOLDER, f"ultimo_dte_exitoso_{timestamp}.json"
        )

        with open(archivo_backup, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_reporte": datetime.now().isoformat(),
                    "ultimo_dte": ultimo_dte_exitoso,
                    "pagina": pagina_ultimo_dte_exitoso,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"💾 Backup guardado: {archivo_backup}")


def contar_archivos_iniciales():
    """Cuenta los archivos PDF y JSON que ya existen en la carpeta de descargas"""
    pdfs = len(glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.pdf")))
    jsons_facturas = len(
        [
            f
            for f in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.json"))
            if not (
                "registros_fallidos" in f
                or "ultimo_dte_exitoso" in f
                or "facturas_anuladas" in f
            )
        ]
    )
    return pdfs, jsons_facturas


def leer_ultimo_dte_exitoso():
    """Lee el último DTE exitoso del archivo JSON más reciente"""
    try:
        archivos_ultimo_dte = glob.glob(
            os.path.join(DOWNLOAD_FOLDER, "ultimo_dte_exitoso_*.json")
        )
        if not archivos_ultimo_dte:
            print(
                "ℹ️ No se encontró archivo de último DTE exitoso. Se procesarán todas las páginas."
            )
            return None, None

        # Obtener el archivo más reciente
        archivo_mas_reciente = max(archivos_ultimo_dte, key=os.path.getmtime)

        with open(archivo_mas_reciente, "r", encoding="utf-8") as f:
            data = json.load(f)
            ultimo_dte = data.get("ultimo_dte")
            pagina = data.get("pagina", None)

            if ultimo_dte:
                print(f"✅ Último DTE exitoso encontrado: {ultimo_dte}")
                if pagina:
                    print(f"   📄 Última página procesada: {pagina}")
                return ultimo_dte, pagina
            else:
                print("⚠️ Archivo de último DTE exitoso vacío.")
                return None, None

    except Exception as e:
        print(f"⚠️ Error al leer último DTE exitoso: {e}")
        return None, None


def buscar_dte_en_pagina(driver, dte_buscado):
    """
    Busca un DTE específico en la página actual.
    Retorna el índice de la fila si lo encuentra, o None si no lo encuentra.
    """
    try:
        filas = driver.find_elements(
            By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
        )

        for idx, fila in enumerate(filas):
            dte_actual = extraer_dte_de_fila(fila)
            if dte_actual == dte_buscado:
                print(f"  ✅ DTE encontrado en la fila {idx + 1}")
                return idx

        print(f"  ℹ️ DTE {dte_buscado} no encontrado en esta página")
        return None

    except Exception as e:
        print(f"  ⚠️ Error al buscar DTE en página: {e}")
        return None


def verificar_factura_anulada(driver, fila):
    """
    Verifica si una factura está anulada buscando el texto 'anulada' en la fila
    """
    try:
        texto_fila = fila.text.lower()
        if "anulada" in texto_fila or "anulado" in texto_fila:
            print("  ⚠️ FACTURA ANULADA detectada")
            return True
        return False
    except Exception as e:
        print(f"  ⚠️ Error al verificar si está anulada: {e}")
        return False


def cerrar_dropdowns_abiertos(driver):
    """Cierra cualquier dropdown que esté abierto haciendo clic en un área neutral"""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        ActionChains(driver).move_to_element(body).move_by_offset(
            -200, -200
        ).click().perform()
        time.sleep(0.5)
        print("  🔒 Dropdowns cerrados")
    except Exception:
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            print("  🔒 Dropdowns cerrados con ESC")
        except:
            print("  ⚠️ No se pudieron cerrar dropdowns, continuando...")


def scroll_to_element(driver, element):
    """Hace scroll hasta el elemento para asegurarse de que esté visible"""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.5)


def scroll_to_bottom(driver):
    """Hace scroll hasta el final de la página"""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    print("  ⬇️ Scroll hasta el final de la página")


def click_impresion_de_fila(driver, fila, wait):
    """
    Hace click en 'Impresión' (por clase o por texto) SOLO dentro del dropdown visible de esta fila.
    """

    def obtener_menu_visible(_):
        menus = fila.find_elements(By.XPATH, ".//ul[contains(@class,'dropdown-menu')]")
        visibles = [m for m in menus if m.is_displayed()]
        return visibles[0] if visibles else False

    menu = WebDriverWait(driver, 8).until(obtener_menu_visible)

    candidatos = menu.find_elements(
        By.XPATH,
        ".//a[contains(concat(' ', normalize-space(@class), ' '), ' print-invoice ') "
        " or contains(normalize-space(.), 'Impresión')]",
    )
    if not candidatos:
        raise Exception("No se encontró 'Impresión' en el menú de esta fila")

    objetivo = next((c for c in candidatos if c.is_displayed()), candidatos[0])
    driver.execute_script("arguments[0].scrollIntoView({block:'nearest'});", objetivo)
    time.sleep(0.2)
    try:
        objetivo.click()
    except:
        driver.execute_script("arguments[0].click();", objetivo)


def cambiar_a_nueva_ventana(driver, ventana_original):
    """Cambia el contexto a la nueva ventana abierta"""
    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
    for ventana in driver.window_handles:
        if ventana != ventana_original:
            driver.switch_to.window(ventana)
            print("  ✅ Cambiado a nueva ventana")
            return True
    return False


def esperar_descarga_completa(carpeta, timeout=30):
    """Espera a que se complete la descarga (sin archivos .crdownload o .tmp)"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        temporales = glob.glob(os.path.join(carpeta, "*.crdownload")) + glob.glob(
            os.path.join(carpeta, "*.tmp")
        )
        if not temporales:
            time.sleep(1)
            return True
        time.sleep(0.5)
    return False


def obtener_ultimo_archivo_descargado(carpeta, extension):
    """Obtiene el archivo más reciente con la extensión especificada"""
    archivos = glob.glob(os.path.join(carpeta, f"*.{extension}"))
    return max(archivos, key=os.path.getmtime) if archivos else None


def sanitize_filename(name: str) -> str:
    """Limpia caracteres no válidos para nombres de archivo."""
    invalid = '<>:"/\\|?*'
    cleaned = name.strip()
    for ch in invalid:
        cleaned = cleaned.replace(ch, "_")
    return cleaned


def extraer_dte_de_fila(fila):
    """
    Busca en la fila una celda que contenga el texto del DTE (p.ej. 'DTE-03-S002P001-000000000000686')
    y lo retorna. Devuelve None si no lo encuentra.
    """
    try:
        celda = fila.find_element(
            By.XPATH, ".//td[contains(normalize-space(.), 'DTE-')]"
        )
        dte = celda.text.strip()
        if dte and "DTE-" in dte:
            return dte
    except Exception:
        pass
    return None


def descargar_pdf_y_json(
    driver, wait, carpeta_descargas, nombre_base, numero_factura=None
):
    """
    Descarga PDF y JSON de la ventana actual y los renombra con 'nombre_base' (el DTE).
    Si no se pasa nombre_base, intenta usar el ID de la URL; si falla, usa 'factura_{numero_factura}'.
    """
    descargas_exitosas = 0
    factura_id = None

    try:
        # Intentar obtener ID de la URL del PDF (fallback si no hay DTE)
        try:
            boton_pdf = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//a[@class='btn-download-action' and contains(@href, '/pdf/')]",
                    )
                )
            )
            url_pdf = boton_pdf.get_attribute("href")
            factura_id = (
                url_pdf.split("/pdf/")[-1] if url_pdf and "/pdf/" in url_pdf else None
            )
            if factura_id:
                print(f"  📋 ID de factura detectado: {factura_id}")
        except Exception as e:
            print(f"  ⚠️ No se pudo obtener el ID de la factura: {e}")

        base = (
            sanitize_filename(nombre_base)
            if nombre_base
            else (factura_id or f"factura_{numero_factura}")
        )

        # Descargar PDF
        try:
            boton_pdf = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//a[@class='btn-download-action' and contains(@href, '/pdf/')]",
                    )
                )
            )
            boton_pdf.click()
            print("  ⬇️ Click en descarga PDF (continuará en segundo plano)...")
            descargas_exitosas += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ No se pudo hacer click en PDF: {e}")

        # Descargar JSON
        try:
            boton_json = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//a[@class='btn-download-action' and contains(@href, '/json/')]",
                    )
                )
            )
            boton_json.click()
            print("  ⬇️ Click en descarga JSON (continuará en segundo plano)...")
            descargas_exitosas += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ No se pudo hacer click en JSON: {e}")

        if descargas_exitosas == 2:
            print("  🎉 Ambos clicks de descarga ejecutados")
            return True
        else:
            print(f"  ⚠️ Solo se ejecutaron {descargas_exitosas}/2 clicks de descarga")
            return False

    except Exception as e:
        print(f"  ❌ Error al iniciar descargas: {e}")
        return False


def procesar_registro_con_reintentos(
    driver, fila, idx, ventana_principal, wait, pagina_actual=None, max_reintentos=3
):
    """
    Procesa un registro con sistema de reintentos (3 intentos con pausa en el último).
    Si no encuentra el botón de impresión después de 3 intentos, verifica si está anulada.
    """
    global ultimo_dte_exitoso
    global pagina_ultimo_dte_exitoso

    dte = extraer_dte_de_fila(fila)
    if dte:
        print(f"  🏷️ DTE detectado: {dte}")
    else:
        print(
            "  ⚠️ No se pudo detectar DTE en la fila. Se usará ID/índice como fallback."
        )

    for intento in range(1, max_reintentos + 1):
        try:
            print(f"  🔄 Intento {intento}/{max_reintentos}")

            # Si es el tercer intento, esperar 1 segundo antes de intentar
            if intento == 3:
                print("  ⏱️ Pausa de 1 segundo antes del último intento...")
                time.sleep(1)

            # Re-obtener la fila para evitar stale elements
            driver.switch_to.window(ventana_principal)
            filas = driver.find_elements(
                By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
            )
            if idx >= len(filas):
                print("  ⚠️ La fila ya no está disponible.")
                return False
            fila = filas[idx]

            # Hacer scroll a la fila
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", fila
            )
            time.sleep(0.3)

            # Re-extraer DTE por si acaso
            if not dte:
                dte = extraer_dte_de_fila(fila)

            # Click en "Acciones"
            try:
                boton_acciones = fila.find_element(By.CLASS_NAME, "btn-actions")
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", boton_acciones
                )
                time.sleep(0.1)
                try:
                    boton_acciones.click()
                except:
                    driver.execute_script("arguments[0].click();", boton_acciones)
                print("  ✅ Click en 'Acciones'")
                time.sleep(0.2)
            except Exception as e:
                print(f"  ❌ No se pudo hacer click en 'Acciones': {e}")
                if intento < max_reintentos:
                    continue
                else:
                    raise

            # Click en "Impresión"
            try:
                click_impresion_de_fila(driver, fila, wait)
                print("  ✅ Click en 'Impresión' - Se abre nueva ventana")
                time.sleep(0.3)
            except Exception as e:
                print(f"  ❌ No se pudo hacer click en 'Impresión': {e}")

                # Si es el último intento y no se encontró el botón, verificar si está anulada
                if intento == max_reintentos:
                    print("  🔍 Verificando si la factura está anulada...")

                    # Cerrar el dropdown
                    cerrar_dropdowns_abiertos(driver)
                    time.sleep(0.3)

                    # Re-obtener la fila
                    filas = driver.find_elements(
                        By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
                    )
                    if idx < len(filas):
                        fila = filas[idx]

                        if verificar_factura_anulada(driver, fila):
                            # Marcar como anulada
                            facturas_anuladas.append(
                                {
                                    "posicion": idx + 1,
                                    "pagina": pagina_actual,
                                    "dte": dte if dte else f"registro_{idx + 1}",
                                    "fecha": datetime.now().isoformat(),
                                    "motivo": "Factura anulada - Sin botón de impresión",
                                }
                            )
                            print(
                                f"  📝 Factura marcada como ANULADA y guardada en registro"
                            )
                            return False

                    # Si no está anulada, se marca como fallida
                    raise
                else:
                    continue

            # Cambiar a la nueva ventana y descargar
            if cambiar_a_nueva_ventana(driver, ventana_principal):
                time.sleep(0.5)

                if descargar_pdf_y_json(driver, wait, DOWNLOAD_FOLDER, dte, idx + 1):
                    print("  ✅ Descargas iniciadas correctamente")
                    ultimo_dte_exitoso = dte if dte else f"registro_{idx + 1}"
                    pagina_ultimo_dte_exitoso = pagina_actual

                    # Guardar backup inmediatamente
                    guardar_backup_ultimo_exitoso()

                    driver.close()
                    driver.switch_to.window(ventana_principal)
                    return True
                else:
                    print("  ⚠️ Problemas con descargas")
                    driver.close()
                    driver.switch_to.window(ventana_principal)
                    if intento < max_reintentos:
                        continue
                    else:
                        return False
            else:
                print("  ⚠️ No se pudo cambiar a la nueva ventana")
                if intento < max_reintentos:
                    continue
                else:
                    return False

        except Exception as e:
            print(f"  ❌ Error en intento {intento}: {e}")
            try:
                if len(driver.window_handles) > 1:
                    for handle in driver.window_handles:
                        if handle != ventana_principal:
                            driver.switch_to.window(handle)
                            driver.close()
                driver.switch_to.window(ventana_principal)
                time.sleep(0.2)
            except:
                pass

            if intento < max_reintentos:
                continue
            else:
                return False

    return False


def guardar_reporte_json(pagina_actual=None):
    """
    Guarda los reportes JSON al finalizar
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Guardar registros fallidos
    if registros_fallidos:
        archivo_fallidos = os.path.join(
            DOWNLOAD_FOLDER, f"registros_fallidos_{timestamp}.json"
        )
        with open(archivo_fallidos, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_reporte": datetime.now().isoformat(),
                    "total_fallidos": len(registros_fallidos),
                    "registros": registros_fallidos,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\n📄 Reporte de fallidos guardado: {archivo_fallidos}")

    # Guardar facturas anuladas
    if facturas_anuladas:
        archivo_anuladas = os.path.join(
            DOWNLOAD_FOLDER, f"facturas_anuladas_{timestamp}.json"
        )
        with open(archivo_anuladas, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_reporte": datetime.now().isoformat(),
                    "total_anuladas": len(facturas_anuladas),
                    "facturas": facturas_anuladas,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"📄 Reporte de anuladas guardado: {archivo_anuladas}")

    # Guardar último DTE exitoso
    if ultimo_dte_exitoso:
        archivo_ultimo = os.path.join(
            DOWNLOAD_FOLDER, f"ultimo_dte_exitoso_{timestamp}.json"
        )
        with open(archivo_ultimo, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_reporte": datetime.now().isoformat(),
                    "ultimo_dte": ultimo_dte_exitoso,
                    "pagina": pagina_actual,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"📄 Último DTE exitoso guardado: {archivo_ultimo}")
        if pagina_actual:
            print(f"   📄 Página: {pagina_actual}")

        # También guardar en backup
        guardar_backup_ultimo_exitoso()


try:
    # Contar archivos iniciales
    print("📊 Contando archivos existentes en la carpeta de descargas...")
    pdfs_iniciales, jsons_iniciales = contar_archivos_iniciales()
    print(f"   📄 PDFs existentes: {pdfs_iniciales}")
    print(f"   📄 JSONs existentes: {jsons_iniciales}")
    print(f"   📦 Total archivos iniciales: {pdfs_iniciales + jsons_iniciales}")

    # Leer último DTE exitoso
    print("\n🔍 Buscando último DTE procesado...")
    ultimo_dte_procesado, pagina_ultimo_dte = leer_ultimo_dte_exitoso()

    # Maximizar ventana
    driver.maximize_window()
    print("\n🚀 Iniciando navegador...")

    # URL de tu ERP
    URL_ERP = "https://hermaco.findexbusiness.com"
    driver.get(URL_ERP)
    print(f"📍 Navegando a: {URL_ERP}")

    wait = WebDriverWait(driver, 10)

    # Click en "Inicio de sesión"
    login_link = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='https://hermaco.findexbusiness.com/login']")
        )
    )
    login_link.click()
    print("✅ Click en 'Inicio de sesión'")

    time.sleep(2)
    print("🔄 Rellenando credenciales...")

    # Rellenar usuario
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    username_input.send_keys("Henri")
    print("✅ Usuario ingresado")

    # Rellenar contraseña
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys("Bajmut")
    print("✅ Contraseña ingresada")

    # Click en botón de login
    login_button = driver.find_element(
        By.XPATH, "//button[@type='submit' and contains(@class, 'btn-primary')]"
    )
    login_button.click()
    print("✅ Click en botón 'Acceder'")

    time.sleep(3)
    print("✅ Login completado, esperando dashboard...")

    # Navegar a Gestión de ventas
    print("\n🔄 Navegando a 'Gestión de ventas'...")
    gestion_ventas = wait.until(EC.element_to_be_clickable((By.ID, "tour_step7_menu")))
    gestion_ventas.click()
    print("✅ Click en 'Gestión de ventas' (desplegable abierto)")

    time.sleep(1)

    # Click en "Todas las ventas"
    todas_ventas = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='https://hermaco.findexbusiness.com/sells']")
        )
    )
    todas_ventas.click()
    print("✅ Click en 'Todas las ventas'")

    time.sleep(2)
    print("📍 Estamos en la página de facturas")

    # Filtro de fecha
    print("\n🔄 Abriendo filtro de fecha...")
    filtro_fecha = wait.until(EC.element_to_be_clickable((By.ID, "sell_date_filter")))
    filtro_fecha.click()
    print("✅ Click en 'Filtrar por fecha' (desplegable abierto)")

    time.sleep(2)
    try:
        ejercicio_actual = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//li[contains(text(), 'Ejercicio actual')] | //a[contains(text(), 'Ejercicio actual')] | //span[contains(text(), 'Ejercicio actual')]",
                )
            )
        )
        ejercicio_actual.click()
        print("✅ Seleccionado 'Ejercicio actual'")
    except:
        print("⚠️ No se encontró 'Ejercicio actual'. Inspecciona el desplegable.")

    time.sleep(3)

    # Mostrar 100 registros por página
    print("\n🔄 Cambiando filtro a 100 registros por página...")
    select_length = wait.until(
        EC.presence_of_element_located((By.NAME, "sell_table_length"))
    )
    try:
        Select(select_length).select_by_value("100")
        print("✅ Seleccionado 100 registros por página")
    except Exception as e:
        print(f"  ❌ No se pudo cambiar el tamaño de página: {e}")
        driver.quit()
        exit(1)

    # Dar tiempo a que carguen los registros
    print("⏳ Esperando 5 segundos a que carguen los registros...")
    time.sleep(5)
    print("✅ Registros cargados")

    # Dar tiempo a que carguen los registros
    print("⏳ Esperando 5 segundos a que carguen los registros...")
    time.sleep(5)
    print("✅ Registros cargados")

    # Navegar a la última página del paginador
    print("\n🔄 Navegando a la última página...")
    scroll_to_bottom(driver)
    time.sleep(1)

    numero_ultima_pagina = None
    pagina_inicio = None

    try:
        # Buscar todos los botones de página y seleccionar el último número
        botones_pagina = driver.find_elements(
            By.XPATH,
            "//div[@id='sell_table_paginate']//li[contains(@class, 'paginate_button') and not(contains(@class, 'previous')) and not(contains(@class, 'next')) and not(contains(@class, 'disabled'))]//a",
        )

        if botones_pagina:
            # Obtener el último botón de página (el número más alto)
            ultimo_boton = botones_pagina[-1]
            numero_ultima_pagina = ultimo_boton.text.strip()
            print(f"📄 Última página detectada: {numero_ultima_pagina}")

            # Click en la última página
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", ultimo_boton
            )
            time.sleep(0.5)
            ultimo_boton.click()
            print(f"✅ Navegado a la página {numero_ultima_pagina}")
            time.sleep(3)  # Esperar a que cargue la página

            # Determinar página de inicio según si hay DTE previo
            if ultimo_dte_procesado and pagina_ultimo_dte:
                # Si hay un DTE previo, navegar a esa página
                print(
                    f"\n🔍 Buscando página {pagina_ultimo_dte} del último DTE procesado..."
                )
                scroll_to_bottom(driver)
                time.sleep(1)

                # Obtener página actual
                try:
                    pagina_activa = driver.find_element(
                        By.XPATH,
                        "//div[@id='sell_table_paginate']//li[contains(@class, 'paginate_button') and contains(@class, 'active')]//a",
                    )
                    pagina_actual_num = int(pagina_activa.text.strip())
                except:
                    pagina_actual_num = int(numero_ultima_pagina)

                pagina_objetivo = int(pagina_ultimo_dte)
                clicks_necesarios = pagina_actual_num - pagina_objetivo

                print(f"   📄 Página actual: {pagina_actual_num}")
                print(f"   🎯 Página objetivo: {pagina_objetivo}")
                print(f"   ⬅️ Clicks necesarios en 'Anterior': {clicks_necesarios}")

                # Navegar hacia atrás hasta la página del último DTE
                for i in range(clicks_necesarios):
                    try:
                        scroll_to_bottom(driver)
                        time.sleep(0.5)

                        # Verificar si el botón está visible en el paginador
                        try:
                            boton_directo = driver.find_element(
                                By.XPATH,
                                f"//div[@id='sell_table_paginate']//li[contains(@class, 'paginate_button')]//a[normalize-space(text())='{pagina_objetivo}']",
                            )
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                boton_directo,
                            )
                            time.sleep(0.3)
                            boton_directo.click()
                            print(f"✅ Click directo en página {pagina_objetivo}")
                            time.sleep(2)
                            break
                        except:
                            # Si no está visible, usar botón "Anterior"
                            boton_anterior = driver.find_element(
                                By.XPATH,
                                "//div[@id='sell_table_paginate']//li[@id='sell_table_previous' and not(contains(@class, 'disabled'))]//a",
                            )
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                boton_anterior,
                            )
                            time.sleep(0.3)
                            boton_anterior.click()

                            # Obtener nueva página actual
                            time.sleep(1.5)
                            try:
                                pagina_activa = driver.find_element(
                                    By.XPATH,
                                    "//div[@id='sell_table_paginate']//li[contains(@class, 'paginate_button') and contains(@class, 'active')]//a",
                                )
                                nueva_pagina = pagina_activa.text.strip()
                                print(
                                    f"✅ Click en 'Anterior' - Ahora en página {nueva_pagina}"
                                )

                                if int(nueva_pagina) == pagina_objetivo:
                                    print(
                                        f"🎯 Llegamos a la página objetivo {pagina_objetivo}"
                                    )
                                    break
                            except:
                                print(
                                    f"✅ Click en 'Anterior' ({i+1}/{clicks_necesarios})"
                                )

                    except Exception as e2:
                        print(f"❌ Error al navegar: {e2}")
                        break

                # Buscar el DTE en la página actual
                print(
                    f"\n🔍 Buscando DTE {ultimo_dte_procesado} en la página actual..."
                )
                time.sleep(2)
                indice_dte = buscar_dte_en_pagina(driver, ultimo_dte_procesado)

                if indice_dte is not None:
                    print(f"✅ DTE encontrado en la fila {indice_dte + 1}")
                    print(
                        f"   ⏭️ Se continuará desde el siguiente registro (fila {indice_dte + 2})"
                    )
                    pagina_inicio = pagina_objetivo
                else:
                    print(f"⚠️ DTE no encontrado en página {pagina_objetivo}")
                    print(f"   📄 Se procesará la página completa por seguridad")
                    pagina_inicio = pagina_objetivo
            else:
                # Si no hay DTE previo, ir a página 35 (penúltima - 1)
                print(
                    "\n🔄 No hay DTE previo. Navegando a la página penúltima menos 1..."
                )
                scroll_to_bottom(driver)
                time.sleep(1)

                try:
                    numero_pagina_objetivo = (
                        int(numero_ultima_pagina) - 2
                    )  # 37 - 2 = 35
                    boton_pagina_35 = driver.find_element(
                        By.XPATH,
                        f"//div[@id='sell_table_paginate']//li[contains(@class, 'paginate_button')]//a[@data-dt-idx and normalize-space(text())='{numero_pagina_objetivo}']",
                    )

                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        boton_pagina_35,
                    )
                    time.sleep(0.5)
                    boton_pagina_35.click()
                    print(
                        f"✅ Navegado a la página {numero_pagina_objetivo} (inicio de descargas)"
                    )
                    time.sleep(3)
                    pagina_inicio = numero_pagina_objetivo

                except Exception as e:
                    print(
                        f"⚠️ No se pudo navegar a la página {numero_pagina_objetivo}: {e}"
                    )
                    print("   Usando botón 'Anterior' dos veces como alternativa...")

                    # Alternativa: usar botón "Anterior" dos veces
                    for i in range(2):
                        try:
                            scroll_to_bottom(driver)
                            time.sleep(0.5)
                            boton_anterior = driver.find_element(
                                By.XPATH,
                                "//div[@id='sell_table_paginate']//li[@id='sell_table_previous' and not(contains(@class, 'disabled'))]//a",
                            )
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                boton_anterior,
                            )
                            time.sleep(0.3)
                            boton_anterior.click()
                            print(f"✅ Click en 'Anterior' ({i+1}/2)")
                            time.sleep(2)
                        except Exception as e2:
                            print(f"❌ Error al hacer click en 'Anterior': {e2}")
                            break

        else:
            print(
                "⚠️ No se encontraron botones de paginación. Puede que solo haya una página."
            )

    except Exception as e:
        print(f"⚠️ Error al navegar a la última página: {e}")
        print("   Continuando desde la página actual...")

    # Hacer scroll hasta el final de la página actual
    print("\n🔄 Haciendo scroll hasta el final de la página...")
    scroll_to_bottom(driver)
    time.sleep(1)

    # NUEVO FLUJO: Procesamiento por páginas
    print("\n" + "=" * 60)
    print("🚀 INICIANDO PROCESAMIENTO POR PÁGINAS (100 registros por página)")
    print("=" * 60)

    ventana_principal = driver.current_window_handle
    registros_procesados_totales = 0
    pagina_actual = None
    primera_pagina = True
    indice_inicio = 0

    while True:
        # Obtener filas de la página actual
        filas = driver.find_elements(
            By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
        )
        total_filas_pagina = len(filas)

        # Detectar número de página actual
        try:
            pagina_activa = driver.find_element(
                By.XPATH,
                "//div[@id='sell_table_paginate']//li[contains(@class, 'paginate_button') and contains(@class, 'active')]//a",
            )
            pagina_actual = pagina_activa.text.strip()
        except:
            pagina_actual = "?"

        print(f"\n{'='*60}")
        print(f"📄 PÁGINA {pagina_actual} - {total_filas_pagina} registros encontrados")
        print(f"{'='*60}")

        # Si es la primera página y hay un DTE previo, buscar desde dónde continuar
        if primera_pagina and ultimo_dte_procesado:
            indice_dte = buscar_dte_en_pagina(driver, ultimo_dte_procesado)
            if indice_dte is not None:
                indice_inicio = indice_dte + 1  # Continuar desde el siguiente
                print(
                    f"⏭️ Continuando desde el registro {indice_inicio + 1} (después del DTE previo)"
                )
            else:
                indice_inicio = 0
                print(
                    f"ℹ️ DTE previo no encontrado en esta página, procesando todos los registros"
                )
            primera_pagina = False
        else:
            indice_inicio = 0

        # Procesar cada registro de la página (desde indice_inicio hacia abajo)
        for idx in range(indice_inicio, total_filas_pagina):
            try:
                driver.switch_to.window(ventana_principal)
                registros_procesados_totales += 1

                print(
                    f"\n📄 Procesando registro {idx + 1}/{total_filas_pagina} de la página {pagina_actual} (Total global: {registros_procesados_totales}) ..."
                )

                # Re-obtener las filas
                filas = driver.find_elements(
                    By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
                )
                if idx >= len(filas):
                    print("  ⚠️ La fila ya no está disponible. Saltando...")
                    continue
                fila = filas[idx]

                # Procesar con sistema de reintentos
                exito = procesar_registro_con_reintentos(
                    driver,
                    fila,
                    idx,
                    ventana_principal,
                    wait,
                    pagina_actual,
                    max_reintentos=3,
                )

                if not exito:
                    dte = extraer_dte_de_fila(fila)

                    # Verificar si no fue marcada como anulada
                    ya_marcada_anulada = any(
                        f.get("dte") == (dte if dte else f"registro_{idx + 1}")
                        for f in facturas_anuladas
                    )

                    if not ya_marcada_anulada:
                        registros_fallidos.append(
                            {
                                "posicion": idx + 1,
                                "pagina": pagina_actual,
                                "dte": dte if dte else f"registro_{idx + 1}",
                                "fecha": datetime.now().isoformat(),
                            }
                        )
                        print(
                            f"  ❌ Registro marcado como fallido después de 3 intentos"
                        )

            except Exception as e:
                print(f"  ❌ Error crítico en registro {idx + 1}: {e}")
                dte = extraer_dte_de_fila(filas[idx]) if idx < len(filas) else None
                registros_fallidos.append(
                    {
                        "posicion": idx + 1,
                        "pagina": pagina_actual,
                        "dte": dte if dte else f"registro_{idx + 1}",
                        "error": str(e),
                        "fecha": datetime.now().isoformat(),
                    }
                )
                try:
                    if len(driver.window_handles) > 1:
                        for handle in driver.window_handles:
                            if handle != ventana_principal:
                                driver.switch_to.window(handle)
                                driver.close()
                    driver.switch_to.window(ventana_principal)
                    time.sleep(0.3)
                except:
                    pass
                continue

        # Terminamos de procesar la página actual
        print(
            f"\n✅ Página {pagina_actual} completada ({total_filas_pagina} registros procesados)"
        )

        # Intentar ir a la página anterior
        print(f"\n🔄 Buscando botón 'Anterior' para ir a la página anterior...")
        scroll_to_bottom(driver)
        time.sleep(1)

        try:
            boton_anterior = driver.find_element(
                By.XPATH,
                "//div[@id='sell_table_paginate']//li[@id='sell_table_previous' and not(contains(@class, 'disabled'))]//a",
            )

            # Hacer scroll al botón
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", boton_anterior
            )
            time.sleep(0.5)

            # Click en Anterior
            boton_anterior.click()
            print("✅ Click en 'Anterior' - Navegando a la página anterior...")
            time.sleep(3)  # Esperar a que cargue la nueva página

            # Hacer scroll al inicio de la nueva página
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

        except Exception as e:
            print(
                f"\n🎯 No hay más páginas anteriores o botón 'Anterior' deshabilitado"
            )
            print(f"   Fin del procesamiento por páginas")
            break

    print(f"\n{'='*60}")
    print(f"🎉 PROCESAMIENTO COMPLETADO")
    print(f"{'='*60}")
    print(f"✅ Total de registros procesados: {registros_procesados_totales}")
    print(f"❌ Registros fallidos: {len(registros_fallidos)}")
    print(f"⚠️ Facturas anuladas: {len(facturas_anuladas)}")

    # Contar archivos finales
    pdfs_finales = len(glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.pdf")))
    jsons_finales = len(
        [
            f
            for f in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.json"))
            if not (
                "registros_fallidos" in f
                or "ultimo_dte_exitoso" in f
                or "facturas_anuladas" in f
            )
        ]
    )

    print(f"\n📊 RESUMEN DE ARCHIVOS:")
    print(f"   📄 PDFs iniciales: {pdfs_iniciales}")
    print(f"   📄 PDFs finales: {pdfs_finales}")
    print(f"   ✨ PDFs nuevos descargados: {pdfs_finales - pdfs_iniciales}")
    print(f"")
    print(f"   📄 JSONs iniciales: {jsons_iniciales}")
    print(f"   📄 JSONs finales: {jsons_finales}")
    print(f"   ✨ JSONs nuevos descargados: {jsons_finales - jsons_iniciales}")
    print(f"")
    print(f"   📦 Total archivos iniciales: {pdfs_iniciales + jsons_iniciales}")
    print(f"   📦 Total archivos finales: {pdfs_finales + jsons_finales}")
    print(
        f"   🎁 Total archivos nuevos: {(pdfs_finales - pdfs_iniciales) + (jsons_finales - jsons_iniciales)}"
    )
    print(f"\n📁 Archivos descargados en: {DOWNLOAD_FOLDER}")
    print(f"💾 Backup guardado en: {BACKUP_FOLDER}")

    # Guardar reportes JSON
    guardar_reporte_json(pagina_actual)

    input("\nPresiona Enter para cerrar el navegador...")

except KeyboardInterrupt:
    print("\n\n⚠️ Ejecución interrumpida por el usuario")
    guardar_reporte_json(pagina_actual if "pagina_actual" in locals() else None)
    print("📊 Reportes guardados antes de salir")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    guardar_reporte_json(pagina_actual if "pagina_actual" in locals() else None)

finally:
    driver.quit()
    print("\n👋 Navegador cerrado")
