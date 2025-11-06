import json
import os
from pathlib import Path


def renombrar_archivos_json():
    """
    Renombra los archivos JSON en la carpeta descargas_erp
    usando el campo numeroControl con el prefijo 'hermaco-'
    """
    # Ruta de la carpeta con los archivos JSON
    carpeta_descargas = Path("descargas_erp")

    # Verificar que la carpeta existe
    if not carpeta_descargas.exists():
        print(f"Error: La carpeta {carpeta_descargas} no existe")
        return

    # Contadores para estadísticas
    renombrados = 0
    errores = 0
    omitidos = 0

    # Obtener todos los archivos JSON
    archivos_json = list(carpeta_descargas.glob("*.json"))
    total_archivos = len(archivos_json)

    print(f"Encontrados {total_archivos} archivos JSON en {carpeta_descargas}")
    print("-" * 60)

    for archivo in archivos_json:
        try:
            # Leer el contenido del archivo JSON
            with open(archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)

            # Extraer el numeroControl
            numero_control = datos.get("identificacion", {}).get("numeroControl")

            if not numero_control:
                print(f"⚠️  {archivo.name}: No se encontró el campo 'numeroControl'")
                omitidos += 1
                continue

            # Crear el nuevo nombre: hermaco- + numeroControl + .json
            nuevo_nombre = f"hermaco-{numero_control}.json"
            nueva_ruta = carpeta_descargas / nuevo_nombre

            # Verificar si el archivo ya tiene el nombre correcto
            if archivo.name == nuevo_nombre:
                print(f"✓ {archivo.name}: Ya tiene el nombre correcto")
                omitidos += 1
                continue

            # Verificar si ya existe un archivo con el nuevo nombre
            if nueva_ruta.exists():
                print(
                    f"⚠️  {archivo.name} -> {nuevo_nombre}: El archivo destino ya existe"
                )
                omitidos += 1
                continue

            # Renombrar el archivo
            archivo.rename(nueva_ruta)
            print(f"✓ Renombrado: {archivo.name} -> {nuevo_nombre}")
            renombrados += 1

        except json.JSONDecodeError as e:
            print(f"❌ {archivo.name}: Error al leer JSON - {e}")
            errores += 1
        except Exception as e:
            print(f"❌ {archivo.name}: Error inesperado - {e}")
            errores += 1

    # Mostrar resumen
    print("-" * 60)
    print(f"\n📊 RESUMEN:")
    print(f"   Total de archivos: {total_archivos}")
    print(f"   ✓ Renombrados: {renombrados}")
    print(f"   ⚠️  Omitidos: {omitidos}")
    print(f"   ❌ Errores: {errores}")


if __name__ == "__main__":
    print("=" * 60)
    print("RENOMBRADOR DE FACTURAS HERMACO")
    print("=" * 60)
    renombrar_archivos_json()
    print("\n✅ Proceso completado")
