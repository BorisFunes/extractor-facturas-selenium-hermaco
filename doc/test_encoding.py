"""
Script de prueba para verificar la codificación UTF-8 en Windows
"""

import sys
import io

# Configurar codificación UTF-8 para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

print("=" * 70)
print("🔧 TEST DE CODIFICACIÓN UTF-8 EN WINDOWS")
print("=" * 70)
print("✅ Si ves emojis correctamente, la codificación funciona!")
print("📅 Fecha actual")
print("📂 Carpeta")
print("🚀 Lanzamiento")
print("❌ Error")
print("⚠️  Advertencia")
print("📊 Estadísticas")
print("=" * 70)
print("\n✅ Test completado exitosamente!")
