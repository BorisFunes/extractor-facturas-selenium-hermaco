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
import json
import traceback
from datetime import datetime

# Configuración de la carpeta de descargas
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "descargas_diarias")
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

# Variables globales
registros_fallidos = []
ultimo_dte_exitoso = None


def cargar_ultimo_exitoso():
    """
    Carga el último DTE exitoso desde el archivo JSON
    """
    archivo = os.path.join(DOWNLOAD_FOLDER, "ultimo_exitoso.json")
    try:
        if os.path.exists(archivo):
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"📂 Último DTE exitoso cargado: {data.get('ultimo_dte', 'N/A')}")
                return data.get("ultimo_dte")
        else:
            print("📂 No hay archivo de último exitoso. Comenzando desde el principio.")
            return None
    except Exception as e:
        print(f"⚠️ Error al cargar último exitoso: {e}")
        return None


def guardar_ultimo_exitoso(dte):
    """
    Guarda el último DTE exitoso en el archivo JSON
    """
    archivo = os.path.join(DOWNLOAD_FOLDER, "ultimo_exitoso.json")
    try:
        data = {
            "fecha_actualizacion": datetime.now().isoformat(),
            "ultimo_dte": dte,
        }
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Último DTE guardado: {dte}")
    except Exception as e:
        print(f"⚠️ Error al guardar último exitoso: {e}")


def buscar_dte_con_ctrl_f(driver, dte_buscado):
    """
    Busca un DTE específico usando Ctrl+F y retorna su índice si lo encuentra
    """
    try:
        print(f"🔍 Buscando DTE: {dte_buscado}")

        # Abrir búsqueda con Ctrl+F
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys("f").key_up(Keys.CONTROL).perform()
        time.sleep(0.5)

        # Escribir el DTE
        actions.send_keys(dte_buscado).perform()
        time.sleep(1)

        # Presionar Enter
        actions.send_keys(Keys.ENTER).perform()
        time.sleep(2)

        # Cerrar búsqueda
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)

        # Buscar la celda con el DTE
        try:
            celda_dte = driver.find_element(
                By.XPATH, f"//td[contains(normalize-space(.), '{dte_buscado}')]"
            )
            fila = celda_dte.find_element(By.XPATH, "./ancestor::tr[@role='row']")

            # Hacer scroll a la fila
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", fila
            )
            time.sleep(0.5)

            # Obtener el índice
            filas = driver.find_elements(
                By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
            )
            for idx, f in enumerate(filas):
                if f == fila:
                    print(f"✅ DTE encontrado en índice: {idx}")
                    return idx

            print("⚠️ DTE encontrado pero no se pudo determinar el índice")
            return None

        except Exception:
            print(f"❌ DTE no encontrado en la tabla")
            return None

    except Exception as e:
        print(f"❌ Error al buscar DTE: {e}")
        return None


def extraer_dte_de_fila(fila):
    """
    Extrae el DTE de una fila
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
    Extrae la fecha de una fila
    """
    try:
        celdas = fila.find_elements(By.TAG_NAME, "td")
        for celda in celdas:
            texto = celda.text.strip()
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

        def obtener_menu_visible(_):
            menus = fila.find_elements(
                By.XPATH, ".//ul[contains(@class,'dropdown-menu')]"
            )
            visibles = [m for m in menus if m.is_displayed()]
            return visibles[0] if visibles else False

        menu = WebDriverWait(driver, 5).until(obtener_menu_visible)

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
        print("  ⏳ Esperando que aparezca el modal...")
        modal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
        )

        print("  ✅ Modal de detalles abierto")
        time.sleep(2)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "modal-footer"))
            )
            print("  ✓ Footer del modal cargado")
        except:
            print("  ⚠️ Footer del modal no encontrado, continuando...")

        boton_impresion = None

        # Buscar botón de impresión
        try:
            boton_impresion = driver.find_element(
                By.XPATH,
                "//a[contains(@onclick, 'openDteUrl') and contains(@class, 'print-invoice')]",
            )
            print("  ✓ Botón encontrado (onclick + clase)")
        except:
            pass

        if not boton_impresion:
            try:
                boton_impresion = driver.find_element(
                    By.XPATH, "//a[contains(@class, 'print-invoice')]"
                )
                print("  ✓ Botón encontrado (clase print-invoice)")
            except:
                pass

        if not boton_impresion:
            try:
                boton_impresion = modal.find_element(
                    By.XPATH,
                    ".//a[contains(@class, 'print-invoice') and contains(@data-href, '/print')]",
                )
                print("  ✓ Botón encontrado (clase + data-href en modal)")
            except:
                pass

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

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", boton_impresion
        )
        time.sleep(0.5)

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


def descargar_pdf_y_json(driver, wait):
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
    Cierra el modal si está abierto
    """
    try:
        modal = driver.find_element(By.CLASS_NAME, "modal-content")

        if modal.is_displayed():
            print("  🔍 Modal detectado abierto, cerrando...")

            # Intentar cerrar con botón "Cerrar"
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

            # Intentar con data-dismiss
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

            # Intentar con botón X
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

            # Intentar con ESC
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
        print("  ⚠️ No se pudo detectar DTE en la fila")

    try:
        # Re-obtener la fila
        driver.switch_to.window(ventana_principal)
        filas = driver.find_elements(
            By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
        )
        if idx >= len(filas):
            print("  ⚠️ La fila ya no está disponible")
            return False
        fila = filas[idx]

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fila)
        time.sleep(0.3)

        # Click en Acciones
        if not click_acciones_fila(driver, fila):
            return False

        # Click en Ver
        if not click_ver_en_dropdown(driver, fila, wait):
            return False

        # Click en Impresión del modal
        if not click_impresion_en_modal(driver, wait):
            return False

        # Cambiar a ventana de impresión
        if not cambiar_a_nueva_ventana(driver, ventana_principal):
            return False

        time.sleep(0.5)

        # Descargar archivos
        if descargar_pdf_y_json(driver, wait):
            print("  ✅ Descarga completada correctamente")
            ultimo_dte_exitoso = dte if dte else f"registro_{idx + 1}"

            # Guardar inmediatamente el último exitoso
            if dte:
                guardar_ultimo_exitoso(dte)

            print("  ⏳ Esperando a que se completen las descargas...")
            time.sleep(2)

            # Cerrar ventana de impresión
            print("  🔒 Cerrando ventana de descarga...")
            driver.close()
            driver.switch_to.window(ventana_principal)
            print("  ✅ Ventana cerrada, recursos liberados")

            cerrar_modal_si_esta_abierto(driver)

            return True
        else:
            time.sleep(1)

            print("  🔒 Cerrando ventana de descarga...")
            driver.close()
            driver.switch_to.window(ventana_principal)
            print("  ✅ Ventana cerrada")

            cerrar_modal_si_esta_abierto(driver)

            return False

    except Exception as e:
        print(f"  ❌ Error al procesar registro: {e}")
        try:
            if len(driver.window_handles) > 1:
                print("  🔒 Cerrando ventanas adicionales por error...")
                for handle in driver.window_handles:
                    if handle != ventana_principal:
                        driver.switch_to.window(handle)
                        driver.close()
                        print("  ✅ Ventana adicional cerrada")
            driver.switch_to.window(ventana_principal)

            cerrar_modal_si_esta_abierto(driver)
        except:
            pass
        return False


def guardar_reporte_fallidos():
    """
    Guarda el reporte de registros fallidos
    """
    if registros_fallidos:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_fallidos = os.path.join(
            DOWNLOAD_FOLDER, f"reporte_fallidos_{timestamp}.json"
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

    # Filtro de fecha - HOY
    print("\n🔄 Abriendo filtro de fecha...")
    filtro_fecha = wait.until(EC.element_to_be_clickable((By.ID, "sell_date_filter")))
    filtro_fecha.click()
    print("✅ Click en 'Filtrar por fecha' (desplegable abierto)")

    time.sleep(2)
    try:
        hoy = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//li[contains(text(), 'Hoy')] | //a[contains(text(), 'Hoy')] | //span[contains(text(), 'Hoy')]",
                )
            )
        )
        hoy.click()
        print("✅ Seleccionado 'Hoy'")
    except:
        print("⚠️ No se encontró 'Hoy'. Continuando...")

    time.sleep(3)

    # Mostrar TODOS los registros
    print("\n🔄 Cambiando filtro a mostrar TODOS los registros...")
    select_length = wait.until(
        EC.presence_of_element_located((By.NAME, "sell_table_length"))
    )
    try:
        # Buscar la opción "Todos" o "-1" como valor
        select_obj = Select(select_length)
        opciones = [option.get_attribute("value") for option in select_obj.options]
        print(f"  📋 Opciones disponibles: {opciones}")

        # Intentar seleccionar "Todos" (puede ser "-1" o "all")
        if "-1" in opciones:
            Select(select_length).select_by_value("-1")
            print("✅ Seleccionado mostrar TODOS los registros")
        elif "all" in opciones:
            Select(select_length).select_by_value("all")
            print("✅ Seleccionado mostrar TODOS los registros")
        else:
            # Si no existe "Todos", usar el valor más alto
            valores_numericos = [int(v) for v in opciones if v.isdigit()]
            if valores_numericos:
                max_valor = str(max(valores_numericos))
                Select(select_length).select_by_value(max_valor)
                print(
                    f"✅ Seleccionado mostrar {max_valor} registros (máximo disponible)"
                )
            else:
                print("⚠️ No se pudo determinar cómo mostrar todos los registros")
    except Exception as e:
        print(f"  ❌ No se pudo cambiar el tamaño de página: {e}")

    # Dar tiempo a que carguen los registros
    print("⏳ Esperando 5 segundos a que carguen los registros...")
    time.sleep(5)
    print("✅ Registros cargados")

    # Hacer scroll al final de la tabla
    print("\n🔄 Desplazando al final de la página...")
    try:
        # Obtener todas las filas
        filas = driver.find_elements(
            By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
        )
        if filas:
            ultima_fila = filas[-1]
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", ultima_fila
            )
            time.sleep(1)
            print(f"✅ Desplazado al final de la tabla ({len(filas)} registros)")
        else:
            print("⚠️ No se encontraron registros en la tabla")
    except Exception as e:
        print(f"⚠️ Error al hacer scroll: {e}")

    # Cargar el último DTE exitoso
    ultimo_dte_cargado = cargar_ultimo_exitoso()

    # Obtener todas las filas
    filas = driver.find_elements(
        By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
    )
    total_filas = len(filas)
    print(f"\n📊 Total de registros en tabla: {total_filas}")

    if total_filas == 0:
        print("⚠️ No hay registros para procesar hoy")
        driver.quit()
        exit(0)

    # Determinar desde dónde empezar
    indice_inicio = None

    if ultimo_dte_cargado:
        print(f"\n🔍 Buscando último DTE procesado: {ultimo_dte_cargado}")
        indice_ultimo = buscar_dte_con_ctrl_f(driver, ultimo_dte_cargado)

        if indice_ultimo is not None:
            # Empezar desde el ANTERIOR al último procesado (hacia arriba/más reciente)
            indice_inicio = indice_ultimo - 1
            print(
                f"✅ Se continuará desde el índice {indice_inicio} (anterior al último procesado)"
            )
        else:
            print("⚠️ No se encontró el último DTE procesado")
            print("   Se procesará desde el final de la tabla")
            indice_inicio = total_filas - 1
    else:
        # Si no hay último exitoso, empezar desde el final
        indice_inicio = total_filas - 1
        print(f"📍 Comenzando desde el final de la tabla (índice {indice_inicio})")

    # Validar que hay registros para procesar
    if indice_inicio < 0:
        print("⚠️ No hay registros nuevos para procesar")
        driver.quit()
        exit(0)

    registros_a_procesar = indice_inicio + 1
    print(f"\n✅ Se procesarán {registros_a_procesar} registros:")
    print(f"   Desde índice: {indice_inicio} (último registro) - HACIA ARRIBA")
    print(f"   Hasta índice: 0 (primer registro)")
    print(f"   Dirección: ⬆️ Hacia registros más recientes (índices menores)")

    # Procesamiento de registros
    print("\n" + "=" * 60)
    print("🚀 INICIANDO PROCESAMIENTO DE REGISTROS DE HOY")
    print("=" * 60)

    ventana_principal = driver.current_window_handle
    registros_procesados = 0
    registros_exitosos = 0

    # Procesar desde indice_inicio hacia arriba (índices menores)
    for idx in range(indice_inicio, -1, -1):
        try:
            driver.switch_to.window(ventana_principal)
            registros_procesados += 1

            print(
                f"\n📄 Procesando registro {registros_procesados}/{registros_a_procesar} (índice {idx}) ..."
            )

            # Re-obtener las filas
            filas = driver.find_elements(
                By.XPATH, "//table[@id='sell_table']//tbody/tr[@role='row']"
            )
            if idx >= len(filas):
                print(f"  ⚠️ Registro {idx} ya no está disponible")
                continue
            fila = filas[idx]

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
    print(f"   Total de registros procesados: {registros_procesados}")
    print(f"   ✅ Registros exitosos: {registros_exitosos}")
    print(f"   ❌ Registros fallidos: {len(registros_fallidos)}")
    if ultimo_dte_exitoso:
        print(f"   🏷️ Último DTE exitoso: {ultimo_dte_exitoso}")
    print(f"\n📁 Archivos descargados en: {DOWNLOAD_FOLDER}")

    # Guardar reporte de fallidos
    guardar_reporte_fallidos()

    input("\nPresiona Enter para cerrar el navegador...")

except KeyboardInterrupt:
    print("\n\n⚠️ Ejecución interrumpida por el usuario")
    guardar_reporte_fallidos()
    print("📊 Reportes guardados antes de salir")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\n📊 Detalles del error:")
    traceback.print_exc()
    guardar_reporte_fallidos()

finally:
    driver.quit()
    print("\n👋 Navegador cerrado")
