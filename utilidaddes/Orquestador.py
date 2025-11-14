"""
ORQUESTADOR DE DESCARGAS - HERMACO ERP
========================================
Este script ejecuta en secuencia los descargadores de:
1. Facturas de ayer (descargador_diario_copy.py)
2. Remisiones (descargadorderemisiones.py)
3. Gastos (descargadordegastos.py)

Modo: Headless (sin interfaz gráfica)
Uso: python Orquestador.py
"""

import subprocess
import sys
import os
import json
import glob
from datetime import datetime
import traceback

# Configurar codificación UTF-8 para Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class OrquestadorDescargas:
    def __init__(self):
        self.directorio_base = os.path.dirname(os.path.abspath(__file__))
        # Ruta base de descargas en el Desktop del usuario H01ventas05
        self.ruta_base_descargas = (
            r"C:\Users\H01ventas05\Desktop\extractor-facturas-selenium-hermaco-main"
        )
        self.fecha_inicio = datetime.now()
        self.scripts = [
            {
                "nombre": "Descargador de Facturas de Ayer",
                "archivo": "descargador_diario_copy.py",
                "descripcion": "Descarga facturas del día anterior",
                "carpeta_descargas": "descargas_diarias",
                "filtro": "Ayer (facturas del día anterior)",
            },
            {
                "nombre": "Descargador de Remisiones",
                "archivo": "descargadorderemisiones.py",
                "descripcion": "Descarga notas de remisión del ejercicio actual",
                "carpeta_descargas": "descargas_remisiones",
                "filtro": "Ejercicio actual - Todas las remisiones nuevas",
            },
            {
                "nombre": "Descargador de Gastos",
                "archivo": "descargadordegastos.py",
                "descripcion": "Descarga todos los gastos con estado 'Pagado'",
                "carpeta_descargas": "descargas_gastos",
                "filtro": "Estado: Pagado - Tipo: Gastos (DTE-14)",
            },
        ]
        self.resultados = []

    def imprimir_banner(self):
        """Imprime el banner inicial"""
        print("\n" + "=" * 70)
        print(" " * 15 + "ORQUESTADOR DE DESCARGAS - HERMACO ERP")
        print("=" * 70)
        print(
            f"📅 Fecha y hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"📂 Directorio de trabajo: {self.directorio_base}")
        print(f"🔧 Modo: Headless (sin interfaz gráfica)")
        print(f"📋 Scripts a ejecutar: {len(self.scripts)}")
        print("=" * 70 + "\n")

    def imprimir_resumen_final(self):
        """Imprime el resumen final de la ejecución"""
        print("\n" + "=" * 70)
        print(" " * 20 + "RESUMEN FINAL DE EJECUCIÓN")
        print("=" * 70)

        exitosos = sum(1 for r in self.resultados if r["exitoso"])
        fallidos = len(self.resultados) - exitosos

        for i, resultado in enumerate(self.resultados):
            script_info = self.scripts[i]
            estado = "✅ EXITOSO" if resultado["exitoso"] else "❌ FALLIDO"
            duracion = resultado["duracion"]

            print(f"\n{estado} - {resultado['nombre']}")
            print(f"   📝 Descripción: {script_info['descripcion']}")
            print(f"   🔍 Filtro usado: {script_info.get('filtro', 'N/A')}")
            print(f"   ⏱️  Duración: {duracion:.2f} segundos")

            # Mostrar archivos descargados
            carpeta_descargas = script_info.get("carpeta_descargas", "")
            if carpeta_descargas and resultado["exitoso"]:
                conteo = self.contar_archivos_descargados(carpeta_descargas)
                print(f"   📁 Archivos descargados:")
                print(f"      • PDFs: {conteo['pdfs']}")
                print(f"      • JSONs: {conteo['jsons']}")
                print(f"      • Total: {conteo['total']}")

            if not resultado["exitoso"]:
                print(f"   ⚠️  Error: {resultado['error']}")

        print("\n" + "-" * 70)
        print(f"📊 Total de scripts ejecutados: {len(self.resultados)}")
        print(f"✅ Exitosos: {exitosos}")
        print(f"❌ Fallidos: {fallidos}")

        # Calcular total de archivos descargados
        total_pdfs = 0
        total_jsons = 0
        for i, resultado in enumerate(self.resultados):
            if resultado["exitoso"]:
                script_info = self.scripts[i]
                carpeta_descargas = script_info.get("carpeta_descargas", "")
                if carpeta_descargas:
                    conteo = self.contar_archivos_descargados(carpeta_descargas)
                    total_pdfs += conteo["pdfs"]
                    total_jsons += conteo["jsons"]

        print(f"\n� Total de archivos descargados:")
        print(f"   • PDFs: {total_pdfs}")
        print(f"   • JSONs: {total_jsons}")
        print(f"   • Total: {total_pdfs + total_jsons}")

        print(
            f"\n�📅 Fecha y hora de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        duracion_total = (datetime.now() - self.fecha_inicio).total_seconds()
        print(f"⏱️  Duración total: {duracion_total:.2f}s ({duracion_total/60:.2f}m)")
        print("=" * 70 + "\n")

    def contar_archivos_descargados(self, carpeta):
        """
        Cuenta los archivos PDF y JSON en una carpeta de descargas

        Args:
            carpeta: Nombre de la carpeta de descargas

        Returns:
            dict: Diccionario con conteo de PDFs y JSONs
        """
        # Usar la ruta base de descargas configurada
        carpeta_path = os.path.join(self.ruta_base_descargas, carpeta)

        if not os.path.exists(carpeta_path):
            return {"pdfs": 0, "jsons": 0, "total": 0}

        # Contar PDFs
        pdfs = len(glob.glob(os.path.join(carpeta_path, "*.pdf")))

        # Contar JSONs (excluir archivos de tracking)
        todos_jsons = glob.glob(os.path.join(carpeta_path, "*.json"))
        archivos_tracking = [
            "ultimo_exitoso.json",
            "01descargados.json",
            "02ignorados.json",
            "ultimo_dte_exitoso",
            "reporte_fallidos",
        ]

        jsons = len(
            [
                f
                for f in todos_jsons
                if not any(
                    tracking in os.path.basename(f) for tracking in archivos_tracking
                )
            ]
        )

        return {"pdfs": pdfs, "jsons": jsons, "total": pdfs + jsons}

    def generar_reporte_json(self):
        """
        Genera un archivo JSON con el reporte detallado de la ejecución
        """
        try:
            timestamp = self.fecha_inicio.strftime("%Y%m%d_%H%M%S")
            archivo_reporte = os.path.join(
                self.directorio_base, f"reporte_ejecucion_{timestamp}.json"
            )

            fecha_fin = datetime.now()
            duracion_total = (fecha_fin - self.fecha_inicio).total_seconds()

            # Calcular totales de archivos descargados
            total_pdfs = 0
            total_jsons = 0
            for i, resultado in enumerate(self.resultados):
                if resultado["exitoso"]:
                    script_info = self.scripts[i]
                    carpeta_descargas = script_info.get("carpeta_descargas", "")
                    if carpeta_descargas:
                        conteo = self.contar_archivos_descargados(carpeta_descargas)
                        total_pdfs += conteo["pdfs"]
                        total_jsons += conteo["jsons"]

            # Construir el reporte
            reporte = {
                "fecha_inicio": self.fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat(),
                "duracion_total_segundos": duracion_total,
                "duracion_total_formateada": f"{duracion_total:.2f}s ({duracion_total/60:.2f}m)",
                "resumen": {
                    "total_scripts": len(self.resultados),
                    "exitosos": sum(1 for r in self.resultados if r["exitoso"]),
                    "fallidos": sum(1 for r in self.resultados if not r["exitoso"]),
                    "tasa_exito": f"{(sum(1 for r in self.resultados if r['exitoso']) / len(self.resultados) * 100):.1f}%",
                },
                "archivos_totales_descargados": {
                    "pdfs": total_pdfs,
                    "jsons": total_jsons,
                    "total": total_pdfs + total_jsons,
                },
                "scripts_ejecutados": [],
            }

            # Agregar información detallada de cada script
            for i, resultado in enumerate(self.resultados, 1):
                script_info = self.scripts[i - 1]
                carpeta_descargas = script_info.get("carpeta_descargas", "")
                filtro_usado = script_info.get("filtro", "No especificado")

                # Contar archivos descargados
                conteo = {"pdfs": 0, "jsons": 0, "total": 0}
                if carpeta_descargas:
                    conteo = self.contar_archivos_descargados(carpeta_descargas)

                script_detalle = {
                    "orden": i,
                    "nombre": resultado["nombre"],
                    "archivo": script_info["archivo"],
                    "descripcion": script_info["descripcion"],
                    "filtro_usado": filtro_usado,
                    "estado": "exitoso" if resultado["exitoso"] else "fallido",
                    "duracion_segundos": resultado["duracion"],
                    "duracion_formateada": f"{resultado['duracion']:.2f}s",
                    "carpeta_descargas": carpeta_descargas,
                    "archivos_descargados": conteo,
                    "error": resultado.get("error", None),
                }

                reporte["scripts_ejecutados"].append(script_detalle)

            # Guardar el JSON
            with open(archivo_reporte, "w", encoding="utf-8") as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)

            print(f"📊 Reporte JSON generado: {archivo_reporte}")
            return archivo_reporte

        except Exception as e:
            print(f"⚠️ Error al generar reporte JSON: {e}")
            traceback.print_exc()
            return None

    def ejecutar_script(self, script_info, numero, total):
        """
        Ejecuta un script individual de Python

        Args:
            script_info: Diccionario con información del script
            numero: Número del script en la secuencia
            total: Total de scripts a ejecutar

        Returns:
            bool: True si fue exitoso, False si falló
        """
        nombre = script_info["nombre"]
        archivo = script_info["archivo"]
        descripcion = script_info["descripcion"]

        # Usar ruta relativa al mismo nivel que el orquestador
        ruta_completa = os.path.join(self.directorio_base, archivo)

        print("\n" + "=" * 70)
        print(f"🚀 EJECUTANDO SCRIPT {numero}/{total}")
        print("=" * 70)
        print(f"📄 Script: {nombre}")
        print(f"📝 Descripción: {descripcion}")
        print(f"📂 Archivo: {archivo}")
        print(f"📍 Directorio base: {self.directorio_base}")
        print(f"⏰ Hora de inicio: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70 + "\n")

        # Verificar que el archivo existe
        if not os.path.exists(ruta_completa):
            print(f"❌ ERROR: El archivo '{archivo}' no existe en la ruta especificada")
            print(f"   Ruta buscada: {ruta_completa}\n")
            return False

        try:
            # Obtener el tiempo de inicio
            inicio = datetime.now()

            # Ejecutar el script
            # subprocess.run espera a que el proceso termine completamente
            resultado = subprocess.run(
                [sys.executable, ruta_completa],
                cwd=self.directorio_base,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # Calcular duración
            duracion = (datetime.now() - inicio).total_seconds()

            # Mostrar la salida del script
            if resultado.stdout:
                print("\n📤 SALIDA DEL SCRIPT:")
                print("-" * 70)
                print(resultado.stdout)
                print("-" * 70)

            # Verificar si hubo errores
            if resultado.returncode != 0:
                print(
                    f"\n❌ El script terminó con código de error: {resultado.returncode}"
                )
                if resultado.stderr:
                    print("\n📛 ERRORES DETECTADOS:")
                    print("-" * 70)
                    print(resultado.stderr)
                    print("-" * 70)

                self.resultados.append(
                    {
                        "nombre": nombre,
                        "exitoso": False,
                        "duracion": duracion,
                        "error": f"Código de salida: {resultado.returncode}",
                    }
                )
                return False

            print(f"\n✅ Script completado exitosamente")
            print(f"⏱️  Duración: {duracion:.2f} segundos")

            self.resultados.append(
                {"nombre": nombre, "exitoso": True, "duracion": duracion, "error": None}
            )
            return True

        except Exception as e:
            print(f"\n❌ ERROR al ejecutar el script:")
            print(f"   {str(e)}")
            print("\n📛 Detalles del error:")
            traceback.print_exc()

            duracion = (
                (datetime.now() - inicio).total_seconds() if "inicio" in locals() else 0
            )
            self.resultados.append(
                {
                    "nombre": nombre,
                    "exitoso": False,
                    "duracion": duracion,
                    "error": str(e),
                }
            )
            return False

    def ejecutar_secuencia(self):
        """
        Ejecuta todos los scripts en secuencia

        Returns:
            bool: True si todos fueron exitosos, False si alguno falló
        """
        self.imprimir_banner()

        total = len(self.scripts)

        for i, script in enumerate(self.scripts, 1):
            exitoso = self.ejecutar_script(script, i, total)

            if not exitoso:
                print(f"\n⚠️  ADVERTENCIA: El script '{script['nombre']}' falló")
                print("   Continuando con el siguiente script...\n")
                # Continuar con el siguiente script aunque falle uno
                continue

            # Esperar un poco entre scripts
            if i < total:
                print(f"\n⏸️  Esperando 5 segundos antes del siguiente script...\n")
                import time

                time.sleep(5)

        self.imprimir_resumen_final()

        # Generar reporte JSON
        print("\n📝 Generando reporte JSON de la ejecución...")
        self.generar_reporte_json()

        # Retornar True solo si todos fueron exitosos
        return all(r["exitoso"] for r in self.resultados)


def main():
    """Función principal"""
    try:
        orquestador = OrquestadorDescargas()
        exitoso = orquestador.ejecutar_secuencia()

        # Código de salida: 0 si todo OK, 1 si hubo fallos
        sys.exit(0 if exitoso else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución interrumpida por el usuario (Ctrl+C)")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO en el orquestador:")
        print(f"   {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
