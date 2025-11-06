import os
import shutil
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuración de carpetas
CARPETA_ORIGEN = Path("descargas_erp")
CARPETA_DESTINO_BASE = Path("facturas")

# Carpetas de destino
CARPETAS_DESTINO = {
    "SS": CARPETA_DESTINO_BASE / "SS",  # San Salvador
    "SA": CARPETA_DESTINO_BASE / "SA",  # Santa Ana
    "SM": CARPETA_DESTINO_BASE / "SM",  # San Miguel
    "notas_credito": CARPETA_DESTINO_BASE / "notas_de_credito",
}

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
    print("  4. Salir")
    print("-" * 80)

    while True:
        opcion = input("\nIngrese el número de opción (1-4): ").strip()
        if opcion in ["1", "2", "3", "4"]:
            return opcion
        else:
            print("⚠️  Opción inválida. Por favor ingrese 1, 2, 3 o 4.")


def distribuir_archivos(modo="mover"):
    """
    Distribuye los archivos PDF y JSON según sus prefijos
    modo: 'mover' o 'copiar'
    """
    print("\n" + "=" * 80)
    print(f"DISTRIBUCIÓN DE ARCHIVOS - MODO: {modo.upper()}")
    print("=" * 80)

    # Verificar que la carpeta origen existe
    if not CARPETA_ORIGEN.exists():
        print(f"\n❌ Error: La carpeta {CARPETA_ORIGEN} no existe")
        return

    # Crear carpetas de destino si no existen
    for carpeta in CARPETAS_DESTINO.values():
        carpeta.mkdir(parents=True, exist_ok=True)

    # Obtener todos los archivos PDF y JSON
    archivos_pdf = list(CARPETA_ORIGEN.glob("*.pdf"))
    archivos_json = list(CARPETA_ORIGEN.glob("*.json"))

    # Filtrar archivos JSON que no sean de reporte
    archivos_json_validos = [
        f
        for f in archivos_json
        if not (
            "registros_fallidos" in f.name
            or "ultimo_" in f.name
            or "duplicados" in f.name
            or "sin_correlacion" in f.name
        )
    ]

    todos_archivos = archivos_pdf + archivos_json_validos
    total_archivos = len(todos_archivos)

    print(f"\n📊 Total de archivos encontrados: {total_archivos}")
    print(f"   📄 PDFs: {len(archivos_pdf)}")
    print(f"   📄 JSONs: {len(archivos_json_validos)}")
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
        "sin_clasificar": 0,
        "errores": 0,
    }

    archivos_sin_clasificar = []
    prefijos_desconocidos = defaultdict(int)

    print(f"\n🔄 Procesando archivos...")
    print("-" * 80)

    # Procesar cada archivo
    for archivo in todos_archivos:
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
        carpeta_destino_key = obtener_carpeta_destino(nombre_archivo, prefijo_completo)

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

    with open(archivo_reporte, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE DISTRIBUCIÓN DE ARCHIVOS - HERMACO\n")
        f.write("=" * 80 + "\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Modo: {modo.upper()}\n")
        f.write(f"Carpeta origen: {CARPETA_ORIGEN}\n")
        f.write("-" * 80 + "\n\n")

        f.write("ESTADÍSTICAS:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total de archivos procesados: {total_archivos}\n")
        f.write(f"  • San Salvador (SS): {estadisticas['SS']}\n")
        f.write(f"  • Santa Ana (SA): {estadisticas['SA']}\n")
        f.write(f"  • San Miguel (SM): {estadisticas['SM']}\n")
        f.write(f"  • Notas de crédito: {estadisticas['notas_credito']}\n")
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
    print(f"  ✓ San Salvador (SS): {estadisticas['SS']}")
    print(f"  ✓ Santa Ana (SA): {estadisticas['SA']}")
    print(f"  ✓ San Miguel (SM): {estadisticas['SM']}")
    print(f"  ✓ Notas de crédito: {estadisticas['notas_credito']}")
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
            # Salir
            print("\n👋 ¡Hasta luego!")
            break

        # Pausa antes de volver al menú
        input("\nPresione Enter para continuar...")


if __name__ == "__main__":
    main()
