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

# Configuración de la carpeta de descargas
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "descargas_gastos")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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
registros_ignorados = []
ultimo_codigo_exitoso = None
pagina_ultimo_codigo_exitoso = None


def contar_archivos_iniciales():
    """Cuenta los archivos PDF y JSON que ya existen en la carpeta de descargas"""
    pdfs = len(glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.pdf")))
    jsons_gastos = len(
        [
            f
            for f in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.json"))
            if not ("registros_fallidos" in f or "ultimo_codigo_exitoso" in f)
        ]
    )
    return pdfs, jsons_gastos


def leer_ultimo_codigo_exitoso():
    """Lee el último código exitoso del archivo JSON más reciente"""
    try:
        archivos_ultimo_codigo = glob.glob(
            os.path.join(DOWNLOAD_FOLDER, "ultimo_codigo_exitoso_*.json")
        )
        if not archivos_ultimo_codigo:
            print(
                "ℹ️ No se encontró archivo de último código exitoso. Se procesarán todas las páginas."
            )
            return None, None

        # Obtener el archivo más reciente
        archivo_mas_reciente = max(archivos_ultimo_codigo, key=os.path.getmtime)

        with open(archivo_mas_reciente, "r", encoding="utf-8") as f:
            data = json.load(f)
            ultimo_codigo = data.get("ultimo_codigo")
            pagina = data.get("pagina", None)

            if ultimo_codigo:
                print(f"✅ Último código exitoso encontrado: {ultimo_codigo}")
                if pagina:
                    print(f"   📄 Última página procesada: {pagina}")
                return ultimo_codigo, pagina
            else:
                print("⚠️ Archivo de último código exitoso vacío.")
                return None, None

    except Exception as e:
        print(f"⚠️ Error al leer último código exitoso: {e}")
        return None, None


def buscar_codigo_en_pagina(driver, codigo_buscado):
    """
    Busca un código de gasto específico en la página actual.
    Retorna el índice de la fila si lo encuentra, o None si no lo encuentra.
    """
    try:
        filas = driver.find_elements(
            By.XPATH, "//table[@id='expense_table']//tbody/tr[@role='row']"
        )

        for idx, fila in enumerate(filas):
            codigo_actual = extraer_codigo_de_fila(fila)
            if codigo_actual == codigo_buscado:
                print(f"  ✅ Código encontrado en la fila {idx + 1}")
                return idx

        print(f"  ℹ️ Código {codigo_buscado} no encontrado en esta página")
        return None

    except Exception as e:
        print(f"  ⚠️ Error al buscar código en página: {e}")
        return None


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


def click_imprimir_dte_de_fila(driver, fila, wait):
    """
    Hace click en 'Imprimir DTE' SOLO dentro del dropdown visible de esta fila.
    """

    def obtener_menu_visible(_):
        menus = fila.find_elements(By.XPATH, ".//ul[contains(@class,'dropdown-menu')]")
        visibles = [m for m in menus if m.is_displayed()]
        return visibles[0] if visibles else False

    menu = WebDriverWait(driver, 8).until(obtener_menu_visible)

    candidatos = menu.find_elements(
        By.XPATH,
        ".//a[contains(concat(' ', normalize-space(@class), ' '), ' print-dte-expense ') "
        " or contains(normalize-space(.), 'Imprimir DTE')]",
    )
    if not candidatos:
        raise Exception("No se encontró 'Imprimir DTE' en el menú de esta fila")

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


def extraer_codigo_de_fila(fila):
    """
    Busca en la fila una celda que contenga el código del gasto (p.ej. 'AE6B49E7-62FA-505E-BFF0-2503F4C6E932')
    y lo retorna. Devuelve None si no lo encuentra.
    """
    try:
        # Buscar en la celda que contiene el código (normalmente la 5ta columna)
        celda = fila.find_element(
            By.XPATH,
            ".//td[@class='clickable_td']//span[@class='text-primary']//strong",
        )
        codigo = celda.text.strip()
        if codigo:
            return codigo
    except Exception:
        pass
    return None


def verificar_estado_pago(fila):
    """
    Verifica el estado de pago de un gasto.
    Retorna True si está "Pagado", False si está "Debido" o cualquier otro estado.
    """
    try:
        # Buscar el elemento que contiene el estado de pago
        estado_element = fila.find_element(
            By.XPATH,
            ".//td//a[contains(@class, 'payment-status')]//span[contains(@class, 'label')]",
        )
        estado_texto = estado_element.text.strip()

        if estado_texto == "Pagado":
            print(f"  ✅ Estado de pago: {estado_texto}")
            return True
        else:
            print(f"  ⏭️ Estado de pago: {estado_texto} - Registro ignorado")
            return False

    except Exception as e:
        print(f"  ⚠️ No se pudo verificar el estado de pago: {e}")
        # Si no se puede verificar, asumir que no está pagado por seguridad
        return False


def descargar_pdf_y_json(
    driver, wait, carpeta_descargas, nombre_base, numero_gasto=None
):
    """
    Descarga PDF y JSON de la ventana actual y los renombra con 'nombre_base' (el código).
    Si no se pasa nombre_base, intenta usar el ID de la URL; si falla, usa 'gasto_{numero_gasto}'.
    """
    descargas_exitosas = 0
    gasto_id = None

    try:
        # Intentar obtener ID de la URL del PDF (fallback si no hay código)
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
            gasto_id = (
                url_pdf.split("/pdf/")[-1] if url_pdf and "/pdf/" in url_pdf else None
            )
            if gasto_id:
                print(f"  📋 ID de gasto detectado: {gasto_id}")
        except Exception as e:
            print(f"  ⚠️ No se pudo obtener el ID del gasto: {e}")

        base = (
            sanitize_filename(nombre_base)
            if nombre_base
            else (gasto_id or f"gasto_{numero_gasto}")
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
    Procesa un registro con sistema de reintentos (3 intentos con pausa en el último)
    """
    global ultimo_codigo_exitoso
    global pagina_ultimo_codigo_exitoso

    # Verificar primero el estado de pago
    if not verificar_estado_pago(fila):
        print(f"  ⏭️ Registro ignorado por estado de pago")
        return "ignorado"  # Retornar un valor especial para indicar que fue ignorado

    codigo = extraer_codigo_de_fila(fila)
    if codigo:
        print(f"  🏷️ Código detectado: {codigo}")
    else:
        print(
            "  ⚠️ No se pudo detectar código en la fila. Se usará ID/índice como fallback."
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
                By.XPATH, "//table[@id='expense_table']//tbody/tr[@role='row']"
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

            # Re-extraer código por si acaso
            if not codigo:
                codigo = extraer_codigo_de_fila(fila)

            # Click en "Acciones"
            try:
                boton_acciones = fila.find_element(
                    By.XPATH,
                    ".//button[contains(@class, 'dropdown-toggle') and contains(text(), 'Acciones')]",
                )
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

            # Click en "Imprimir DTE"
            try:
                click_imprimir_dte_de_fila(driver, fila, wait)
                print("  ✅ Click en 'Imprimir DTE' - Se abre nueva ventana")
                time.sleep(0.3)
            except Exception as e:
                print(f"  ❌ No se pudo hacer click en 'Imprimir DTE': {e}")
                if intento < max_reintentos:
                    continue
                else:
                    raise

            # Cambiar a la nueva ventana y descargar
            if cambiar_a_nueva_ventana(driver, ventana_principal):
                time.sleep(0.5)

                if descargar_pdf_y_json(driver, wait, DOWNLOAD_FOLDER, codigo, idx + 1):
                    print("  ✅ Descargas iniciadas correctamente")
                    ultimo_codigo_exitoso = codigo if codigo else f"registro_{idx + 1}"
                    pagina_ultimo_codigo_exitoso = pagina_actual
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

    # Guardar registros ignorados
    if registros_ignorados:
        archivo_ignorados = os.path.join(
            DOWNLOAD_FOLDER, f"registros_ignorados_{timestamp}.json"
        )
        with open(archivo_ignorados, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_reporte": datetime.now().isoformat(),
                    "total_ignorados": len(registros_ignorados),
                    "registros": registros_ignorados,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"📄 Reporte de ignorados guardado: {archivo_ignorados}")

    # Guardar último código exitoso
    if ultimo_codigo_exitoso:
        archivo_ultimo = os.path.join(
            DOWNLOAD_FOLDER, f"ultimo_codigo_exitoso_{timestamp}.json"
        )
        with open(archivo_ultimo, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_reporte": datetime.now().isoformat(),
                    "ultimo_codigo": ultimo_codigo_exitoso,
                    "pagina": pagina_actual,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"📄 Último código exitoso guardado: {archivo_ultimo}")
        if pagina_actual:
            print(f"   📄 Página: {pagina_actual}")


try:
    # Contar archivos iniciales
    print("📊 Contando archivos existentes en la carpeta de descargas...")
    pdfs_iniciales, jsons_iniciales = contar_archivos_iniciales()
    print(f"   📄 PDFs existentes: {pdfs_iniciales}")
    print(f"   📄 JSONs existentes: {jsons_iniciales}")
    print(f"   📦 Total archivos iniciales: {pdfs_iniciales + jsons_iniciales}")

    # Leer último código exitoso
    print("\n🔍 Buscando último código procesado...")
    ultimo_codigo_procesado, pagina_ultimo_codigo = leer_ultimo_codigo_exitoso()

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

    # Navegar a Gastos
    print("\n🔄 Navegando a 'Gastos'...")
    try:
        # Buscar el elemento li con clase treeview que contiene "Gastos"
        gastos_menu = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//li[contains(@class, 'treeview')]//a[contains(., 'Gastos')]",
                )
            )
        )
        gastos_menu.click()
        print("✅ Click en 'Gastos' (desplegable abierto)")
    except Exception as e:
        print(f"⚠️ Error al buscar menú Gastos: {e}")
        print("   Intentando método alternativo...")
        # Intentar con un XPath más específico
        gastos_menu = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Gastos']/parent::a"))
        )
        gastos_menu.click()
        print("✅ Click en 'Gastos' (desplegable abierto)")

    time.sleep(1)

    # Click en "Lista de gastos"
    print("\n🔄 Navegando a 'Lista de gastos'...")
    lista_gastos = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='https://hermaco.findexbusiness.com/expenses']")
        )
    )
    lista_gastos.click()
    print("✅ Click en 'Lista de gastos'")

    time.sleep(2)
    print("📍 Estamos en la página de gastos")

    # Filtro de fecha
    print("\n🔄 Abriendo filtro de fecha...")
    filtro_fecha = wait.until(EC.element_to_be_clickable((By.ID, "expense_date_range")))
    filtro_fecha.click()
    print("✅ Click en 'Rango de fechas' (desplegable abierto)")

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

    # Mostrar 1000 registros por página
    print("\n🔄 Cambiando filtro a 1000 registros por página...")
    select_length = wait.until(
        EC.presence_of_element_located((By.NAME, "expense_table_length"))
    )
    try:
        Select(select_length).select_by_value("1000")
        print("✅ Seleccionado 1000 registros por página")
    except Exception as e:
        print(f"  ❌ No se pudo cambiar el tamaño de página: {e}")
        driver.quit()
        exit(1)

    # Dar tiempo a que carguen los registros
    print("⏳ Esperando 5 segundos a que carguen los registros...")
    time.sleep(5)
    print("✅ Registros cargados")

    # Navegar a la última página del paginador (si existe)
    print("\n🔄 Navegando a la última página...")
    scroll_to_bottom(driver)
    time.sleep(1)

    numero_ultima_pagina = None
    pagina_inicio = None

    try:
        # Buscar todos los botones de página y seleccionar el último número
        botones_pagina = driver.find_elements(
            By.XPATH,
            "//div[@id='expense_table_paginate']//li[contains(@class, 'paginate_button') and not(contains(@class, 'previous')) and not(contains(@class, 'next')) and not(contains(@class, 'disabled'))]//a",
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

            # Determinar página de inicio según si hay código previo
            if ultimo_codigo_procesado and pagina_ultimo_codigo:
                # Si hay un código previo, navegar a esa página
                print(
                    f"\n🔍 Buscando página {pagina_ultimo_codigo} del último código procesado..."
                )
                scroll_to_bottom(driver)
                time.sleep(1)

                # Obtener página actual
                try:
                    pagina_activa = driver.find_element(
                        By.XPATH,
                        "//div[@id='expense_table_paginate']//li[contains(@class, 'paginate_button') and contains(@class, 'active')]//a",
                    )
                    pagina_actual_num = int(pagina_activa.text.strip())
                except:
                    pagina_actual_num = int(numero_ultima_pagina)

                pagina_objetivo = int(pagina_ultimo_codigo)
                clicks_necesarios = pagina_actual_num - pagina_objetivo

                print(f"   📄 Página actual: {pagina_actual_num}")
                print(f"   🎯 Página objetivo: {pagina_objetivo}")
                print(f"   🔢 Clicks necesarios en 'Anterior': {clicks_necesarios}")

                # Navegar hacia atrás hasta la página del último código
                for i in range(clicks_necesarios):
                    try:
                        scroll_to_bottom(driver)
                        time.sleep(0.5)

                        # Verificar si el botón está visible en el paginador
                        try:
                            boton_directo = driver.find_element(
                                By.XPATH,
                                f"//div[@id='expense_table_paginate']//li[contains(@class, 'paginate_button')]//a[normalize-space(text())='{pagina_objetivo}']",
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
                                "//div[@id='expense_table_paginate']//li[@id='expense_table_previous' and not(contains(@class, 'disabled'))]//a",
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
                                    "//div[@id='expense_table_paginate']//li[contains(@class, 'paginate_button') and contains(@class, 'active')]//a",
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

                # Buscar el código en la página actual
                print(
                    f"\n🔍 Buscando código {ultimo_codigo_procesado} en la página actual..."
                )
                time.sleep(2)
                indice_codigo = buscar_codigo_en_pagina(driver, ultimo_codigo_procesado)

                if indice_codigo is not None:
                    print(f"✅ Código encontrado en la fila {indice_codigo + 1}")
                    print(
                        f"   ⏭️ Se continuará desde el siguiente registro (fila {indice_codigo + 2})"
                    )
                    pagina_inicio = pagina_objetivo
                else:
                    print(f"⚠️ Código no encontrado en página {pagina_objetivo}")
                    print(f"   📄 Se procesará la página completa por seguridad")
                    pagina_inicio = pagina_objetivo
            else:
                # Si no hay código previo, comenzar desde la última página
                print("\n📄 No hay código previo. Comenzando desde la última página...")
                pagina_inicio = numero_ultima_pagina

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
    print("🚀 INICIANDO PROCESAMIENTO DE GASTOS (1000 registros por página)")
    print("=" * 60)

    ventana_principal = driver.current_window_handle
    registros_procesados_totales = 0
    pagina_actual = None
    primera_pagina = True
    indice_inicio = 0

    while True:
        # Obtener filas de la página actual
        filas = driver.find_elements(
            By.XPATH, "//table[@id='expense_table']//tbody/tr[@role='row']"
        )
        total_filas_pagina = len(filas)

        # Detectar número de página actual
        try:
            pagina_activa = driver.find_element(
                By.XPATH,
                "//div[@id='expense_table_paginate']//li[contains(@class, 'paginate_button') and contains(@class, 'active')]//a",
            )
            pagina_actual = pagina_activa.text.strip()
        except:
            pagina_actual = "?"

        print(f"\n{'='*60}")
        print(f"📄 PÁGINA {pagina_actual} - {total_filas_pagina} registros encontrados")
        print(f"{'='*60}")

        # Si es la primera página y hay un código previo, buscar desde dónde continuar
        if primera_pagina and ultimo_codigo_procesado:
            indice_codigo = buscar_codigo_en_pagina(driver, ultimo_codigo_procesado)
            if indice_codigo is not None:
                indice_inicio = indice_codigo + 1  # Continuar desde el siguiente
                print(
                    f"⏭️ Continuando desde el registro {indice_inicio + 1} (después del código previo)"
                )
            else:
                indice_inicio = 0
                print(
                    f"ℹ️ Código previo no encontrado en esta página, procesando todos los registros"
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
                    By.XPATH, "//table[@id='expense_table']//tbody/tr[@role='row']"
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

                # Si el registro fue ignorado por estado de pago, continuar con el siguiente
                if exito == "ignorado":
                    codigo = extraer_codigo_de_fila(fila)
                    registros_ignorados.append(
                        {
                            "posicion": idx + 1,
                            "pagina": pagina_actual,
                            "codigo": codigo if codigo else f"registro_{idx + 1}",
                            "razon": "Estado de pago no es 'Pagado'",
                            "fecha": datetime.now().isoformat(),
                        }
                    )
                    print(f"  ⏭️ Saltando al siguiente registro...")
                    continue

                if not exito:
                    codigo = extraer_codigo_de_fila(fila)
                    registros_fallidos.append(
                        {
                            "posicion": idx + 1,
                            "pagina": pagina_actual,
                            "codigo": codigo if codigo else f"registro_{idx + 1}",
                            "fecha": datetime.now().isoformat(),
                        }
                    )
                    print(f"  ❌ Registro marcado como fallido después de 3 intentos")

            except Exception as e:
                print(f"  ❌ Error crítico en registro {idx + 1}: {e}")
                codigo = (
                    extraer_codigo_de_fila(filas[idx]) if idx < len(filas) else None
                )
                registros_fallidos.append(
                    {
                        "posicion": idx + 1,
                        "pagina": pagina_actual,
                        "codigo": codigo if codigo else f"registro_{idx + 1}",
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
                "//div[@id='expense_table_paginate']//li[@id='expense_table_previous' and not(contains(@class, 'disabled'))]//a",
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
    print(f"⏭️ Registros ignorados (no pagados): {len(registros_ignorados)}")
    print(f"❌ Registros fallidos: {len(registros_fallidos)}")

    # Contar archivos finales
    pdfs_finales = len(glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.pdf")))
    jsons_finales = len(
        [
            f
            for f in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.json"))
            if not ("registros_fallidos" in f or "ultimo_codigo_exitoso" in f)
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
