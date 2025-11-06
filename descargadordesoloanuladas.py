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

# Configuración de carpetas
DOWNLOAD_FOLDER_NORMAL = os.path.join(os.getcwd(), "descargas_erp")
DOWNLOAD_FOLDER_ANULADAS = os.path.join(os.getcwd(), "anuladas")
os.makedirs(DOWNLOAD_FOLDER_NORMAL, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER_ANULADAS, exist_ok=True)

print(f"📁 Carpeta facturas normales: {DOWNLOAD_FOLDER_NORMAL}")
print(f"📁 Carpeta facturas anuladas: {DOWNLOAD_FOLDER_ANULADAS}")

# Listas para tracking
facturas_descargadas_anuladas = []
facturas_descargadas_normales = []
facturas_no_encontradas = []
errores_descarga = []


def solicitar_archivos_fallidos():
    """
    Solicita al usuario los archivos JSON con registros fallidos
    """
    print("\n" + "=" * 80)
    print("DESCARGADOR DE FACTURAS ANULADAS Y NORMALES")
    print("=" * 80)
    print("\nIngrese las rutas de los archivos JSON con registros fallidos")
    print("Presione Enter sin escribir nada cuando haya terminado de agregar archivos")
    print("-" * 80)

    archivos = []
    contador = 1

    while True:
        ruta = input(f"\nArchivo {contador} (o Enter para continuar): ").strip()

        if not ruta:
            if archivos:
                break
            else:
                print("⚠️ Debe ingresar al menos un archivo")
                continue

        # Remover comillas si las tiene
        ruta = ruta.strip('"').strip("'")

        if os.path.exists(ruta):
            archivos.append(ruta)
            print(f"✅ Archivo agregado: {ruta}")
            contador += 1
        else:
            print(f"❌ Archivo no encontrado: {ruta}")

    return archivos


def cargar_registros_fallidos(archivos):
    """
    Carga y combina todos los registros fallidos de los archivos JSON
    """
    todos_registros = []

    for archivo in archivos:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
                registros = datos.get("registros", [])
                todos_registros.extend(registros)
                print(
                    f"✅ Cargados {len(registros)} registros de {os.path.basename(archivo)}"
                )
        except Exception as e:
            print(f"❌ Error al leer {archivo}: {e}")

    print(f"\n📊 Total de registros fallidos a procesar: {len(todos_registros)}")
    return todos_registros


def buscar_factura_por_dte(driver, dte):
    """
    Busca una factura en la tabla usando Ctrl+F del navegador
    """
    try:
        print(f"\n🔍 Buscando DTE: {dte}")

        # Abrir búsqueda con Ctrl+F
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys("f").key_up(Keys.CONTROL).perform()
        time.sleep(0.5)

        # Escribir el DTE en el cuadro de búsqueda
        actions.send_keys(dte).perform()
        print("  ⏳ Escribiendo DTE en búsqueda...")
        time.sleep(1)

        # Presionar Enter para buscar
        actions.send_keys(Keys.ENTER).perform()
        print("  ⏳ Esperando respuesta del frontend...")
        time.sleep(3)  # Esperar a que el frontend responda la búsqueda

        # Cerrar el cuadro de búsqueda
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)

        # Intentar encontrar la fila que contiene el DTE
        try:
            celda_dte = driver.find_element(
                By.XPATH, f"//td[contains(normalize-space(.), '{dte}')]"
            )

            # Obtener la fila completa
            fila = celda_dte.find_element(By.XPATH, "./ancestor::tr[@role='row']")

            # Hacer scroll a la fila
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", fila
            )
            time.sleep(0.5)

            print(f"✅ DTE encontrado en la tabla")
            return fila

        except Exception as e:
            print(f"❌ DTE no encontrado en la tabla: {e}")
            return None

    except Exception as e:
        print(f"❌ Error al buscar DTE: {e}")
        return None


def verificar_estado_factura(fila):
    """
    Verifica si la factura está anulada buscando la etiqueta correspondiente
    Retorna: 'anulada', 'normal', o None si no se puede determinar
    """
    try:
        # Buscar la etiqueta de estado anulada
        try:
            etiqueta_anulada = fila.find_element(
                By.XPATH,
                ".//td[@class=' text-center']//span[@class='label label-danger' and contains(text(), 'Anulada')]",
            )
            print("  ⚠️ Estado: ANULADA")
            return "anulada"
        except:
            pass

        # Si no tiene etiqueta de anulada, es una factura normal
        print("  ✅ Estado: NORMAL")
        return "normal"

    except Exception as e:
        print(f"  ⚠️ No se pudo determinar el estado: {e}")
        return None


def click_acciones_fila(driver, fila):
    """
    Hace click en el botón de Acciones de la fila
    """
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
        time.sleep(0.5)
        return True

    except Exception as e:
        print(f"  ❌ Error al hacer click en Acciones: {e}")
        return False


def click_ver_en_dropdown(driver, fila, wait):
    """
    Hace click en la opción 'Ver' del dropdown de acciones
    """
    try:
        # Buscar el menú dropdown visible
        def obtener_menu_visible(_):
            menus = fila.find_elements(
                By.XPATH, ".//ul[contains(@class,'dropdown-menu')]"
            )
            visibles = [m for m in menus if m.is_displayed()]
            return visibles[0] if visibles else False

        menu = WebDriverWait(driver, 5).until(obtener_menu_visible)

        # Buscar el botón "Ver"
        boton_ver = menu.find_element(
            By.XPATH, ".//a[@class='btn-modal' and contains(., 'Ver')]"
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'nearest'});", boton_ver
        )
        time.sleep(0.2)

        try:
            boton_ver.click()
        except:
            driver.execute_script("arguments[0].click();", boton_ver)

        print("  ✅ Click en 'Ver'")
        time.sleep(1)
        return True

    except Exception as e:
        print(f"  ❌ Error al hacer click en Ver: {e}")
        return False


def click_impresion_de_fila(driver, fila, wait):
    """
    Hace click en 'Impresión' del dropdown de acciones (para facturas normales)
    """
    try:

        def obtener_menu_visible(_):
            menus = fila.find_elements(
                By.XPATH, ".//ul[contains(@class,'dropdown-menu')]"
            )
            visibles = [m for m in menus if m.is_displayed()]
            return visibles[0] if visibles else False

        menu = WebDriverWait(driver, 5).until(obtener_menu_visible)

        candidatos = menu.find_elements(
            By.XPATH,
            ".//a[contains(concat(' ', normalize-space(@class), ' '), ' print-invoice ') "
            " or contains(normalize-space(.), 'Impresión')]",
        )
        if not candidatos:
            raise Exception("No se encontró 'Impresión' en el menú de esta fila")

        objetivo = next((c for c in candidatos if c.is_displayed()), candidatos[0])
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'nearest'});", objetivo
        )
        time.sleep(0.2)

        try:
            objetivo.click()
        except:
            driver.execute_script("arguments[0].click();", objetivo)

        print("  ✅ Click en 'Impresión'")
        time.sleep(0.5)
        return True

    except Exception as e:
        print(f"  ❌ Error al hacer click en Impresión: {e}")
        return False


def click_impresion_en_modal(driver, wait):
    """
    Hace click en el botón 'Impresión' del modal flotante (para facturas anuladas)
    """
    try:
        # Esperar a que aparezca el modal con más tiempo
        print("  ⏳ Esperando que aparezca el modal...")
        modal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
        )

        print("  ✅ Modal de detalles abierto")

        # Esperar a que el contenido del modal se cargue completamente
        # Esperamos específicamente por el modal-footer que contiene el botón
        print("  ⏳ Esperando que se cargue el contenido del modal...")
        time.sleep(2)

        # Esperar a que el footer esté visible
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "modal-footer"))
            )
            print("  ✓ Footer del modal cargado")
        except:
            print("  ⚠️ Footer del modal no encontrado, continuando...")

        # Intentar encontrar el botón de impresión con múltiples estrategias
        boton_impresion = None

        # Estrategia 1: Buscar en todo el documento (no solo en modal) por onclick que contiene openDteUrl
        try:
            boton_impresion = driver.find_element(
                By.XPATH,
                "//a[contains(@onclick, 'openDteUrl') and contains(@class, 'print-invoice')]",
            )
            print("  ✓ Botón encontrado (estrategia 1: onclick + clase)")
        except:
            pass

        # Estrategia 2: Buscar solo por clase print-invoice en todo el documento
        if not boton_impresion:
            try:
                boton_impresion = driver.find_element(
                    By.XPATH, "//a[contains(@class, 'print-invoice')]"
                )
                print("  ✓ Botón encontrado (estrategia 2: solo clase en documento)")
            except:
                pass

        # Estrategia 3: Buscar por clase y data-href en el modal
        if not boton_impresion:
            try:
                boton_impresion = modal.find_element(
                    By.XPATH,
                    ".//a[contains(@class, 'print-invoice') and contains(@data-href, '/print')]",
                )
                print("  ✓ Botón encontrado (estrategia 3: clase + data-href en modal)")
            except:
                pass

        # Estrategia 4: Buscar por texto "Impresión" en el modal-footer
        if not boton_impresion:
            try:
                footer = driver.find_element(By.CLASS_NAME, "modal-footer")
                boton_impresion = footer.find_element(
                    By.XPATH, ".//a[contains(., 'Impresión')]"
                )
                print("  ✓ Botón encontrado (estrategia 4: texto en footer)")
            except:
                pass

        # Estrategia 5: Buscar cualquier botón btn-primary en modal-footer
        if not boton_impresion:
            try:
                footer = driver.find_element(By.CLASS_NAME, "modal-footer")
                boton_impresion = footer.find_element(
                    By.XPATH, ".//a[contains(@class, 'btn-primary')]"
                )
                print("  ✓ Botón encontrado (estrategia 5: btn-primary en footer)")
            except:
                pass

        # Estrategia 6: Buscar por href que contenga /print
        if not boton_impresion:
            try:
                boton_impresion = driver.find_element(
                    By.XPATH,
                    "//a[contains(@data-href, '/print') or contains(@href, '/print')]",
                )
                print("  ✓ Botón encontrado (estrategia 6: href con /print)")
            except:
                pass

        if not boton_impresion:
            # Mostrar el HTML del modal para debug
            try:
                html_modal = modal.get_attribute("innerHTML")
                print(f"  ⚠️ HTML del modal (primeros 500 caracteres):")
                print(f"  {html_modal[:500]}")
            except:
                pass
            raise Exception("No se pudo encontrar el botón de Impresión en el modal")

        # Hacer scroll al botón
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", boton_impresion
        )
        time.sleep(0.5)

        # Intentar hacer click
        try:
            boton_impresion.click()
        except:
            driver.execute_script("arguments[0].click();", boton_impresion)

        print("  ✅ Click en 'Impresión' del modal")
        time.sleep(0.5)
        return True

    except Exception as e:
        print(f"  ❌ Error al hacer click en Impresión del modal: {e}")
        return False


def cambiar_a_nueva_ventana(driver, ventana_original):
    """Cambia el contexto a la nueva ventana abierta"""
    try:
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        for ventana in driver.window_handles:
            if ventana != ventana_original:
                driver.switch_to.window(ventana)
                print("  ✅ Cambiado a nueva ventana de impresión")
                return True
        return False
    except Exception as e:
        print(f"  ❌ Error al cambiar de ventana: {e}")
        return False


def descargar_pdf_y_json(driver, wait, carpeta_destino, nombre_base):
    """
    Descarga PDF y JSON de la ventana actual
    """
    descargas_exitosas = 0

    try:
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
            print("  ⬇️ Click en descarga PDF...")
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
            print("  ⬇️ Click en descarga JSON...")
            descargas_exitosas += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ No se pudo hacer click en JSON: {e}")

        if descargas_exitosas == 2:
            print("  🎉 Ambas descargas iniciadas")
            return True
        else:
            print(f"  ⚠️ Solo se ejecutaron {descargas_exitosas}/2 descargas")
            return False

    except Exception as e:
        print(f"  ❌ Error al iniciar descargas: {e}")
        return False


def cambiar_carpeta_descarga(driver, nueva_carpeta):
    """
    Cambia dinámicamente la carpeta de descarga de Chrome
    """
    try:
        driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": nueva_carpeta},
        )
        print(f"  📁 Carpeta de descarga configurada: {nueva_carpeta}")
        return True
    except Exception as e:
        print(f"  ⚠️ No se pudo cambiar carpeta de descarga: {e}")
        return False


def cerrar_modal_si_esta_abierto(driver):
    """
    Cierra el modal si está abierto después de regresar a la ventana principal
    """
    try:
        # Verificar si hay un modal abierto
        modal = driver.find_element(By.CLASS_NAME, "modal-content")

        if modal.is_displayed():
            print("  🔍 Modal detectado abierto, cerrando...")

            # Estrategia 1: Buscar botón "Cerrar" en el footer
            try:
                boton_cerrar = driver.find_element(
                    By.XPATH,
                    "//div[@class='modal-footer']//button[contains(text(), 'Cerrar')]",
                )
                boton_cerrar.click()
                print("  ✅ Modal cerrado (botón 'Cerrar')")
                time.sleep(0.5)
                return True
            except:
                pass

            # Estrategia 2: Buscar botón con data-dismiss="modal"
            try:
                boton_cerrar = driver.find_element(
                    By.XPATH,
                    "//button[@data-dismiss='modal']",
                )
                boton_cerrar.click()
                print("  ✅ Modal cerrado (data-dismiss)")
                time.sleep(0.5)
                return True
            except:
                pass

            # Estrategia 3: Buscar la X de cerrar
            try:
                boton_x = driver.find_element(
                    By.XPATH,
                    "//button[@class='close no-print']",
                )
                boton_x.click()
                print("  ✅ Modal cerrado (botón X)")
                time.sleep(0.5)
                return True
            except:
                pass

            # Estrategia 4: Presionar ESC
            try:
                from selenium.webdriver.common.action_chains import ActionChains

                actions = ActionChains(driver)
                actions.send_keys(Keys.ESCAPE).perform()
                print("  ✅ Modal cerrado (tecla ESC)")
                time.sleep(0.5)
                return True
            except:
                pass

            print("  ⚠️ No se pudo cerrar el modal automáticamente")
            return False
    except:
        # No hay modal abierto
        return True


def procesar_factura_anulada(driver, wait, fila, dte, ventana_principal):
    """
    Procesa una factura anulada: Acciones -> Ver -> Modal -> Impresión
    """
    try:
        # 1. Click en Acciones
        if not click_acciones_fila(driver, fila):
            return False

        # 2. Click en Ver
        if not click_ver_en_dropdown(driver, fila, wait):
            return False

        # 3. Click en Impresión del modal
        if not click_impresion_en_modal(driver, wait):
            return False

        # 4. Cambiar a ventana de impresión
        if not cambiar_a_nueva_ventana(driver, ventana_principal):
            return False

        time.sleep(0.5)

        # 4.5. CAMBIAR CARPETA DE DESCARGA A ANULADAS
        cambiar_carpeta_descarga(driver, DOWNLOAD_FOLDER_ANULADAS)

        # 5. Descargar archivos
        if descargar_pdf_y_json(driver, wait, DOWNLOAD_FOLDER_ANULADAS, dte):
            print("  ✅ Factura ANULADA descargada correctamente")
            facturas_descargadas_anuladas.append(
                {"dte": dte, "fecha": datetime.now().isoformat(), "carpeta": "anuladas"}
            )

            # Esperar a que terminen las descargas
            print("  ⏳ Esperando a que se completen las descargas...")
            time.sleep(2)

            # Cerrar ventana de impresión
            print("  🔒 Cerrando ventana de descarga...")
            driver.close()
            driver.switch_to.window(ventana_principal)
            print("  ✅ Ventana cerrada, recursos liberados")

            # Cerrar modal si está abierto
            cerrar_modal_si_esta_abierto(driver)

            return True
        else:
            # Esperar un poco incluso si falla
            time.sleep(1)

            # Cerrar ventana de impresión
            print("  🔒 Cerrando ventana de descarga...")
            driver.close()
            driver.switch_to.window(ventana_principal)
            print("  ✅ Ventana cerrada")

            # Cerrar modal si está abierto incluso si falla la descarga
            cerrar_modal_si_esta_abierto(driver)

            return False

    except Exception as e:
        print(f"  ❌ Error al procesar factura anulada: {e}")
        try:
            # Cerrar TODAS las ventanas extras que puedan estar abiertas
            if len(driver.window_handles) > 1:
                print("  🔒 Cerrando ventanas adicionales por error...")
                for handle in driver.window_handles:
                    if handle != ventana_principal:
                        driver.switch_to.window(handle)
                        driver.close()
                        print("  ✅ Ventana adicional cerrada")
            driver.switch_to.window(ventana_principal)

            # Cerrar modal si está abierto después de un error
            cerrar_modal_si_esta_abierto(driver)
        except:
            pass
        return False


def procesar_factura_normal(driver, wait, fila, dte, ventana_principal):
    """
    Procesa una factura normal: Acciones -> Impresión directa
    """
    try:
        # 1. Click en Acciones
        if not click_acciones_fila(driver, fila):
            return False

        # 2. Click en Impresión
        if not click_impresion_de_fila(driver, fila, wait):
            return False

        # 3. Cambiar a ventana de impresión
        if not cambiar_a_nueva_ventana(driver, ventana_principal):
            return False

        time.sleep(0.5)

        # 3.5. CAMBIAR CARPETA DE DESCARGA A DESCARGAS_ERP (NORMALES)
        cambiar_carpeta_descarga(driver, DOWNLOAD_FOLDER_NORMAL)

        # 4. Descargar archivos
        if descargar_pdf_y_json(driver, wait, DOWNLOAD_FOLDER_NORMAL, dte):
            print("  ✅ Factura NORMAL descargada correctamente")
            facturas_descargadas_normales.append(
                {
                    "dte": dte,
                    "fecha": datetime.now().isoformat(),
                    "carpeta": "descargas_erp",
                }
            )

            # Esperar a que terminen las descargas
            print("  ⏳ Esperando a que se completen las descargas...")
            time.sleep(2)

            # Cerrar ventana de impresión
            print("  🔒 Cerrando ventana de descarga...")
            driver.close()
            driver.switch_to.window(ventana_principal)
            print("  ✅ Ventana cerrada, recursos liberados")

            return True
        else:
            # Esperar un poco incluso si falla
            time.sleep(1)

            # Cerrar ventana de impresión
            print("  🔒 Cerrando ventana de descarga...")
            driver.close()
            driver.switch_to.window(ventana_principal)
            print("  ✅ Ventana cerrada")

            return False

    except Exception as e:
        print(f"  ❌ Error al procesar factura normal: {e}")
        try:
            # Cerrar TODAS las ventanas extras que puedan estar abiertas
            if len(driver.window_handles) > 1:
                print("  🔒 Cerrando ventanas adicionales por error...")
                for handle in driver.window_handles:
                    if handle != ventana_principal:
                        driver.switch_to.window(handle)
                        driver.close()
                        print("  ✅ Ventana adicional cerrada")
            driver.switch_to.window(ventana_principal)
        except:
            pass
        return False


def guardar_reporte_final():
    """
    Guarda el reporte final con todas las facturas procesadas
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    reporte = {
        "fecha_reporte": datetime.now().isoformat(),
        "resumen": {
            "total_procesadas": len(facturas_descargadas_anuladas)
            + len(facturas_descargadas_normales),
            "anuladas_descargadas": len(facturas_descargadas_anuladas),
            "normales_descargadas": len(facturas_descargadas_normales),
            "no_encontradas": len(facturas_no_encontradas),
            "errores": len(errores_descarga),
        },
        "facturas_anuladas": facturas_descargadas_anuladas,
        "facturas_normales": facturas_descargadas_normales,
        "no_encontradas": facturas_no_encontradas,
        "errores": errores_descarga,
    }

    archivo_reporte = f"reporte_descarga_fallidas_{timestamp}.json"

    with open(archivo_reporte, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Reporte guardado: {archivo_reporte}")


# PRIMERO: Solicitar archivos ANTES de iniciar el navegador
print("\n" + "=" * 80)
print("🔧 CONFIGURACIÓN INICIAL")
print("=" * 80)

archivos_fallidos = solicitar_archivos_fallidos()

if not archivos_fallidos:
    print("\n❌ No se proporcionaron archivos. Saliendo...")
    exit()

# Cargar registros fallidos
registros_fallidos = cargar_registros_fallidos(archivos_fallidos)

if not registros_fallidos:
    print("\n❌ No hay registros para procesar. Saliendo...")
    exit()

print(f"\n✅ Configuración completa. Iniciando navegador...\n")

# SEGUNDO: Configurar e iniciar el navegador
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": DOWNLOAD_FOLDER_NORMAL,
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

try:

    # Maximizar ventana
    driver.maximize_window()
    print("\n🚀 Iniciando navegador...")

    # URL de tu ERP
    URL_ERP = "https://hermaco.findexbusiness.com"
    driver.get(URL_ERP)
    print(f"📍 Navegando a: {URL_ERP}")

    wait = WebDriverWait(driver, 10)

    # Login
    print("\n🔐 Iniciando sesión...")
    login_link = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='https://hermaco.findexbusiness.com/login']")
        )
    )
    login_link.click()
    print("✅ Click en 'Inicio de sesión'")

    time.sleep(2)

    # Rellenar credenciales
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    username_input.send_keys("Henri")
    print("✅ Usuario ingresado")

    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys("Bajmut")
    print("✅ Contraseña ingresada")

    login_button = driver.find_element(
        By.XPATH, "//button[@type='submit' and contains(@class, 'btn-primary')]"
    )
    login_button.click()
    print("✅ Login completado")

    time.sleep(3)

    # Navegar a Gestión de ventas
    print("\n🔄 Navegando a 'Gestión de ventas'...")
    gestion_ventas = wait.until(EC.element_to_be_clickable((By.ID, "tour_step7_menu")))
    gestion_ventas.click()
    time.sleep(1)

    todas_ventas = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='https://hermaco.findexbusiness.com/sells']")
        )
    )
    todas_ventas.click()
    print("✅ Click en 'Todas las ventas'")

    time.sleep(2)

    # Filtro de fecha
    print("\n🔄 Configurando filtros...")
    filtro_fecha = wait.until(EC.element_to_be_clickable((By.ID, "sell_date_filter")))
    filtro_fecha.click()
    time.sleep(2)

    try:
        ejercicio_actual = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//li[contains(text(), 'Ejercicio actual')] | //a[contains(text(), 'Ejercicio actual')]",
                )
            )
        )
        ejercicio_actual.click()
        print("✅ Seleccionado 'Ejercicio actual'")
    except:
        print("⚠️ No se pudo seleccionar 'Ejercicio actual'")

    time.sleep(3)

    # Mostrar TODOS los registros
    print("\n🔄 Cambiando filtro a TODOS los registros...")
    select_length = wait.until(
        EC.presence_of_element_located((By.NAME, "sell_table_length"))
    )

    try:
        Select(select_length).select_by_value("-1")  # -1 = Todos
        print("✅ Seleccionado TODOS los registros")
        print("⏳ Esperando 40 segundos a que cargue toda la data extensa...")

        # Mostrar progreso de la espera
        for i in range(40, 0, -5):
            print(f"   ⏱️  {i} segundos restantes...")
            time.sleep(5)

        print("✅ Carga completada")

    except:
        print("⚠️ No se pudo seleccionar TODOS, intentando con 100...")
        try:
            Select(select_length).select_by_value("100")
            print("✅ Seleccionado 100 registros por página")
            print("⏳ Esperando a que carguen los registros...")
            time.sleep(10)
        except Exception as e:
            print(f"❌ Error al cambiar tamaño de página: {e}")

    print("✅ Tabla lista para procesar")

    # Procesar cada registro fallido
    ventana_principal = driver.current_window_handle

    print("\n" + "=" * 80)
    print("🚀 INICIANDO PROCESAMIENTO DE FACTURAS FALLIDAS")
    print("=" * 80)

    for idx, registro in enumerate(registros_fallidos, 1):
        dte = registro.get("dte")

        if not dte:
            print(
                f"\n[{idx}/{len(registros_fallidos)}] ⚠️ Registro sin DTE, saltando..."
            )
            continue

        print(f"\n{'='*80}")
        print(f"[{idx}/{len(registros_fallidos)}] Procesando: {dte}")
        print(f"{'='*80}")

        try:
            # Volver a ventana principal
            driver.switch_to.window(ventana_principal)

            # Buscar la factura por DTE
            fila = buscar_factura_por_dte(driver, dte)

            if not fila:
                print(f"  ❌ Factura no encontrada")
                facturas_no_encontradas.append(
                    {"dte": dte, "fecha": datetime.now().isoformat()}
                )
                continue

            # Verificar estado de la factura
            estado = verificar_estado_factura(fila)

            if estado == "anulada":
                # Procesar como factura anulada
                exito = procesar_factura_anulada(
                    driver, wait, fila, dte, ventana_principal
                )
            elif estado == "normal":
                # Procesar como factura normal
                exito = procesar_factura_normal(
                    driver, wait, fila, dte, ventana_principal
                )
            else:
                print(f"  ⚠️ No se pudo determinar el estado de la factura")
                errores_descarga.append(
                    {
                        "dte": dte,
                        "error": "Estado desconocido",
                        "fecha": datetime.now().isoformat(),
                    }
                )
                continue

            if not exito:
                errores_descarga.append(
                    {
                        "dte": dte,
                        "error": "Error en descarga",
                        "fecha": datetime.now().isoformat(),
                    }
                )

            # Pausa entre facturas
            time.sleep(1)

        except Exception as e:
            print(f"  ❌ Error crítico: {e}")
            errores_descarga.append(
                {"dte": dte, "error": str(e), "fecha": datetime.now().isoformat()}
            )

            # Asegurar que volvemos a ventana principal
            try:
                if len(driver.window_handles) > 1:
                    for handle in driver.window_handles:
                        if handle != ventana_principal:
                            driver.switch_to.window(handle)
                            driver.close()
                driver.switch_to.window(ventana_principal)
            except:
                pass

            continue

    # Resumen final
    print("\n" + "=" * 80)
    print("🎉 PROCESAMIENTO COMPLETADO")
    print("=" * 80)
    print(f"✅ Facturas anuladas descargadas: {len(facturas_descargadas_anuladas)}")
    print(f"✅ Facturas normales descargadas: {len(facturas_descargadas_normales)}")
    print(f"❌ Facturas no encontradas: {len(facturas_no_encontradas)}")
    print(f"⚠️ Errores en descarga: {len(errores_descarga)}")
    print(f"\n📁 Facturas anuladas en: {DOWNLOAD_FOLDER_ANULADAS}")
    print(f"📁 Facturas normales en: {DOWNLOAD_FOLDER_NORMAL}")

    # Guardar reporte
    guardar_reporte_final()

    input("\nPresiona Enter para cerrar el navegador...")

except KeyboardInterrupt:
    print("\n\n⚠️ Ejecución interrumpida por el usuario")
    guardar_reporte_final()

except Exception as e:
    print(f"\n❌ Error crítico: {e}")
    import traceback

    traceback.print_exc()
    guardar_reporte_final()

finally:
    driver.quit()
    print("\n👋 Navegador cerrado")
