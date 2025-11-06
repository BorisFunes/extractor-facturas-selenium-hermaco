import json
import os
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def mostrar_menu():
    """
    Muestra el menú principal y retorna la opción seleccionada
    """
    print("\n" + "=" * 80)
    print("GESTOR DE DUPLICADOS - FACTURAS HERMACO")
    print("=" * 80)
    print("\nSeleccione una opción:")
    print("  1. Detectar duplicados en JSON")
    print("  2. Detectar duplicados en PDF")
    print("  3. Eliminar duplicados")
    print("  4. Salir")
    print("-" * 80)

    while True:
        opcion = input("\nIngrese el número de opción (1-4): ").strip()
        if opcion in ["1", "2", "3", "4"]:
            return opcion
        else:
            print("⚠️  Opción inválida. Por favor ingrese 1, 2, 3 o 4.")


def eliminar_duplicados():
    """
    Elimina archivos duplicados basándose en un archivo JSON de duplicados
    Soporta tanto duplicados de JSON como de PDF
    """
    print("\n" + "=" * 80)
    print("ELIMINADOR DE DUPLICADOS")
    print("=" * 80)

    # Solicitar el archivo JSON de duplicados
    print("\nIngrese la ruta del archivo JSON con los duplicados")
    print(
        "(Por ejemplo: duplicados_20251105_091226.json o duplicados_pdf_20251106_103230.json)"
    )
    archivo_duplicados_input = input("\nRuta del archivo: ").strip()

    # Remover comillas si las tiene
    archivo_duplicados = archivo_duplicados_input.strip('"').strip("'")

    # Verificar que el archivo existe
    if not os.path.exists(archivo_duplicados):
        print(f"\n❌ Error: El archivo '{archivo_duplicados}' no existe")
        return

    # Leer el archivo de duplicados
    try:
        with open(archivo_duplicados, "r", encoding="utf-8") as f:
            datos_duplicados = json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n❌ Error al leer el archivo JSON: {e}")
        return
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return

    # Extraer la lista de duplicados
    duplicados = datos_duplicados.get("duplicados", [])

    if not duplicados:
        print("\n⚠️  No se encontraron duplicados en el archivo JSON")
        return

    # Determinar el tipo de duplicados (JSON o PDF)
    tipo_duplicado = duplicados[0].get("tipo", "")
    es_duplicado_pdf = tipo_duplicado == "duplicado_pdf"

    print(f"\n📋 Se encontraron {len(duplicados)} duplicados en el archivo")
    print(f"📦 Tipo de duplicados: {'PDF' if es_duplicado_pdf else 'JSON'}")
    print("-" * 80)

    # Confirmar antes de eliminar
    confirmacion = (
        input("\n¿Desea proceder con la eliminación? (S/N): ").strip().upper()
    )

    if confirmacion != "S":
        print("\n❌ Operación cancelada por el usuario")
        return

    # Determinar la carpeta de descargas
    if es_duplicado_pdf:
        # Para PDF, usar la carpeta del JSON
        carpeta_descargas = Path(
            datos_duplicados.get("carpeta_analizada", "descargas_erp")
        )
    else:
        # Para JSON, usar descargas_erp por defecto
        carpeta_descargas = Path("descargas_erp")

    if not carpeta_descargas.exists():
        print(f"\n❌ Error: La carpeta {carpeta_descargas} no existe")
        return

    print(f"📁 Carpeta de trabajo: {carpeta_descargas}")
    print("-" * 80)

    # Contadores
    eliminados = 0
    no_encontrados = 0
    errores = 0

    print("\n🗑️  Eliminando archivos duplicados...")
    print("-" * 80)

    # Procesar cada duplicado
    for duplicado in duplicados:
        if es_duplicado_pdf:
            # Procesar duplicados PDF
            archivo_original = duplicado.get("archivo_original")
            archivo_duplicado = duplicado.get("archivo_duplicado")
            nombre_base = duplicado.get("nombre_base", "N/A")

            if not archivo_duplicado:
                print(f"⚠️  Registro sin archivo_duplicado: {duplicado}")
                continue

            # Ruta completa del archivo a eliminar (el duplicado)
            ruta_archivo_duplicado = carpeta_descargas / archivo_duplicado

            # Verificar que el archivo existe
            if not ruta_archivo_duplicado.exists():
                print(f"⚠️  No encontrado: {archivo_duplicado}")
                no_encontrados += 1
                continue

            try:
                # Eliminar el archivo duplicado
                os.remove(ruta_archivo_duplicado)
                print(f"✓ Eliminado: {archivo_duplicado}")
                print(f"  (Conservado: {archivo_original})")
                print(f"  Nombre base: {nombre_base}")
                eliminados += 1
            except Exception as e:
                print(f"❌ Error al eliminar {archivo_duplicado}: {e}")
                errores += 1
        else:
            # Procesar duplicados JSON (lógica original)
            archivo1 = duplicado.get("archivo1")
            archivo2 = duplicado.get("archivo2")
            numero_control = duplicado.get("numeroControl", "N/A")

            if not archivo1 or not archivo2:
                print(f"⚠️  Registro sin archivo1 o archivo2: {duplicado}")
                continue

            # Ruta completa del archivo a eliminar (archivo1)
            ruta_archivo1 = carpeta_descargas / archivo1

            # Verificar que el archivo existe
            if not ruta_archivo1.exists():
                print(f"⚠️  No encontrado: {archivo1}")
                no_encontrados += 1
                continue

            try:
                # Eliminar el archivo1
                os.remove(ruta_archivo1)
                print(f"✓ Eliminado: {archivo1}")
                print(f"  (Conservado: {archivo2})")
                print(f"  numeroControl: {numero_control}")
                eliminados += 1
            except Exception as e:
                print(f"❌ Error al eliminar {archivo1}: {e}")
                errores += 1

    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE ELIMINACIÓN")
    print("=" * 80)
    print(f"Carpeta procesada: {carpeta_descargas}")
    print(f"Total de duplicados procesados: {len(duplicados)}")
    print(f"✓ Archivos eliminados: {eliminados}")
    print(f"⚠️  Archivos no encontrados: {no_encontrados}")
    print(f"❌ Errores: {errores}")
    print("=" * 80)


def obtener_hash_contenido(datos):
    """
    Convierte el diccionario a una cadena JSON ordenada para comparación
    """
    # Excluimos campos que no son relevantes para la comparación
    datos_copia = datos.copy()
    # Convertir a string JSON con claves ordenadas para comparación consistente
    return json.dumps(datos_copia, sort_keys=True, ensure_ascii=False)


def son_archivos_identicos(datos1, datos2):
    """
    Compara si dos archivos JSON son idénticos en su contenido
    """
    return obtener_hash_contenido(datos1) == obtener_hash_contenido(datos2)


def detector_duplicados():
    """
    Detecta archivos duplicados y con correlación inconsistente
    """
    # Ruta de la carpeta con los archivos JSON
    carpeta_descargas = Path("descargas_erp")

    # Verificar que la carpeta existe
    if not carpeta_descargas.exists():
        print(f"Error: La carpeta {carpeta_descargas} no existe")
        return

    # Diccionarios para almacenar los resultados
    archivos_por_numero_control = defaultdict(list)
    duplicados_completos = []
    sin_correlacion = []

    # Obtener todos los archivos JSON
    archivos_json = list(carpeta_descargas.glob("*.json"))
    total_archivos = len(archivos_json)

    print(f"🔍 Analizando {total_archivos} archivos JSON...")
    print("-" * 80)

    # Primera pasada: agrupar por numeroControl
    archivos_datos = {}
    errores = 0

    for archivo in archivos_json:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)

            numero_control = datos.get("identificacion", {}).get("numeroControl")

            if not numero_control:
                print(f"⚠️  {archivo.name}: No tiene numeroControl")
                continue

            archivos_datos[archivo.name] = datos
            archivos_por_numero_control[numero_control].append(archivo.name)

        except json.JSONDecodeError as e:
            print(f"❌ {archivo.name}: Error al leer JSON - {e}")
            errores += 1
        except Exception as e:
            print(f"❌ {archivo.name}: Error inesperado - {e}")
            errores += 1

    print(f"✓ {len(archivos_datos)} archivos procesados correctamente")
    if errores > 0:
        print(f"❌ {errores} archivos con errores")
    print("-" * 80)

    # Segunda pasada: comparar archivos con mismo numeroControl
    print("\n🔍 Buscando duplicados...")

    for numero_control, lista_archivos in archivos_por_numero_control.items():
        if len(lista_archivos) > 1:
            print(f"\n📋 numeroControl: {numero_control}")
            print(f"   Encontrados {len(lista_archivos)} archivos:")

            # Comparar todos los pares de archivos
            for i in range(len(lista_archivos)):
                for j in range(i + 1, len(lista_archivos)):
                    archivo1 = lista_archivos[i]
                    archivo2 = lista_archivos[j]

                    datos1 = archivos_datos[archivo1]
                    datos2 = archivos_datos[archivo2]

                    if son_archivos_identicos(datos1, datos2):
                        # Duplicados completos
                        print(f"   ✓ DUPLICADO COMPLETO: {archivo1} ≈ {archivo2}")
                        duplicados_completos.append(
                            {
                                "numeroControl": numero_control,
                                "archivo1": archivo1,
                                "archivo2": archivo2,
                                "tipo": "duplicado_completo",
                            }
                        )
                    else:
                        # Mismo numeroControl pero contenido diferente
                        print(f"   ⚠️  SIN CORRELACIÓN: {archivo1} ≠ {archivo2}")
                        sin_correlacion.append(
                            {
                                "numeroControl": numero_control,
                                "archivo1": archivo1,
                                "archivo2": archivo2,
                                "tipo": "sin_correlacion",
                                "diferencias": encontrar_diferencias(datos1, datos2),
                            }
                        )

    # Generar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Guardar duplicados completos
    if duplicados_completos:
        archivo_duplicados = f"duplicados_{timestamp}.json"
        with open(archivo_duplicados, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_analisis": datetime.now().isoformat(),
                    "total_duplicados": len(duplicados_completos),
                    "duplicados": duplicados_completos,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\n✅ Se encontraron {len(duplicados_completos)} duplicados completos")
        print(f"   Guardados en: {archivo_duplicados}")
    else:
        print(f"\n✓ No se encontraron duplicados completos")

    # Guardar archivos sin correlación
    if sin_correlacion:
        archivo_sin_correlacion = f"sin_correlacion_{timestamp}.json"
        with open(archivo_sin_correlacion, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_analisis": datetime.now().isoformat(),
                    "total_sin_correlacion": len(sin_correlacion),
                    "sin_correlacion": sin_correlacion,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\n⚠️  Se encontraron {len(sin_correlacion)} archivos sin correlación")
        print(f"   Guardados en: {archivo_sin_correlacion}")
    else:
        print(f"\n✓ No se encontraron archivos sin correlación")

    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DEL ANÁLISIS")
    print("=" * 80)
    print(f"Total de archivos analizados: {len(archivos_datos)}")
    print(f"Archivos con errores: {errores}")
    print(f"Números de control únicos: {len(archivos_por_numero_control)}")
    print(
        f"Números de control duplicados: {sum(1 for lista in archivos_por_numero_control.values() if len(lista) > 1)}"
    )
    print(f"Duplicados completos encontrados: {len(duplicados_completos)}")
    print(f"Archivos sin correlación: {len(sin_correlacion)}")
    print("=" * 80)


def encontrar_diferencias(datos1, datos2):
    """
    Encuentra las diferencias principales entre dos archivos JSON
    """
    diferencias = []

    # Comparar campos principales
    campos_a_comparar = [
        ("identificacion", "codigoGeneracion"),
        ("identificacion", "fecEmi"),
        ("identificacion", "horEmi"),
        ("resumen", "totalPagar"),
        ("resumen", "montoTotalOperacion"),
        ("emisor", "nombre"),
        ("receptor", "nombre"),
    ]

    for campo_path in campos_a_comparar:
        if len(campo_path) == 2:
            seccion, campo = campo_path
            valor1 = datos1.get(seccion, {}).get(campo)
            valor2 = datos2.get(seccion, {}).get(campo)

            if valor1 != valor2:
                diferencias.append(
                    {
                        "campo": f"{seccion}.{campo}",
                        "valor_archivo1": valor1,
                        "valor_archivo2": valor2,
                    }
                )

    # Comparar número de items
    items1 = len(datos1.get("cuerpoDocumento", []))
    items2 = len(datos2.get("cuerpoDocumento", []))

    if items1 != items2:
        diferencias.append(
            {
                "campo": "cuerpoDocumento.cantidad",
                "valor_archivo1": items1,
                "valor_archivo2": items2,
            }
        )

    return diferencias[:10]  # Limitar a 10 diferencias principales


def normalizar_nombre_pdf(nombre):
    """
    Normaliza el nombre de un archivo PDF para comparación,
    removiendo el sufijo (1), (2), etc.
    """
    # Remover la extensión .pdf
    nombre_sin_ext = nombre.replace(".pdf", "")

    # Buscar patrones como (1), (2), etc. al final
    # Patrón: espacio opcional + paréntesis + número + paréntesis al final
    patron = r"\s*\(\d+\)$"
    nombre_normalizado = re.sub(patron, "", nombre_sin_ext)

    return nombre_normalizado


def detector_duplicados_pdf():
    """
    Detecta archivos PDF duplicados basándose en sus nombres
    """
    print("\n" + "=" * 80)
    print("SELECCIÓN DE CARPETA PARA DETECTAR DUPLICADOS EN PDF")
    print("=" * 80)

    # Solicitar carpeta al usuario
    print("\nIngrese la ruta de la carpeta con los archivos PDF")
    print("(Presione Enter para usar 'descargas_erp' por defecto)")
    carpeta_input = input("\nRuta de la carpeta: ").strip()

    if not carpeta_input:
        carpeta_descargas = Path("descargas_erp")
    else:
        # Remover comillas si las tiene
        carpeta_input = carpeta_input.strip('"').strip("'")
        carpeta_descargas = Path(carpeta_input)

    # Verificar que la carpeta existe
    if not carpeta_descargas.exists():
        print(f"\n❌ Error: La carpeta {carpeta_descargas} no existe")
        return

    # Diccionario para agrupar archivos por nombre normalizado
    archivos_por_nombre = defaultdict(list)

    # Obtener todos los archivos PDF
    archivos_pdf = list(carpeta_descargas.glob("*.pdf"))
    total_archivos = len(archivos_pdf)

    print(f"\n🔍 Analizando {total_archivos} archivos PDF...")
    print("-" * 80)

    # Agrupar archivos por nombre normalizado
    for archivo in archivos_pdf:
        nombre_original = archivo.name
        nombre_normalizado = normalizar_nombre_pdf(nombre_original)

        archivos_por_nombre[nombre_normalizado].append(nombre_original)

    # Encontrar duplicados
    duplicados_pdf = []
    archivos_con_numero = []  # Archivos que tienen (1), (2), etc.

    print("\n🔍 Buscando duplicados...")
    print("-" * 80)

    for nombre_normalizado, lista_archivos in archivos_por_nombre.items():
        if len(lista_archivos) > 1:
            print(f"\n📋 Nombre base: {nombre_normalizado}")
            print(f"   Encontrados {len(lista_archivos)} archivos:")

            # Separar archivos: sin numeración vs con numeración
            archivos_sin_numero = []
            archivos_numerados = []

            for archivo in lista_archivos:
                print(f"   - {archivo}")

                # Verificar si tiene numeración (1), (2), etc.
                if re.search(r"\s*\(\d+\)\.pdf$", archivo):
                    archivos_numerados.append(archivo)
                    archivos_con_numero.append(
                        {
                            "nombre_original": archivo,
                            "nombre_base": nombre_normalizado,
                            "tipo": "archivo_numerado",
                        }
                    )
                else:
                    archivos_sin_numero.append(archivo)

            # Determinar el archivo original
            # Prioridad: archivo sin numeración > archivo con menor numeración
            if archivos_sin_numero:
                # Si hay archivos sin numeración, el primero (alfabéticamente) es el original
                archivo_original = sorted(archivos_sin_numero)[0]
            else:
                # Si todos tienen numeración, el primero alfabéticamente es el original
                archivo_original = sorted(archivos_numerados)[0]

            # Crear registros de duplicados
            # Todos los archivos numerados son duplicados
            for archivo_numerado in archivos_numerados:
                # Si el archivo numerado es el "original", no lo marcamos como duplicado
                if archivo_numerado != archivo_original:
                    duplicados_pdf.append(
                        {
                            "nombre_base": nombre_normalizado,
                            "archivo_original": archivo_original,
                            "archivo_duplicado": archivo_numerado,
                            "tipo": "duplicado_pdf",
                        }
                    )

            # Si hay más de un archivo sin numeración, también son duplicados
            archivos_sin_numero_ordenados = sorted(archivos_sin_numero)
            for i in range(1, len(archivos_sin_numero_ordenados)):
                duplicados_pdf.append(
                    {
                        "nombre_base": nombre_normalizado,
                        "archivo_original": archivo_original,
                        "archivo_duplicado": archivos_sin_numero_ordenados[i],
                        "tipo": "duplicado_pdf",
                    }
                )

    # Generar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Guardar duplicados PDF
    if duplicados_pdf:
        archivo_duplicados_pdf = f"duplicados_pdf_{timestamp}.json"
        with open(archivo_duplicados_pdf, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fecha_analisis": datetime.now().isoformat(),
                    "carpeta_analizada": str(carpeta_descargas),
                    "total_duplicados": len(duplicados_pdf),
                    "total_archivos_con_numero": len(archivos_con_numero),
                    "duplicados": duplicados_pdf,
                    "archivos_con_numero": archivos_con_numero,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\n✅ Se encontraron {len(duplicados_pdf)} archivos PDF duplicados")
        print(f"   Guardados en: {archivo_duplicados_pdf}")

        if archivos_con_numero:
            print(
                f"\n⚠️  Se encontraron {len(archivos_con_numero)} archivos con numeración (1), (2), etc."
            )
            print(f"   Estos archivos están incluidos en el reporte JSON")
    else:
        print(f"\n✓ No se encontraron archivos PDF duplicados")

    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DEL ANÁLISIS DE PDF")
    print("=" * 80)
    print(f"Carpeta analizada: {carpeta_descargas}")
    print(f"Total de archivos PDF: {total_archivos}")
    print(f"Nombres únicos (normalizados): {len(archivos_por_nombre)}")
    print(f"Archivos duplicados encontrados: {len(duplicados_pdf)}")
    print(f"Archivos con numeración (1), (2), etc.: {len(archivos_con_numero)}")
    print("=" * 80)


def main():
    """
    Función principal que gestiona el menú y las opciones
    """
    while True:
        opcion = mostrar_menu()

        if opcion == "1":
            # Detectar duplicados en JSON
            print("\n" + "=" * 80)
            print("DETECTOR DE DUPLICADOS EN JSON")
            print("=" * 80)
            print()
            detector_duplicados()
            print("\n✅ Análisis completado")

        elif opcion == "2":
            # Detectar duplicados en PDF
            print("\n" + "=" * 80)
            print("DETECTOR DE DUPLICADOS EN PDF")
            print("=" * 80)
            print()
            detector_duplicados_pdf()
            print("\n✅ Análisis completado")

        elif opcion == "3":
            # Eliminar duplicados
            eliminar_duplicados()

        elif opcion == "4":
            # Salir
            print("\n👋 ¡Hasta luego!")
            break

        # Pausa antes de volver al menú
        input("\nPresione Enter para continuar...")


if __name__ == "__main__":
    main()
