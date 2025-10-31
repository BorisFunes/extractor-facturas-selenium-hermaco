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
from pathlib import Path
from datetime import datetime

# Configuración de la carpeta de descargas
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "descargas_erp")
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


# =========================
# Helper: Click impresión en la fila (Opción 1)
# =========================
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


try:
    # Maximizar ventana
    driver.maximize_window()
    print("🚀 Iniciando navegador...")

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

    # ===== CAMBIO: Mostrar TODOS los registros =====
    print("\n🔄 Cambiando filtro a 'Todos' los registros...")
    select_length = wait.until(
        EC.presence_of_element_located((By.NAME, "sell_table_length"))
    )
    try:
        Select(select_length).select_by_value("-1")
        print("✅ Seleccionado 'Todos' registros (value = -1)")
    except Exception as e:
        print(f"  ⚠️ No se pudo seleccionar por value -1: {e}. Probando por texto...")
        try:
            # Fallback por texto visible (ES/EN)
            option_todos = driver.find_element(
                By.XPATH,
                "//select[@name='sell_table_length']/option[normalize-space(.)='Todos' or normalize-space(.)='All' or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'todos')]",
            )
            option_todos.click()
            print("✅ Seleccionado 'Todos' registros (por texto visible)")
        except Exception as e2:
            print(f"  ⚠️ Tampoco por texto: {e2}. Intentando 100 como alternativa...")
            try:
                Select(select_length).select_by_value("100")
                print("✅ Seleccionado 100 registros como alternativa")
            except Exception as e3:
                print(f"  ❌ No se pudo cambiar el tamaño de página: {e3}")

    # Dar tiempo a que carguen todos los registros
    print("⏳ Esperando 40 segundos a que carguen TODOS los registros...")
    time.sleep(40)
    print("✅ Registros cargados")

    # Obtener filas de la tabla
    filas = driver.find_elements(
        By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
    )
    total_filas = len(filas)
    print(f"📊 Total de registros encontrados: {total_filas}")

    # ====== PROCESAMIENTO SIN FILTROS: Tomar TODOS los registros en orden ======
    print(
        "\n🔄 Preparando para procesar TODOS los registros en orden (del primero al último)..."
    )

    # Limitar a 4000 registros como prueba
    LIMITE_PRUEBA = 4000
    cantidad_procesar = min(LIMITE_PRUEBA, total_filas)

    print(
        f"🧪 Se procesarán los primeros {cantidad_procesar} registros de {total_filas} disponibles"
    )

    ventana_principal = driver.current_window_handle

    # Iterar por los índices (del 0 al límite)
    for idx in range(cantidad_procesar):
        try:
            driver.switch_to.window(ventana_principal)

            print(f"\n📄 Procesando registro {idx + 1}/{cantidad_procesar} ...")

            # Re-obtener las filas y tomar la del índice actual
            filas = driver.find_elements(
                By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
            )
            if idx >= len(filas):
                print("  ⚠️ La fila ya no está disponible. Saltando...")
                continue
            fila = filas[idx]

            # Extraer DTE de la fila para usarlo como nombre de archivo
            dte = extraer_dte_de_fila(fila)
            if dte:
                print(f"  🏷️ DTE detectado: {dte}")
            else:
                print(
                    "  ⚠️ No se pudo detectar DTE en la fila. Se usará ID/índice como fallback."
                )

            # Click en "Acciones"
            try:
                boton_acciones = fila.find_element(By.CLASS_NAME, "btn-actions")
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", boton_acciones
                )
                time.sleep(0.2)
                try:
                    boton_acciones.click()
                except:
                    driver.execute_script("arguments[0].click();", boton_acciones)
                print("  ✅ Click en 'Acciones'")
                time.sleep(0.3)
            except Exception as e:
                print(f"  ❌ No se pudo hacer click en 'Acciones': {e}")
                continue

            # Click en "Impresión" (usando helper)
            try:
                click_impresion_de_fila(driver, fila, wait)
                print("  ✅ Click en 'Impresión' - Se abre nueva ventana")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ❌ No se pudo hacer click en 'Impresión' de esta fila: {e}")
                try:
                    print("  🔄 Reintentando...")
                    time.sleep(0.3)
                    boton_acciones = fila.find_element(By.CLASS_NAME, "btn-actions")
                    driver.execute_script("arguments[0].click();", boton_acciones)
                    time.sleep(0.3)
                    click_impresion_de_fila(driver, fila, wait)
                    print("  ✅ Click en 'Impresión' exitoso en segundo intento")
                    time.sleep(0.5)
                except Exception as e2:
                    print(f"  ❌ Segundo intento falló: {e2}. Saltando este registro.")
                    continue

            # Cambiar a la nueva ventana y descargar con nombre DTE
            if cambiar_a_nueva_ventana(driver, ventana_principal):
                time.sleep(1)

                if descargar_pdf_y_json(driver, wait, DOWNLOAD_FOLDER, dte, idx + 1):
                    print("  ✅ Descargas iniciadas")
                else:
                    print("  ⚠️ Problemas con descargas")

                driver.close()
                driver.switch_to.window(ventana_principal)
                print("  ✅ Siguiente registro...")
                time.sleep(0.2)
            else:
                print("  ⚠️ No se pudo cambiar a la nueva ventana")

        except Exception as e:
            print(f"  ❌ Error en registro {idx + 1}: {e}")
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

    print(f"\n🎉 Proceso completado!")
    print(
        f"✅ Se procesaron {cantidad_procesar} facturas (del primer registro al último)"
    )
    print(
        f"📦 Esperadas: {cantidad_procesar * 2} archivos ({cantidad_procesar} PDFs + {cantidad_procesar} JSONs)"
    )
    print(f"📁 Archivos descargados en: {DOWNLOAD_FOLDER}")

    pdfs = len(glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.pdf")))
    jsons = len(glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.json")))
    print(f"📊 Archivos reales: {pdfs} PDFs + {jsons} JSONs = {pdfs + jsons} total")

    input("\nPresiona Enter para cerrar el navegador...")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

finally:
    driver.quit()
