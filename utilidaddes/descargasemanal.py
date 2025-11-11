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
import traceback
from pathlib import Path
from datetime import datetime

# Configuración de la carpeta de descargas
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "descargas_erp")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ⚠️ CONFIGURACIÓN DE BÚSQUEDA
DTE_INICIAL = "DTE-03-M001P001-000000000001376"
FECHA_LIMITE = "10/11/2025 08:13 am"

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
ultimo_dte_exitoso = None


def buscar_dte_en_tabla(driver, dte_buscado):
    """
    Busca un DTE específico en la tabla usando Ctrl+F.
    Retorna la fila si lo encuentra, o None si no lo encuentra.
    """
    try:
        print(f"\n🔍 Buscando DTE: {dte_buscado}")

        # Abrir búsqueda con Ctrl+F
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys("f").key_up(Keys.CONTROL).perform()
        time.sleep(0.5)

        # Escribir el DTE en el cuadro de búsqueda
        actions.send_keys(dte_buscado).perform()
        print("  ⏳ Escribiendo DTE en búsqueda...")
        time.sleep(1)

        # Presionar Enter para buscar
        actions.send_keys(Keys.ENTER).perform()
        print("  ⏳ Esperando respuesta del frontend...")
        time.sleep(3)

        # Cerrar el cuadro de búsqueda
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)

        # Intentar encontrar la fila que contiene el DTE
        try:
            celda_dte = driver.find_element(
                By.XPATH, f"//td[contains(normalize-space(.), '{dte_buscado}')]"
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


def buscar_fecha_limite_en_tabla(driver, fecha_buscada):
    """
    Busca una fecha específica en la tabla usando Ctrl+F para encontrar el límite.
    Retorna el índice de la fila si lo encuentra, o None si no lo encuentra.
    """
    try:
        print(f"\n🔍 Buscando fecha límite: {fecha_buscada}")

        # Abrir búsqueda con Ctrl+F
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys("f").key_up(Keys.CONTROL).perform()
        time.sleep(0.5)

        # Escribir la fecha en el cuadro de búsqueda
        actions.send_keys(fecha_buscada).perform()
        print("  ⏳ Escribiendo fecha en búsqueda...")
        time.sleep(1)

        # Presionar Enter para buscar
        actions.send_keys(Keys.ENTER).perform()
        print("  ⏳ Esperando respuesta del frontend...")
        time.sleep(3)

        # Cerrar el cuadro de búsqueda
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)

        # Intentar encontrar la fila que contiene la fecha
        try:
            celda_fecha = driver.find_element(
                By.XPATH, f"//td[contains(normalize-space(.), '{fecha_buscada}')]"
            )

            # Obtener la fila completa
            fila = celda_fecha.find_element(By.XPATH, "./ancestor::tr[@role='row']")

            # Hacer scroll a la fila
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", fila
            )
            time.sleep(0.5)

            # Obtener el índice de la fila
            filas = driver.find_elements(
                By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
            )
            for idx, f in enumerate(filas):
                if f == fila:
                    print(f"✅ Fecha límite encontrada en índice {idx}")
                    return idx

            print(f"⚠️ No se pudo determinar el índice de la fecha")
            return None

        except Exception as e:
            print(f"❌ Fecha límite no encontrada en la tabla: {e}")
            return None

    except Exception as e:
        print(f"❌ Error al buscar fecha límite: {e}")
        return None


def obtener_indice_fila(driver, fila):
    """
    Obtiene el índice de una fila dentro de la tabla
    """
    try:
        filas = driver.find_elements(
            By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
        )
        for idx, f in enumerate(filas):
            if f == fila:
                return idx
        return None
    except:
        return None


def extraer_dte_de_fila(fila):
    """
    Busca en la fila una celda que contenga el texto del DTE
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


def extraer_fecha_de_fila(fila):
    """
    Busca en la fila una celda que contenga la fecha
    Asume que la fecha está en un formato como "10/11/2025 08:13 am"
    """
    try:
        # Buscar todas las celdas de la fila
        celdas = fila.find_elements(By.TAG_NAME, "td")
        for celda in celdas:
            texto = celda.text.strip()
            # Buscar patrón de fecha (dd/mm/yyyy)
            if "/" in texto and any(char.isdigit() for char in texto):
                return texto
    except Exception:
        pass
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

        # Esperar a que el contenido del modal se cargue
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

        # Buscar el botón de impresión
        boton_impresion = None

        # Estrategia 1: Buscar por onclick que contiene openDteUrl
        try:
            boton_impresion = driver.find_element(
                By.XPATH,
                "//a[contains(@onclick, 'openDteUrl') and contains(@class, 'print-invoice')]",
            )
            print("  ✓ Botón encontrado (onclick + clase)")
        except:
            pass

        # Estrategia 2: Buscar solo por clase print-invoice
        if not boton_impresion:
            try:
                boton_impresion = driver.find_element(
                    By.XPATH, "//a[contains(@class, 'print-invoice')]"
                )
                print("  ✓ Botón encontrado (clase print-invoice)")
            except:
                pass

        # Estrategia 3: Buscar por clase y data-href en el modal
        if not boton_impresion:
            try:
                boton_impresion = modal.find_element(
                    By.XPATH,
                    ".//a[contains(@class, 'print-invoice') and contains(@data-href, '/print')]",
                )
                print("  ✓ Botón encontrado (clase + data-href en modal)")
            except:
                pass

        # Estrategia 4: Buscar por texto "Impresión"
        if not boton_impresion:
            try:
                footer = driver.find_element(By.CLASS_NAME, "modal-footer")
                boton_impresion = footer.find_element(
                    By.XPATH, ".//a[contains(., 'Impresión')]"
                )
                print("  ✓ Botón encontrado (texto en footer)")
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


def descargar_pdf_y_json(driver, wait, carpeta_descargas, nombre_base):
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


def procesar_registro_con_modal(driver, fila, idx, ventana_principal, wait):
    """
    Procesa un registro usando el flujo de modal (Ver -> Modal -> Impresión)
    """
    global ultimo_dte_exitoso

    dte = extraer_dte_de_fila(fila)
    if dte:
        print(f"  🏷️ DTE detectado: {dte}")
    else:
        print("  ⚠️ No se pudo detectar DTE en la fila. Se usará índice como fallback.")

    try:
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
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fila)
        time.sleep(0.3)

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

        # 5. Descargar archivos
        if descargar_pdf_y_json(driver, wait, DOWNLOAD_FOLDER, dte):
            print("  ✅ Descarga completada correctamente")
            ultimo_dte_exitoso = dte if dte else f"registro_{idx + 1}"

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
        print(f"  ❌ Error al procesar registro: {e}")
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


def guardar_reporte_json():
    """
    Guarda los reportes JSON al finalizar
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Guardar registros fallidos
    if registros_fallidos:
        archivo_fallidos = os.path.join(
            DOWNLOAD_FOLDER, f"reporte_descarga_fallidas_{timestamp}.json"
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
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"📄 Último DTE exitoso guardado: {archivo_ultimo}")


try:
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

    # Filtro de fecha - ÚLTIMOS 7 DÍAS
    print("\n🔄 Abriendo filtro de fecha...")
    filtro_fecha = wait.until(EC.element_to_be_clickable((By.ID, "sell_date_filter")))
    filtro_fecha.click()
    print("✅ Click en 'Filtrar por fecha' (desplegable abierto)")

    time.sleep(2)
    try:
        ultimos_7_dias = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//li[contains(text(), 'Los últimos 7 días')] | //a[contains(text(), 'Los últimos 7 días')] | //span[contains(text(), 'Los últimos 7 días')]",
                )
            )
        )
        ultimos_7_dias.click()
        print("✅ Seleccionado 'Los últimos 7 días'")
    except:
        print("⚠️ No se encontró 'Los últimos 7 días'. Continuando...")

    time.sleep(3)

    # Mostrar 200 registros por página
    print("\n🔄 Cambiando filtro a 200 registros por página...")
    select_length = wait.until(
        EC.presence_of_element_located((By.NAME, "sell_table_length"))
    )
    try:
        Select(select_length).select_by_value("200")
        print("✅ Seleccionado 200 registros por página")
    except Exception as e:
        print(f"  ❌ No se pudo cambiar el tamaño de página: {e}")
        driver.quit()
        exit(1)

    # Dar tiempo a que carguen los registros
    print("⏳ Esperando 5 segundos a que carguen los registros...")
    time.sleep(5)
    print("✅ Registros cargados")

    # ⚠️ PASO 1: Buscar el DTE inicial
    print("\n" + "=" * 60)
    print("🔍 BUSCANDO DTE INICIAL")
    print("=" * 60)
    print(f"DTE a buscar: {DTE_INICIAL}")

    fila_dte_inicial = buscar_dte_en_tabla(driver, DTE_INICIAL)

    if not fila_dte_inicial:
        print(f"\n❌ ERROR: No se encontró el DTE inicial {DTE_INICIAL}")
        print("No se puede continuar con el procesamiento.")
        driver.quit()
        exit(1)

    indice_dte_inicial = obtener_indice_fila(driver, fila_dte_inicial)
    if indice_dte_inicial is None:
        print(f"\n❌ ERROR: No se pudo determinar el índice del DTE inicial")
        driver.quit()
        exit(1)

    print(f"✅ DTE inicial encontrado en índice: {indice_dte_inicial}")

    # ⚠️ PASO 2: Buscar la fecha límite
    print("\n" + "=" * 60)
    print("🔍 BUSCANDO FECHA LÍMITE")
    print("=" * 60)
    print(f"Fecha límite: {FECHA_LIMITE}")

    indice_fecha_limite = buscar_fecha_limite_en_tabla(driver, FECHA_LIMITE)

    if indice_fecha_limite is None:
        print(f"⚠️ No se encontró la fecha límite exacta")
        print("Se procesarán todos los registros desde el DTE inicial hasta el final")
        # Obtener total de filas
        filas = driver.find_elements(
            By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
        )
        indice_fecha_limite = len(filas)  # Procesar hasta el final
    else:
        print(f"✅ Fecha límite encontrada en índice: {indice_fecha_limite}")
        # El límite es ANTES de la fecha límite (no incluir el 10/11/2025)
        print(f"⚠️ Se detendrá ANTES del índice {indice_fecha_limite}")
        print(f"   (No se descargará la fecha {FECHA_LIMITE} ni registros posteriores)")

    # ⚠️ PASO 3: Determinar el rango de procesamiento
    print("\n" + "=" * 60)
    print("📋 RANGO DE PROCESAMIENTO")
    print("=" * 60)

    # Obtener todas las filas
    filas = driver.find_elements(
        By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
    )
    total_filas = len(filas)
    print(f"Total de registros en tabla: {total_filas}")

    # La tabla está ordenada de MÁS RECIENTE (índice 0) a MÁS ANTIGUO (índice N)
    # Debemos ir HACIA ARRIBA (índices menores) desde el DTE inicial

    # Calcular el rango - IR HACIA ARRIBA desde el DTE inicial
    indice_inicio = (
        indice_dte_inicial - 1
    )  # Empezar desde el ANTERIOR al DTE inicial (hacia arriba/más reciente)

    # El índice fin es donde está la fecha límite (o el inicio de la tabla si no se encuentra)
    if indice_fecha_limite is not None:
        indice_fin = (
            indice_fecha_limite + 1
        )  # Detenerse DESPUÉS de la fecha límite (no incluirla)
    else:
        indice_fin = 0  # Si no se encuentra la fecha límite, ir hasta el inicio

    # Validar que hay registros para procesar
    if indice_inicio < indice_fin:
        print(
            f"\n⚠️ No hay registros para procesar entre el DTE inicial y la fecha límite"
        )
        print(f"   Índice DTE inicial: {indice_dte_inicial}")
        print(f"   Índice inicio (anterior al DTE): {indice_inicio}")
        print(
            f"   Índice fecha límite: {indice_fecha_limite if indice_fecha_limite is not None else 'N/A'}"
        )
        print(f"   Índice fin: {indice_fin}")
        driver.quit()
        exit(0)

    registros_a_procesar = indice_inicio - indice_fin + 1
    print(f"\n✅ Se procesarán {registros_a_procesar} registros:")
    print(
        f"   Desde índice: {indice_inicio} (anterior al DTE {DTE_INICIAL}) - HACIA ARRIBA"
    )
    print(f"   Hasta índice: {indice_fin} (después de {FECHA_LIMITE})")
    print(f"   Dirección: ⬆️ Hacia registros más recientes (índices menores)")

    # ⚠️ PASO 4: Procesamiento de registros
    print("\n" + "=" * 60)
    print("🚀 INICIANDO PROCESAMIENTO DE REGISTROS")
    print("=" * 60)

    ventana_principal = driver.current_window_handle
    registros_procesados = 0
    registros_exitosos = 0

    # Procesar desde indice_inicio HACIA ABAJO hasta indice_fin (hacia registros más recientes)
    # Es decir, de índice mayor a índice menor
    for idx in range(
        indice_inicio, indice_fin - 1, -1
    ):  # El -1 hace que vaya hacia abajo
        try:
            driver.switch_to.window(ventana_principal)
            registros_procesados += 1

            print(
                f"\n📄 Procesando registro {registros_procesados}/{registros_a_procesar} (índice {idx}) ..."
            )

            # Re-obtener las filas para evitar stale elements
            filas = driver.find_elements(
                By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
            )
            if idx >= len(filas):
                print(f"  ⚠️ Registro {idx} ya no está disponible")
                continue
            fila = filas[idx]

            # Verificar fecha antes de procesar
            fecha_fila = extraer_fecha_de_fila(fila)
            if fecha_fila:
                print(f"  📅 Fecha del registro: {fecha_fila}")
                # Verificar si llegamos a la fecha límite
                if FECHA_LIMITE in fecha_fila:
                    print(f"\n🛑 DETENIDO: Se alcanzó la fecha límite ({FECHA_LIMITE})")
                    print(f"   Este registro NO se descargará")
                    break

            # Procesar con el flujo de modal
            exito = procesar_registro_con_modal(
                driver, fila, idx, ventana_principal, wait
            )

            if exito:
                registros_exitosos += 1
                print(
                    f"  ✅ Registro procesado exitosamente ({registros_exitosos}/{registros_procesados})"
                )
            else:
                dte = extraer_dte_de_fila(fila)
                fecha = extraer_fecha_de_fila(fila)
                registros_fallidos.append(
                    {
                        "posicion": idx + 1,
                        "dte": dte if dte else f"registro_{idx + 1}",
                        "fecha": fecha if fecha else "desconocida",
                        "error": "No se pudo completar la descarga",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        except Exception as e:
            print(f"  ❌ Error crítico en registro {idx}: {e}")
            filas_actuales = driver.find_elements(
                By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
            )
            dte = (
                extraer_dte_de_fila(filas_actuales[idx])
                if idx < len(filas_actuales)
                else None
            )
            fecha = (
                extraer_fecha_de_fila(filas_actuales[idx])
                if idx < len(filas_actuales)
                else None
            )
            registros_fallidos.append(
                {
                    "posicion": idx + 1,
                    "dte": dte if dte else f"registro_{idx + 1}",
                    "fecha": fecha if fecha else "desconocida",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            try:
                if len(driver.window_handles) > 1:
                    for handle in driver.window_handles:
                        if handle != ventana_principal:
                            driver.switch_to.window(handle)
                            driver.close()
                driver.switch_to.window(ventana_principal)
                cerrar_modal_si_esta_abierto(driver)
            except:
                pass
            continue

    print(f"\n{'='*60}")
    print(f"🎉 PROCESAMIENTO COMPLETADO")
    print(f"{'='*60}")
    print(f"📊 RESUMEN:")
    print(f"   DTE inicial: {DTE_INICIAL} (índice {indice_dte_inicial})")
    print(
        f"   Fecha límite: {FECHA_LIMITE} (índice {indice_fecha_limite if indice_fecha_limite else 'N/A'})"
    )
    print(
        f"   Rango procesado: desde índice {indice_inicio} hasta índice {indice_fin} (⬆️ hacia arriba)"
    )
    print(f"   Total de registros procesados: {registros_procesados}")
    print(f"   ✅ Registros exitosos: {registros_exitosos}")
    print(f"   ❌ Registros fallidos: {len(registros_fallidos)}")
    print(f"\n📁 Archivos descargados en: {DOWNLOAD_FOLDER}")

    # Guardar reportes JSON
    guardar_reporte_json()

    input("\nPresiona Enter para cerrar el navegador...")

except KeyboardInterrupt:
    print("\n\n⚠️ Ejecución interrumpida por el usuario")
    guardar_reporte_json()
    print("📊 Reportes guardados antes de salir")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\n📊 Detalles del error:")
    traceback.print_exc()
    guardar_reporte_json()

finally:
    driver.quit()
    print("\n👋 Navegador cerrado")
