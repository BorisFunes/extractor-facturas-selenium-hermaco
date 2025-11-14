"""
TEST DE INSTALACIÓN
===================
Script para verificar que todas las dependencias estén correctamente instaladas
"""

print("=" * 70)
print(" " * 20 + "VERIFICACIÓN DE INSTALACIÓN")
print("=" * 70 + "\n")

errores = []

# Verificar Python
import sys

print(f"✅ Python versión: {sys.version}")
print(f"   Ruta: {sys.executable}\n")

# Verificar Selenium
try:
    import selenium

    print(f"✅ Selenium versión: {selenium.__version__}")
except ImportError as e:
    print(f"❌ Error al importar Selenium: {e}")
    errores.append("selenium")

# Verificar webdriver-manager
try:
    from webdriver_manager.chrome import ChromeDriverManager

    print("✅ webdriver-manager instalado correctamente")
except ImportError as e:
    print(f"❌ Error al importar webdriver-manager: {e}")
    errores.append("webdriver-manager")

# Verificar urllib3
try:
    import urllib3

    print(f"✅ urllib3 versión: {urllib3.__version__}")
except ImportError as e:
    print(f"❌ Error al importar urllib3: {e}")
    errores.append("urllib3")

# Verificar certifi
try:
    import certifi

    print(f"✅ certifi versión: {certifi.__version__}")
except ImportError as e:
    print(f"❌ Error al importar certifi: {e}")
    errores.append("certifi")

# Verificar otras dependencias de selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    print("✅ Módulos de Selenium importados correctamente")
except ImportError as e:
    print(f"❌ Error al importar módulos de Selenium: {e}")
    errores.append("selenium-modules")

# Verificar que Chrome esté instalado
print("\n🌐 Verificando Google Chrome...")
try:
    import os
    import winreg

    # Buscar Chrome en el registro de Windows
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        )
        chrome_path = winreg.QueryValue(key, None)
        print(f"✅ Google Chrome encontrado en: {chrome_path}")
    except:
        # Intentar en HKEY_CURRENT_USER
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
            )
            chrome_path = winreg.QueryValue(key, None)
            print(f"✅ Google Chrome encontrado en: {chrome_path}")
        except:
            print("⚠️  No se pudo encontrar Google Chrome en el registro de Windows")
            print("   Esto podría no ser un problema si Chrome está instalado")

except Exception as e:
    print(f"❌ Error al verificar Chrome: {e}")

# Verificar estructuras de directorios
print("\n📂 Verificando estructura de directorios...")
import os

directorios_necesarios = [
    "descargas_diarias",
    "descargas_gastos",
    "descargas_remisiones",
]

for directorio in directorios_necesarios:
    if os.path.exists(directorio):
        print(f"✅ Directorio '{directorio}' existe")
    else:
        print(f"⚠️  Directorio '{directorio}' no existe (se creará automáticamente)")

# Verificar scripts principales
print("\n📄 Verificando scripts principales...")
scripts = [
    "Orquestador.py",
    "descargador_diario copy.py",
    "descargadordegastos.py",
    "descargadorderemisiones.py",
]

for script in scripts:
    if os.path.exists(script):
        print(f"✅ Script '{script}' encontrado")
    else:
        print(f"❌ Script '{script}' NO encontrado")
        errores.append(f"script-{script}")

# Resumen final
print("\n" + "=" * 70)
if not errores:
    print("🎉 VERIFICACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print("\n✅ Todas las dependencias están instaladas correctamente")
    print("✅ El sistema está listo para usarse")
    print("\n💡 Siguiente paso: Ejecutar 'python Orquestador.py'")
else:
    print("⚠️  VERIFICACIÓN COMPLETADA CON ERRORES")
    print("=" * 70)
    print(f"\n❌ Se encontraron {len(errores)} problemas:")
    for error in errores:
        print(f"   - {error}")
    print("\n💡 Solución: Instala las dependencias faltantes con:")
    print("   pip install -r requirements.txt")

print("\n" + "=" * 70)
