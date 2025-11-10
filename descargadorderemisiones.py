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
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "descargas_remisiones")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Archivo JSON fijo para tracking
ARCHIVO_ULTIMO_EXITOSO = os.path.join(DOWNLOAD_FOLDER, "ultimo_exitoso.json")

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

# Variable para tracking
ultimo_correlativo_exitoso = None


def contar_archivos_iniciales():
    """Cuenta los archivos PDF y JSON que ya existen en la carpeta de descargas"""
    pdfs = len(glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.pdf")))
    jsons_remisiones = len(
        [
            f
            for f in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.json"))
            if not ("ultimo_exitoso" in f)
        ]
    )
    return pdfs, jsons_remisiones


def leer_ultimo_correlativo_exitoso():
    """Lee el último correlativo exitoso del archivo JSON fijo"""
    try:
        if not os.path.exists(ARCHIVO_ULTIMO_EXITOSO):
            print(
                "ℹ️ No se encontró archivo de último correlativo exitoso. Se procesarán todas las remisiones."
            )
            return None

        with open(ARCHIVO_ULTIMO_EXITOSO, "r", encoding="utf-8") as f:
            data = json.load(f)
            ultimo_correlativo = data.get("ultimo_correlativo")

            if ultimo_correlativo:
                print(f"✅ Último correlativo exitoso encontrado: {ultimo_correlativo}")
                return ultimo_correlativo
            else:
                print("⚠️ Archivo de último correlativo exitoso vacío.")
                return None

    except Exception as e:
        print(f"⚠️ Error al leer último correlativo exitoso: {e}")
        return None


def guardar_ultimo_correlativo(correlativo):
    """Guarda el último correlativo exitoso en el archivo JSON fijo"""
    try:
        with open(ARCHIVO_ULTIMO_EXITOSO, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_actualizacion": datetime.now().isoformat(),
                    "ultimo_correlativo": correlativo,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"  ✅ Último correlativo guardado: {correlativo}")
        return True
    except Exception as e:
        print(f"  ❌ Error al guardar último correlativo: {e}")
        return False


def buscar_correlativo_con_ctrl_f(driver, correlativo_buscado):
    """
    Busca un correlativo específico usando Ctrl+F del navegador.
    Retorna el índice de la fila si lo encuentra, o None si no lo encuentra.
    """
    try:
        print(f"\n🔍 Buscando correlativo: {correlativo_buscado}")

        # Abrir búsqueda con Ctrl+F
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys("f").key_up(Keys.CONTROL).perform()
        time.sleep(0.5)

        # Escribir el correlativo en el cuadro de búsqueda
        actions.send_keys(correlativo_buscado).perform()
        print("  ⏳ Escribiendo correlativo en búsqueda...")
        time.sleep(1)

        # Presionar Enter para buscar
        actions.send_keys(Keys.ENTER).perform()
        print("  ⏳ Esperando respuesta del frontend...")
        time.sleep(3)

        # Cerrar el cuadro de búsqueda
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)

        # Intentar encontrar la fila que contiene el correlativo
        try:
            filas = driver.find_elements(
                By.XPATH, "//table[@id='remission_notes_table']//tbody/tr[@role='row']"
            )
            
            for idx, fila in enumerate(filas):
                correlativo_fila = extraer_correlativo_de_fila(fila)
                if correlativo_fila == correlativo_buscado:
                    print(f"  ✅ Correlativo encontrado en la fila {idx + 1}")
                    return idx
            
            print(f"  ⚠️ Correlativo no encontrado en la tabla")
            return None

        except Exception as e:
            print(f"  ❌ Error al buscar en la tabla: {e}")
            return None

    except Exception as e:
        print(f"❌ Error al buscar correlativo: {e}")
        return None


def buscar_correlativo_en_pagina(driver, correlativo_buscado):
    """
    Busca un correlativo específico en la página actual.
    Retorna el índice de la fila si lo encuentra, o None si no lo encuentra.
    """
    try:
        filas = driver.find_elements(
            By.XPATH, "//table[@id='remission_notes_table']//tbody/tr[@role='row']"
        )

        for idx, fila in enumerate(filas):
            correlativo_actual = extraer_correlativo_de_fila(fila)
            if correlativo_actual == correlativo_buscado:
                print(f"  ✅ Correlativo encontrado en la fila {idx + 1}")
                return idx

        print(f"  ℹ️ Correlativo {correlativo_buscado} no encontrado en esta página")
        return None

    except Exception as e:
        print(f"  ⚠️ Error al buscar correlativo en página: {e}")
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


def extraer_correlativo_de_fila(fila):
    """
    Busca en la fila el correlativo de la nota de remisión
    y lo retorna. Devuelve None si no lo encuentra.
    """
    try:
        # El correlativo suele estar en una celda específica
        celdas = fila.find_elements(By.TAG_NAME, "td")
        # Buscar en todas las celdas el patrón del correlativo
        for celda in celdas:
            texto = celda.text.strip()
            # Los correlativos tienen formato como: D54375A9-1E4A-A65F-BC54-80CA4EE8D85C
            if len(texto) == 36 and texto.count("-") == 4:
                return texto
    except Exception:
        pass
    return None


def click_acciones_fila(driver, fila):
    """
    Hace click en el botón de Acciones de la fila
    """
    try:
        boton_acciones = fila.find_element(
            By.XPATH,
            ".//button[contains(@class, 'dropdown-toggle') and contains(@class, 'btn-actions')]",
        )
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


def click_impresion_en_modal(driver, wait):
    """
    Hace click en el botón 'Impresión' del modal flotante
    """
    try:
        # Esperar a que aparezca el modal
        print("  ⏳ Esperando que aparezca el modal...")
        modal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
        )

        print("  ✅ Modal de detalles abierto")
        time.sleep(2)  # Esperar a que se cargue el contenido del modal

        # Buscar el botón de impresión en el modal
        boton_impresion = None

        # Estrategia 1: Buscar por onclick que contiene openDteUrl
        try:
            boton_impresion = driver.find_element(
                By.XPATH,
                "//a[contains(@onclick, 'openDteUrl') and contains(@class, 'print-invoice')]",
            )
            print("  ✓ Botón encontrado (estrategia 1: onclick + clase)")
        except:
            pass

        # Estrategia 2: Buscar solo por clase print-invoice
        if not boton_impresion:
            try:
                boton_impresion = driver.find_element(
                    By.XPATH, "//a[contains(@class, 'print-invoice')]"
                )
                print("  ✓ Botón encontrado (estrategia 2: solo clase)")
            except:
                pass

        # Estrategia 3: Buscar por texto "Impresión" en el modal-footer
        if not boton_impresion:
            try:
                footer = driver.find_element(By.CLASS_NAME, "modal-footer")
                boton_impresion = footer.find_element(
                    By.XPATH, ".//a[contains(., 'Impresión')]"
                )
                print("  ✓ Botón encontrado (estrategia 3: texto en footer)")
            except:
                pass

        # Estrategia 4: Buscar cualquier botón btn-primary en modal-footer
        if not boton_impresion:
            try:
                footer = driver.find_element(By.CLASS_NAME, "modal-footer")
                boton_impresion = footer.find_element(
                    By.XPATH, ".//a[contains(@class, 'btn-primary')]"
                )
                print("  ✓ Botón encontrado (estrategia 4: btn-primary en footer)")
            except:
                pass

        if not boton_impresion:
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


def descargar_pdf_y_json(
    driver, wait, carpeta_descargas, nombre_base, numero_remision=None
):
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


def cerrar_modal_si_esta_abierto(driver):
    """
    Cierra el modal si está abierto después de regresar a la ventana principal
    """
    try:
        # Verificar si hay un modal abierto
        modal = driver.find_element(By.CLASS_NAME, "modal-content")

        if modal.is_displayed():
            print("  🔍 Modal detectado abierto, cerrando...")

            # Buscar botón "Cerrar" en el footer
            try:
                boton_cerrar = driver.find_element(
                    By.XPATH,
                    "//button[@data-dismiss='modal' and contains(., 'Cerrar')]",
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", boton_cerrar
                )
                time.sleep(0.3)

                try:
                    boton_cerrar.click()
                except:
                    driver.execute_script("arguments[0].click();", boton_cerrar)

                print("  ✅ Modal cerrado con botón 'Cerrar'")
                time.sleep(0.5)
                return True
            except:
                pass

            # Si no funciona, intentar con la X
            try:
                boton_x = driver.find_element(
                    By.XPATH,
                    "//button[@class='close no-print' and @data-dismiss='modal']",
                )
                try:
                    boton_x.click()
                except:
                    driver.execute_script("arguments[0].click();", boton_x)

                print("  ✅ Modal cerrado con botón X")
                time.sleep(0.5)
                return True
            except:
                pass

            # Último recurso: ESC
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                print("  ✅ Modal cerrado con ESC")
                time.sleep(0.5)
                return True
            except:
                pass

        return False

    except Exception as e:
        print(f"  ⚠️ No se detectó modal abierto o error al cerrar: {e}")
        return False


def procesar_registro_con_reintentos(
    driver, fila, idx, ventana_principal, wait, pagina_actual=None, max_reintentos=3
):
    """
    Procesa un registro con sistema de reintentos (3 intentos con pausa en el último)
    """
    global ultimo_correlativo_exitoso

    correlativo = extraer_correlativo_de_fila(fila)
    if correlativo:
        print(f"  🏷️ Correlativo detectado: {correlativo}")
    else:
        print(
            "  ⚠️ No se pudo detectar correlativo en la fila. Se usará índice como fallback."
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
                By.XPATH, "//table[@id='remission_notes_table']//tbody/tr[@role='row']"
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

            # Re-extraer correlativo por si acaso
            if not correlativo:
                correlativo = extraer_correlativo_de_fila(fila)

            # Click en "Acciones"
            if not click_acciones_fila(driver, fila):
                if intento < max_reintentos:
                    continue
                else:
                    raise Exception("No se pudo hacer click en Acciones")

            # Click en "Ver"
            if not click_ver_en_dropdown(driver, fila, wait):
                if intento < max_reintentos:
                    continue
                else:
                    raise Exception("No se pudo hacer click en Ver")

            # Esperar y hacer click en "Impresión" del modal
            if not click_impresion_en_modal(driver, wait):
                # Intentar cerrar el modal antes de reintentar
                cerrar_modal_si_esta_abierto(driver)
                if intento < max_reintentos:
                    continue
                else:
                    raise Exception("No se pudo hacer click en Impresión del modal")

            # Cambiar a la nueva ventana y descargar
            if cambiar_a_nueva_ventana(driver, ventana_principal):
                time.sleep(0.5)

                if descargar_pdf_y_json(
                    driver, wait, DOWNLOAD_FOLDER, correlativo, idx + 1
                ):
                    print("  ✅ Descargas iniciadas correctamente")
                    
                    # Guardar el último correlativo exitoso
                    if correlativo:
                        ultimo_correlativo_exitoso = correlativo
                        guardar_ultimo_correlativo(correlativo)

                    # Cerrar la ventana de descarga
                    driver.close()
                    driver.switch_to.window(ventana_principal)
                    time.sleep(0.5)

                    # Cerrar el modal que quedó abierto
                    cerrar_modal_si_esta_abierto(driver)

                    return True
                else:
                    print("  ⚠️ Problemas con descargas")
                    driver.close()
                    driver.switch_to.window(ventana_principal)
                    cerrar_modal_si_esta_abierto(driver)
                    if intento < max_reintentos:
                        continue
                    else:
                        return False
            else:
                print("  ⚠️ No se pudo cambiar a la nueva ventana")
                cerrar_modal_si_esta_abierto(driver)
                if intento < max_reintentos:
                    continue
                else:
                    return False

        except Exception as e:
            print(f"  ❌ Error en intento {intento}: {e}")
            try:
                # Cerrar ventanas adicionales
                if len(driver.window_handles) > 1:
                    for handle in driver.window_handles:
                        if handle != ventana_principal:
                            driver.switch_to.window(handle)
                            driver.close()
                driver.switch_to.window(ventana_principal)

                # Cerrar modal si está abierto
                cerrar_modal_si_esta_abierto(driver)
                time.sleep(0.2)
            except:
                pass

            if intento < max_reintentos:
                continue
            else:
                return False

    return False


try:
    # Contar archivos iniciales
    print("📊 Contando archivos existentes en la carpeta de descargas...")
    pdfs_iniciales, jsons_iniciales = contar_archivos_iniciales()
    print(f"   📄 PDFs existentes: {pdfs_iniciales}")
    print(f"   📄 JSONs existentes: {jsons_iniciales}")
    print(f"   📦 Total archivos iniciales: {pdfs_iniciales + jsons_iniciales}")

    # Leer último correlativo exitoso
    print("\n🔍 Buscando último correlativo procesado...")
    ultimo_correlativo_procesado = leer_ultimo_correlativo_exitoso()

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

    # Click en "Notas de remisión"
    print("\n🔄 Navegando a 'Notas de remisión'...")
    notas_remision = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//a[@href='https://hermaco.findexbusiness.com/remission-notes']",
            )
        )
    )
    notas_remision.click()
    print("✅ Click en 'Notas de remisión'")

    time.sleep(2)
    print("📍 Estamos en la página de notas de remisión")

    # Filtro de fecha
    print("\n🔄 Abriendo filtro de fecha...")
    filtro_fecha = wait.until(
        EC.element_to_be_clickable((By.ID, "remission_date_filter"))
    )
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

    # Mostrar "Todos" los registros
    print("\n🔄 Cambiando filtro a mostrar TODOS los registros...")
    select_length = wait.until(
        EC.presence_of_element_located((By.NAME, "remission_notes_table_length"))
    )
    try:
        Select(select_length).select_by_value("-1")
        print("✅ Seleccionado 'Todos' los registros")
    except Exception as e:
        print(f"  ❌ No se pudo cambiar el tamaño de página: {e}")
        driver.quit()
        exit(1)

    # Dar tiempo a que carguen todos los registros
    print("⏳ Esperando 10 segundos a que carguen TODOS los registros...")
    time.sleep(10)
    print("✅ Registros cargados")

    # Hacer scroll hasta el final de la página
    print("\n🔄 Haciendo scroll hasta el final de la página...")
    scroll_to_bottom(driver)
    time.sleep(1)

    # PROCESAMIENTO: Como se muestran todos los registros, no hay paginación
    print("\n" + "=" * 60)
    print("🚀 INICIANDO PROCESAMIENTO DE NOTAS DE REMISIÓN")
    print("=" * 60)

    ventana_principal = driver.current_window_handle
    registros_procesados_totales = 0

    # Obtener todas las filas
    filas = driver.find_elements(
        By.XPATH, "//table[@id='remission_notes_table']//tbody/tr[@role='row']"
    )
    total_filas = len(filas)

    print(f"\n{'='*60}")
    print(f"📄 TOTAL DE REGISTROS: {total_filas}")
    print(f"{'='*60}")

    # Determinar desde dónde empezar (buscar con Ctrl+F si hay último correlativo)
    indice_ultimo = None
    if ultimo_correlativo_procesado:
        indice_ultimo = buscar_correlativo_con_ctrl_f(driver, ultimo_correlativo_procesado)
        
        if indice_ultimo is not None:
            print(f"✅ Último correlativo encontrado en índice {indice_ultimo}")
            print(f"⬆️ Se procesarán los registros ANTERIORES (hacia arriba) desde el índice {indice_ultimo - 1} hasta el índice 0")
        else:
            print(f"⚠️ Correlativo previo no encontrado, procesando desde el final hacia arriba")
            indice_ultimo = total_filas  # Empezar desde el final si no se encuentra

    else:
        print(f"ℹ️ No hay correlativo previo, procesando desde el final hacia arriba")
        indice_ultimo = total_filas  # Empezar desde el final

    # Procesar cada registro HACIA ARRIBA (índices menores = más recientes)
    # Rango: desde (indice_ultimo - 1) hasta 0 (inclusive), decrementando
    registros_a_procesar = indice_ultimo
    print(f"\n🔢 Se procesarán {registros_a_procesar} registros nuevos")
    
    for idx in range(indice_ultimo - 1, -1, -1):  # Desde indice_ultimo-1 hasta 0, decrementando
        try:
            driver.switch_to.window(ventana_principal)
            registros_procesados_totales += 1

            print(
                f"\n📄 Procesando registro {idx + 1}/{total_filas} (Procesados: {registros_procesados_totales}/{registros_a_procesar}) ..."
            )

            # Re-obtener las filas
            filas = driver.find_elements(
                By.XPATH, "//table[@id='remission_notes_table']//tbody/tr[@role='row']"
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
                pagina_actual="1",
                max_reintentos=3,
            )

            if not exito:
                print(f"  ❌ Registro falló después de 3 intentos")

        except Exception as e:
            print(f"  ❌ Error crítico en registro {idx + 1}: {e}")
            try:
                if len(driver.window_handles) > 1:
                    for handle in driver.window_handles:
                        if handle != ventana_principal:
                            driver.switch_to.window(handle)
                            driver.close()
                driver.switch_to.window(ventana_principal)
                cerrar_modal_si_esta_abierto(driver)
                time.sleep(0.3)
            except:
                pass
            continue

    print(f"\n{'='*60}")
    print(f"🎉 PROCESAMIENTO COMPLETADO")
    print(f"{'='*60}")
    print(f"✅ Total de registros procesados: {registros_procesados_totales}")

    # Contar archivos finales
    pdfs_finales = len(glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.pdf")))
    jsons_finales = len(
        [
            f
            for f in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.json"))
            if not ("registros_fallidos" in f or "ultimo_correlativo_exitoso" in f)
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
    
    if ultimo_correlativo_exitoso:
        print(f"📄 Último correlativo procesado: {ultimo_correlativo_exitoso}")

    input("\nPresiona Enter para cerrar el navegador...")

except KeyboardInterrupt:
    print("\n\n⚠️ Ejecución interrumpida por el usuario")
    if ultimo_correlativo_exitoso:
        print(f"� Último correlativo guardado: {ultimo_correlativo_exitoso}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    if ultimo_correlativo_exitoso:
        print(f"📄 Último correlativo guardado: {ultimo_correlativo_exitoso}")

finally:
    driver.quit()
    print("\n👋 Navegador cerrado")
