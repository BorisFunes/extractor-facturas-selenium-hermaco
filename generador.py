import os
import json
from datetime import datetime
from pathlib import Path

# Ruta donde se encuentran los archivos JSON de facturas
RUTA_BACKUP = r"C:\zeta2\Henri\Copia de seguridad de facturas(No borrar)\Backup"

# Archivo de salida con la lista de clientes
ARCHIVO_CLIENTES = os.path.join(os.getcwd(), "lista_clientes.json")


def buscar_archivos_json(ruta):
    """
    Busca todos los archivos JSON en la ruta especificada
    """
    archivos_json = []
    try:
        ruta_path = Path(ruta)
        if not ruta_path.exists():
            print(f"❌ La ruta no existe: {ruta}")
            return []

        # Buscar todos los archivos .json recursivamente
        archivos_json = list(ruta_path.rglob("*.json"))
        print(f"📊 Total de archivos JSON encontrados: {len(archivos_json)}")
        return archivos_json

    except Exception as e:
        print(f"❌ Error al buscar archivos JSON: {e}")
        return []


def extraer_cliente_de_json(archivo_path):
    """
    Extrae el nombre del cliente (receptor) de un archivo JSON
    Retorna el nombre del cliente o None si no se encuentra
    """
    try:
        with open(archivo_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            # Buscar el campo receptor -> nombre
            if "receptor" in data and isinstance(data["receptor"], dict):
                nombre_cliente = data["receptor"].get("nombre")
                if nombre_cliente:
                    return nombre_cliente.strip()

    except json.JSONDecodeError:
        # Ignorar archivos JSON mal formados
        pass
    except Exception as e:
        # Ignorar otros errores silenciosamente
        pass

    return None


def generar_lista_clientes(ruta_backup):
    """
    Genera una lista única de clientes a partir de los archivos JSON
    """
    print("\n" + "=" * 60)
    print("🚀 INICIANDO GENERACIÓN DE LISTA DE CLIENTES")
    print("=" * 60)

    # Buscar todos los archivos JSON
    print(f"\n🔍 Buscando archivos JSON en: {ruta_backup}")
    archivos_json = buscar_archivos_json(ruta_backup)

    if not archivos_json:
        print("⚠️ No se encontraron archivos JSON para procesar")
        return

    # Set para almacenar clientes únicos
    clientes_unicos = set()
    archivos_procesados = 0
    archivos_con_cliente = 0

    print(f"\n📄 Procesando archivos...")

    for idx, archivo in enumerate(archivos_json, 1):
        archivos_procesados += 1

        # Mostrar progreso cada 100 archivos
        if archivos_procesados % 100 == 0:
            print(
                f"  ⏳ Procesados: {archivos_procesados}/{len(archivos_json)} archivos..."
            )

        # Extraer nombre del cliente
        nombre_cliente = extraer_cliente_de_json(archivo)

        if nombre_cliente:
            clientes_unicos.add(nombre_cliente)
            archivos_con_cliente += 1

    print(f"\n✅ Procesamiento completado")
    print(f"   📊 Total de archivos procesados: {archivos_procesados}")
    print(f"   👥 Archivos con información de cliente: {archivos_con_cliente}")
    print(f"   ✨ Clientes únicos encontrados: {len(clientes_unicos)}")

    # Convertir set a lista ordenada alfabéticamente
    lista_clientes_ordenada = sorted(list(clientes_unicos))

    # Generar estructura JSON para guardar
    datos_salida = {
        "fecha_generacion": datetime.now().isoformat(),
        "fecha_legible": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ruta_origen": ruta_backup,
        "total_clientes": len(lista_clientes_ordenada),
        "total_archivos_analizados": archivos_procesados,
        "clientes": lista_clientes_ordenada,
    }

    # Guardar en archivo JSON
    try:
        with open(ARCHIVO_CLIENTES, "w", encoding="utf-8") as f:
            json.dump(datos_salida, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Lista de clientes guardada en: {ARCHIVO_CLIENTES}")
        print(f"\n📋 PRIMEROS 10 CLIENTES (ejemplo):")
        for i, cliente in enumerate(lista_clientes_ordenada[:10], 1):
            print(f"   {i}. {cliente}")

        if len(lista_clientes_ordenada) > 10:
            print(f"   ... y {len(lista_clientes_ordenada) - 10} clientes más")

    except Exception as e:
        print(f"❌ Error al guardar archivo de clientes: {e}")


def mostrar_resumen_clientes():
    """
    Muestra un resumen del archivo de clientes si existe
    """
    try:
        if os.path.exists(ARCHIVO_CLIENTES):
            with open(ARCHIVO_CLIENTES, "r", encoding="utf-8") as f:
                datos = json.load(f)

                print("\n" + "=" * 60)
                print("📊 RESUMEN DE CLIENTES EXISTENTE")
                print("=" * 60)
                print(f"   📅 Fecha de generación: {datos.get('fecha_legible', 'N/A')}")
                print(f"   👥 Total de clientes: {datos.get('total_clientes', 0)}")
                print(
                    f"   📄 Archivos analizados: {datos.get('total_archivos_analizados', 0)}"
                )
                return True
        return False
    except:
        return False


if __name__ == "__main__":
    try:
        print("\n🔧 GENERADOR DE LISTA DE CLIENTES")
        print("=" * 60)

        # Verificar si ya existe un archivo de clientes
        if mostrar_resumen_clientes():
            print("\n⚠️ Ya existe un archivo de clientes generado previamente.")
            respuesta = input("¿Desea regenerar la lista? (s/n): ").strip().lower()
            if respuesta != "s":
                print("\n✅ Operación cancelada. Se mantiene el archivo existente.")
                exit(0)

        # Verificar que la ruta existe
        if not os.path.exists(RUTA_BACKUP):
            print(f"\n❌ ERROR: La ruta no existe: {RUTA_BACKUP}")
            print("   Por favor, verifica que la ruta sea correcta.")
            exit(1)

        # Generar lista de clientes
        generar_lista_clientes(RUTA_BACKUP)

        print("\n" + "=" * 60)
        print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️ Proceso interrumpido por el usuario")

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback

        traceback.print_exc()
