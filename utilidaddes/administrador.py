import sys
import io

# Configurar codificación UTF-8 para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import shutil
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Nombres de carpetas origen a buscar
CARPETAS_ORIGEN_NOMBRES = [
    "descargas_diarias",
    "descargas_gastos",
    "descargas_remisiones",
]

# Nombres de carpetas destino requeridas (para clasificación)
CARPETAS_DESTINO_NOMBRES = [
    "notas_de_credito",
    "SA",
    "SS",
    "SM",
    "descargas_remisiones",
    "descargas_gastos",
]

# Carpetas que NO se clasifican (se copian/mueven directamente)
CARPETAS_SIN_CLASIFICAR = ["descargas_remisiones", "descargas_gastos"]

# Variables globales que se configurarán en tiempo de ejecución
CARPETAS_ORIGEN = []
CARPETAS_DESTINO = {}

# Reglas de prefijos (solo los primeros 4 caracteres importan: M001, S001, etc.)
REGLAS_PREFIJOS = {
    "M001": "SA",  # M001 -> Santa Ana
    "S001": "SS",  # S001 -> San Salvador
    "S002": "SM",  # S002 -> San Miguel
    "M002": "SM",  # M002 -> San Miguel
    "M003": "SS",  # M003 -> San Salvador
}

# Patrón especial para notas de crédito (DTE-05 con M001)
PATRON_NOTA_CREDITO = r"DTE-05-M001"


def extraer_prefijo_completo(nombre_archivo):
    """
    Extrae el prefijo completo del nombre del archivo.
    Ejemplo:
    - DTE-01-M0030001-000000000000029.pdf -> M0030001
    - DTE-01-M001P001-000000000000001.pdf -> M001P001
    """
    # Patrón flexible: DTE-XX- seguido de cualquier combinación de caracteres hasta el siguiente guión
    # Captura desde M o S hasta el próximo guión (-)
    patron = r"DTE-\d{2}-([MS][^-]+)-"
    match = re.search(patron, nombre_archivo)

    if match:
        return match.group(1)

    return None


def extraer_prefijo_sucursal(prefijo_completo):
    """
    Extrae solo los primeros 4 caracteres del prefijo (la parte de la sucursal).
    Ejemplo: M0030001 -> M003
    """
    if prefijo_completo and len(prefijo_completo) >= 4:
        return prefijo_completo[:4]

    return None


def es_nota_credito(nombre_archivo):
    """
    Verifica si el archivo es una nota de crédito (DTE-05 con M001)
    """
    return re.search(PATRON_NOTA_CREDITO, nombre_archivo) is not None


def obtener_carpeta_destino(nombre_archivo, prefijo_completo):
    """
    Determina la carpeta de destino según el prefijo
    """
    # Verificar si es nota de crédito
    if es_nota_credito(nombre_archivo):
        return "notas_credito"

    # Extraer solo la parte de la sucursal (primeros 4 caracteres)
    prefijo_sucursal = extraer_prefijo_sucursal(prefijo_completo)

    if not prefijo_sucursal:
        return None

    # Buscar el prefijo de sucursal en las reglas
    if prefijo_sucursal in REGLAS_PREFIJOS:
        return REGLAS_PREFIJOS[prefijo_sucursal]

    return None


def configurar_carpetas():
    """
    Solicita al usuario las rutas de carpetas origen y destino
    """
    global CARPETAS_ORIGEN, CARPETAS_DESTINO

    print("\n" + "=" * 80)
    print("CONFIGURACIÓN DE RUTAS")
    print("=" * 80)

    # Solicitar carpeta padre de origen
    while True:
        print("\n📂 CARPETA DE ORIGEN (Padre)")
        print("   Esta carpeta debe contener las subcarpetas:")
        for nombre in CARPETAS_ORIGEN_NOMBRES:
            print(f"   - {nombre}")

        ruta_origen_padre = input(
            "\nIngrese la ruta de la carpeta padre de origen: "
        ).strip()
        ruta_origen_padre = Path(ruta_origen_padre)

        if not ruta_origen_padre.exists():
            print(f"❌ Error: La ruta '{ruta_origen_padre}' no existe.")
            print("   Por favor, ingrese una ruta válida.")
            continue

        if not ruta_origen_padre.is_dir():
            print(f"❌ Error: '{ruta_origen_padre}' no es un directorio.")
            continue

        # Verificar que existan las carpetas de origen
        carpetas_encontradas = []
        carpetas_faltantes = []

        for nombre in CARPETAS_ORIGEN_NOMBRES:
            carpeta = ruta_origen_padre / nombre
            if carpeta.exists() and carpeta.is_dir():
                carpetas_encontradas.append(carpeta)
                print(f"   ✓ Encontrada: {nombre}")
            else:
                carpetas_faltantes.append(nombre)
                print(f"   ✗ No encontrada: {nombre}")

        if carpetas_faltantes:
            print(f"\n⚠️  Advertencia: Faltan {len(carpetas_faltantes)} carpeta(s):")
            for nombre in carpetas_faltantes:
                print(f"   - {nombre}")

            continuar = (
                input("\n¿Desea continuar de todas formas? (S/N): ").strip().upper()
            )
            if continuar != "S":
                continue

        CARPETAS_ORIGEN = carpetas_encontradas
        print(f"\n✓ Carpetas de origen configuradas: {len(CARPETAS_ORIGEN)}")
        break

    # Solicitar carpeta de destino
    while True:
        print("\n📂 CARPETA DE DESTINO")
        print("   Esta carpeta debe contener (o se crearán) las subcarpetas:")
        for nombre in CARPETAS_DESTINO_NOMBRES:
            print(f"   - {nombre}")

        ruta_destino = input("\nIngrese la ruta de la carpeta de destino: ").strip()
        ruta_destino = Path(ruta_destino)

        if not ruta_destino.exists():
            print(f"⚠️  La ruta '{ruta_destino}' no existe.")
            crear = input("¿Desea crearla? (S/N): ").strip().upper()
            if crear == "S":
                try:
                    ruta_destino.mkdir(parents=True, exist_ok=True)
                    print(f"✓ Carpeta creada: {ruta_destino}")
                except Exception as e:
                    print(f"❌ Error al crear carpeta: {e}")
                    continue
            else:
                continue

        if not ruta_destino.is_dir():
            print(f"❌ Error: '{ruta_destino}' no es un directorio.")
            continue

        # Verificar estructura de carpetas destino
        carpetas_destino_encontradas = []
        carpetas_destino_faltantes = []

        for nombre in CARPETAS_DESTINO_NOMBRES:
            carpeta = ruta_destino / nombre
            if carpeta.exists() and carpeta.is_dir():
                carpetas_destino_encontradas.append(nombre)
                print(f"   ✓ Encontrada: {nombre}")
            else:
                carpetas_destino_faltantes.append(nombre)
                print(f"   ✗ No encontrada: {nombre}")

        if carpetas_destino_faltantes:
            print(f"\n⚠️  Faltan carpetas de destino, se creará una nueva estructura")
            print(f"   Carpetas a crear: {len(carpetas_destino_faltantes)}")

            # Crear las carpetas faltantes
            try:
                for nombre in carpetas_destino_faltantes:
                    carpeta = ruta_destino / nombre
                    carpeta.mkdir(parents=True, exist_ok=True)
                    print(f"   ✓ Creada: {nombre}")
                print("\n✓ Estructura de carpetas creada correctamente")
            except Exception as e:
                print(f"❌ Error al crear estructura: {e}")
                continue
        else:
            print("\n✓ Estructura de carpetas de destino encontrada")

        # Configurar diccionario de carpetas destino
        CARPETAS_DESTINO = {
            "SS": ruta_destino / "SS",
            "SA": ruta_destino / "SA",
            "SM": ruta_destino / "SM",
            "notas_credito": ruta_destino / "notas_de_credito",
            "descargas_remisiones": ruta_destino / "descargas_remisiones",
            "descargas_gastos": ruta_destino / "descargas_gastos",
        }

        print(f"\n✓ Carpetas de destino configuradas")
        break

    print("\n" + "=" * 80)
    print("✓ CONFIGURACIÓN COMPLETADA")
    print("=" * 80)
    print(f"📂 Carpetas origen: {len(CARPETAS_ORIGEN)}")
    print(f"📂 Carpeta destino: {ruta_destino}")
    print("=" * 80)


def mostrar_menu():
    """
    Muestra el menú principal
    """
    print("\n" + "=" * 80)
    print("ADMINISTRADOR DE FACTURAS - HERMACO")
    print("=" * 80)
    print("\nSeleccione una opción:")
    print("  1. Distribuir archivos (mover)")
    print("  2. Distribuir archivos (copiar)")
    print("  3. Generar reporte sin mover archivos")
    print("  4. Reconfigurar rutas")
    print("  5. Salir")
    print("-" * 80)

    while True:
        opcion = input("\nIngrese el número de opción (1-5): ").strip()
        if opcion in ["1", "2", "3", "4", "5"]:
            return opcion
        else:
            print("⚠️  Opción inválida. Por favor ingrese 1, 2, 3, 4 o 5.")


def distribuir_archivos(modo="mover"):
    """
    Distribuye los archivos PDF y JSON según sus prefijos
    modo: 'mover' o 'copiar'
    """
    print("\n" + "=" * 80)
    print(f"DISTRIBUCIÓN DE ARCHIVOS - MODO: {modo.upper()}")
    print("=" * 80)

    # Verificar que hay carpetas configuradas
    if not CARPETAS_ORIGEN:
        print(f"\n❌ Error: No hay carpetas de origen configuradas")
        print("   Use la opción 4 para configurar las rutas")
        return

    if not CARPETAS_DESTINO:
        print(f"\n❌ Error: No hay carpetas de destino configuradas")
        print("   Use la opción 4 para configurar las rutas")
        return

    # Crear carpetas de destino si no existen
    for carpeta in CARPETAS_DESTINO.values():
        carpeta.mkdir(parents=True, exist_ok=True)

    # Recolectar archivos por tipo (clasificables y sin clasificar)
    archivos_para_clasificar = []  # De descargas_diarias
    archivos_sin_clasificar_por_carpeta = {}  # De remisiones y gastos

    print(f"\n🔍 Buscando archivos en {len(CARPETAS_ORIGEN)} carpeta(s)...")
    print("-" * 80)

    for carpeta_origen in CARPETAS_ORIGEN:
        print(f"\n📂 Procesando: {carpeta_origen.name}")

        # Obtener todos los archivos PDF y JSON
        archivos_pdf = list(carpeta_origen.glob("*.pdf"))
        archivos_json = list(carpeta_origen.glob("*.json"))

        # Filtrar archivos JSON que no sean de reporte
        archivos_json_validos = [
            f
            for f in archivos_json
            if not (
                "registros_fallidos" in f.name
                or "ultimo_" in f.name
                or "duplicados" in f.name
                or "sin_correlacion" in f.name
                or "01descargados" in f.name
                or "02ignorados" in f.name
            )
        ]

        carpeta_archivos = archivos_pdf + archivos_json_validos

        print(f"   📄 PDFs encontrados: {len(archivos_pdf)}")
        print(f"   📄 JSONs encontrados: {len(archivos_json_validos)}")
        print(f"   📊 Total: {len(carpeta_archivos)}")

        # Determinar si esta carpeta requiere clasificación o copia directa
        if carpeta_origen.name in CARPETAS_SIN_CLASIFICAR:
            # Carpetas sin clasificar: copiar/mover directamente
            archivos_sin_clasificar_por_carpeta[carpeta_origen.name] = carpeta_archivos
            print(f"   ℹ️  Modo: Copia directa (sin clasificación)")
        else:
            # Carpetas que requieren clasificación
            archivos_para_clasificar.extend(carpeta_archivos)
            print(f"   ℹ️  Modo: Clasificación por prefijo")

    total_archivos_clasificables = len(archivos_para_clasificar)
    total_archivos_directos = sum(
        len(archivos) for archivos in archivos_sin_clasificar_por_carpeta.values()
    )
    total_archivos = total_archivos_clasificables + total_archivos_directos

    print("\n" + "=" * 80)
    print(f"📊 RESUMEN DE ARCHIVOS ENCONTRADOS")
    print("=" * 80)
    print(f"Total de archivos a procesar: {total_archivos}")
    print(f"  • Archivos para clasificar: {total_archivos_clasificables}")
    print(f"  • Archivos para copia directa: {total_archivos_directos}")
    if archivos_sin_clasificar_por_carpeta:
        for carpeta_nombre, archivos in archivos_sin_clasificar_por_carpeta.items():
            print(f"    - {carpeta_nombre}: {len(archivos)}")
    print("-" * 80)

    if total_archivos == 0:
        print("\n⚠️  No hay archivos para distribuir")
        return

    # Confirmar antes de procesar
    if modo != "reporte":
        confirmacion = (
            input(f"\n¿Desea proceder con la {modo}? (S/N): ").strip().upper()
        )

        if confirmacion != "S":
            print(f"\n❌ Operación cancelada por el usuario")
            return

    # Contadores y estadísticas
    estadisticas = {
        "SS": 0,
        "SA": 0,
        "SM": 0,
        "notas_credito": 0,
        "descargas_remisiones": 0,
        "descargas_gastos": 0,
        "sin_clasificar": 0,
        "errores": 0,
    }

    archivos_sin_clasificar = []
    prefijos_desconocidos = defaultdict(int)

    print(f"\n🔄 Procesando archivos...")
    print("-" * 80)

    # PARTE 1: Procesar archivos sin clasificar (copia directa)
    if archivos_sin_clasificar_por_carpeta:
        print(f"\n📦 PROCESANDO ARCHIVOS DE COPIA DIRECTA...")
        print("-" * 80)

        for carpeta_nombre, archivos in archivos_sin_clasificar_por_carpeta.items():
            carpeta_destino = CARPETAS_DESTINO[carpeta_nombre]
            print(f"\n📂 Carpeta: {carpeta_nombre} -> {carpeta_nombre}")
            print(f"   Archivos: {len(archivos)}")

            for archivo in archivos:
                nombre_archivo = archivo.name
                ruta_destino = carpeta_destino / nombre_archivo

                try:
                    if modo == "mover":
                        shutil.move(str(archivo), str(ruta_destino))
                        print(f"   ✓ Movido: {nombre_archivo}")
                    elif modo == "copiar":
                        shutil.copy2(str(archivo), str(ruta_destino))
                        print(f"   ✓ Copiado: {nombre_archivo}")
                    else:  # modo reporte
                        print(f"   📋 {nombre_archivo} -> {carpeta_nombre}")

                    estadisticas[carpeta_nombre] += 1

                except Exception as e:
                    print(f"   ❌ Error al procesar {nombre_archivo}: {e}")
                    estadisticas["errores"] += 1

    # PARTE 2: Procesar archivos que requieren clasificación
    if archivos_para_clasificar:
        print(f"\n🔍 PROCESANDO ARCHIVOS CON CLASIFICACIÓN...")
        print("-" * 80)

        for archivo in archivos_para_clasificar:
            nombre_archivo = archivo.name

            # Extraer prefijo completo
            prefijo_completo = extraer_prefijo_completo(nombre_archivo)

            if not prefijo_completo:
                # No se pudo extraer prefijo
                archivos_sin_clasificar.append(nombre_archivo)
                estadisticas["sin_clasificar"] += 1
                print(f"⚠️  Sin prefijo: {nombre_archivo}")
                continue

            # Extraer prefijo de sucursal (primeros 4 caracteres)
            prefijo_sucursal = extraer_prefijo_sucursal(prefijo_completo)

            # Obtener carpeta destino
            carpeta_destino_key = obtener_carpeta_destino(
                nombre_archivo, prefijo_completo
            )

            if carpeta_destino_key:
                carpeta_destino = CARPETAS_DESTINO[carpeta_destino_key]

                # Mover o copiar el archivo
                ruta_destino = carpeta_destino / nombre_archivo

                try:
                    if modo == "mover":
                        shutil.move(str(archivo), str(ruta_destino))
                        print(
                            f"✓ Movido: {nombre_archivo} -> {carpeta_destino_key} [{prefijo_sucursal}]"
                        )
                    elif modo == "copiar":
                        shutil.copy2(str(archivo), str(ruta_destino))
                        print(
                            f"✓ Copiado: {nombre_archivo} -> {carpeta_destino_key} [{prefijo_sucursal}]"
                        )
                    else:  # modo reporte
                        print(
                            f"📋 {nombre_archivo} -> {carpeta_destino_key} [{prefijo_sucursal}]"
                        )

                    estadisticas[carpeta_destino_key] += 1

                except Exception as e:
                    print(f"❌ Error al procesar {nombre_archivo}: {e}")
                    estadisticas["errores"] += 1

            else:
                # Prefijo no reconocido
                archivos_sin_clasificar.append(nombre_archivo)
                prefijos_desconocidos[
                    prefijo_sucursal if prefijo_sucursal else prefijo_completo
                ] += 1
                estadisticas["sin_clasificar"] += 1
                print(
                    f"⚠️  Prefijo no reconocido [{prefijo_sucursal}] (completo: {prefijo_completo}): {nombre_archivo}"
                )

    # Generar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_reporte = f"reporte_distribucion_{timestamp}.txt"

    # Obtener nombres de carpetas origen para el reporte
    nombres_carpetas_origen = [str(carpeta.name) for carpeta in CARPETAS_ORIGEN]
    carpetas_origen_str = ", ".join(nombres_carpetas_origen)

    with open(archivo_reporte, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE DISTRIBUCIÓN DE ARCHIVOS - HERMACO\n")
        f.write("=" * 80 + "\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Modo: {modo.upper()}\n")
        f.write(f"Carpetas origen: {carpetas_origen_str}\n")
        f.write(f"Carpeta destino: {list(CARPETAS_DESTINO.values())[0].parent}\n")
        f.write("-" * 80 + "\n\n")

        f.write("ESTADÍSTICAS:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total de archivos procesados: {total_archivos}\n")
        f.write("\nArchivos clasificados por sucursal:\n")
        f.write(f"  • San Salvador (SS): {estadisticas['SS']}\n")
        f.write(f"  • Santa Ana (SA): {estadisticas['SA']}\n")
        f.write(f"  • San Miguel (SM): {estadisticas['SM']}\n")
        f.write(f"  • Notas de crédito: {estadisticas['notas_credito']}\n")
        f.write("\nArchivos copiados sin clasificación:\n")
        f.write(f"  • Remisiones: {estadisticas['descargas_remisiones']}\n")
        f.write(f"  • Gastos: {estadisticas['descargas_gastos']}\n")
        f.write("\nOtros:\n")
        f.write(f"  • Sin clasificar: {estadisticas['sin_clasificar']}\n")
        f.write(f"  • Errores: {estadisticas['errores']}\n")
        f.write("\n")

        if prefijos_desconocidos:
            f.write("PREFIJOS NO RECONOCIDOS:\n")
            f.write("-" * 80 + "\n")
            for prefijo, cantidad in sorted(prefijos_desconocidos.items()):
                f.write(f"  • {prefijo}: {cantidad} archivo(s)\n")
            f.write("\n")

        if archivos_sin_clasificar:
            f.write("ARCHIVOS SIN CLASIFICAR:\n")
            f.write("-" * 80 + "\n")
            for archivo in archivos_sin_clasificar:
                f.write(f"  • {archivo}\n")
            f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("REGLAS DE CLASIFICACIÓN APLICADAS:\n")
        f.write("=" * 80 + "\n")
        f.write(
            "NOTA: Solo los primeros 4 caracteres del prefijo determinan la sucursal.\n"
        )
        f.write("      Los últimos 4 dígitos pueden variar.\n")
        f.write(
            "      Ejemplo: M0010001, M0010002, M0010123 -> Todos van a M001 (SA)\n"
        )
        f.write("\n")
        f.write("  • M001xxxx (M001) -> SA (Santa Ana)\n")
        f.write("  • S001xxxx (S001) -> SS (San Salvador)\n")
        f.write("  • S002xxxx (S002) -> SM (San Miguel)\n")
        f.write("  • M002xxxx (M002) -> SM (San Miguel)\n")
        f.write("  • M003xxxx (M003) -> SS (San Salvador)\n")
        f.write("  • DTE-05-M001xxxx -> Notas de crédito\n")
        f.write("=" * 80 + "\n")

    # Resumen en consola
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE DISTRIBUCIÓN")
    print("=" * 80)
    print(f"Total de archivos procesados: {total_archivos}")
    print("\nArchivos clasificados por sucursal:")
    print(f"  ✓ San Salvador (SS): {estadisticas['SS']}")
    print(f"  ✓ Santa Ana (SA): {estadisticas['SA']}")
    print(f"  ✓ San Miguel (SM): {estadisticas['SM']}")
    print(f"  ✓ Notas de crédito: {estadisticas['notas_credito']}")
    print("\nArchivos copiados sin clasificación:")
    print(f"  ✓ Remisiones: {estadisticas['descargas_remisiones']}")
    print(f"  ✓ Gastos: {estadisticas['descargas_gastos']}")
    print("\nOtros:")
    print(f"  ⚠️  Sin clasificar: {estadisticas['sin_clasificar']}")
    print(f"  ❌ Errores: {estadisticas['errores']}")

    if prefijos_desconocidos:
        print(f"\n⚠️  PREFIJOS NO RECONOCIDOS:")
        for prefijo, cantidad in sorted(prefijos_desconocidos.items()):
            print(f"     • {prefijo}: {cantidad} archivo(s)")

    print(f"\n📄 Reporte guardado en: {archivo_reporte}")
    print("=" * 80)


def main():
    """
    Función principal
    """
    print("\n🚀 Iniciando Administrador de Facturas HERMACO")

    # Configurar carpetas al inicio
    configurar_carpetas()

    while True:
        opcion = mostrar_menu()

        if opcion == "1":
            # Distribuir archivos (mover)
            distribuir_archivos(modo="mover")

        elif opcion == "2":
            # Distribuir archivos (copiar)
            distribuir_archivos(modo="copiar")

        elif opcion == "3":
            # Generar reporte sin mover
            distribuir_archivos(modo="reporte")

        elif opcion == "4":
            # Reconfigurar rutas
            configurar_carpetas()

        elif opcion == "5":
            # Salir
            print("\n👋 ¡Hasta luego!")
            break

        # Pausa antes de volver al menú
        input("\nPresione Enter para continuar...")


if __name__ == "__main__":
    main()
