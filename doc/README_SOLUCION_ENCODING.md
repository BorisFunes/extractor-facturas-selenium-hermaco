# 🔧 Solución al Error de Codificación en Windows Server

## ❌ Problema
Los scripts fallaban con error `UnicodeEncodeError: 'charmap' codec can't encode character` porque PowerShell en Windows Server usa codificación `cp1252` que no soporta emojis.

## ✅ Solución Implementada
Se agregó al inicio de todos los scripts Python la configuración UTF-8 para Windows:

```python
import sys
import io

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

## 📝 Archivos Modificados
1. ✅ `Orquestador.py` - Script principal orquestador
2. ✅ `descargador_diario_copy.py` - Descargador de facturas de ayer
3. ✅ `descargador_diario.py` - Descargador de facturas (versión original)
4. ✅ `descargadorderemisiones.py` - Descargador de remisiones
5. ✅ `descargadordegastos.py` - Descargador de gastos

## 🚀 Cómo Usar

### Ejecutar el Orquestador (RECOMENDADO)
El orquestador ejecuta los 3 scripts en orden automáticamente:

```powershell
python Orquestador.py
```

**Orden de ejecución:**
1. Descargador de Facturas de Ayer (`descargador_diario_copy.py`)
2. Descargador de Remisiones (`descargadorderemisiones.py`)
3. Descargador de Gastos (`descargadordegastos.py`)

### Ejecutar Scripts Individuales
Si necesitas ejecutar solo un script específico:

```powershell
# Descargar facturas de ayer
python descargador_diario_copy.py

# Descargar remisiones
python descargadorderemisiones.py

# Descargar gastos
python descargadordegastos.py
```

## 🧪 Probar la Codificación
Para verificar que la codificación UTF-8 funciona correctamente:

```powershell
python test_encoding.py
```

Deberías ver emojis correctamente. Si ves caracteres raros o errores, contacta al administrador.

## 📊 Características del Orquestador

### ✅ Ejecución Secuencial
- Los scripts se ejecutan UNO después del OTRO
- Cada script espera a que el anterior termine
- No hay ejecución en paralelo

### ✅ Modo Headless
- Todos los scripts corren en modo **headless** (sin ventana del navegador)
- Ideal para Windows Server sin interfaz gráfica
- Menor consumo de recursos

### ✅ Reportes de Ejecución
- Muestra progreso en tiempo real
- Reporta éxitos y errores
- Genera archivos JSON con estadísticas
- Cuenta archivos descargados (PDFs y JSONs)

### ✅ Manejo de Errores
- Si un script falla, continúa con el siguiente
- No requiere permisos de administrador
- Registra todos los errores en consola

## 📂 Carpetas de Descarga
Los archivos se guardan en:
- `descargas_diarias/` - Facturas de ayer
- `descargas_remisiones/` - Notas de remisión
- `descargas_gastos/` - Gastos pagados

## ⚠️ Notas Importantes

1. **No se requieren permisos de administrador**
2. **Se ejecuta desde PowerShell normal**
3. **Los scripts ahora manejan correctamente emojis en Windows**
4. **El orquestador NO ejecuta scripts en paralelo** - uno a la vez
5. **Cada script espera que el anterior termine completamente**

## 🐛 Solución de Problemas

### Error de Codificación
Si aún ves errores de codificación, asegúrate de ejecutar en PowerShell:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
python Orquestador.py
```

### Script No Encontrado
Verifica que estés en el directorio correcto:
```powershell
cd "J:\Henri\extractor-facturas-selenium-hermaco-main\extractor-facturas-selenium-hermaco-main"
python Orquestador.py
```

### Navegador No Se Cierra
Si un script se queda colgado, presiona `Ctrl+C` para interrumpir.

---

**Fecha de actualización:** 13 de noviembre de 2025
**Versión:** 1.0 - Arreglo de codificación UTF-8 para Windows Server
