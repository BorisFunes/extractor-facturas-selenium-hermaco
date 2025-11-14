# 🎯 Orquestador de Descargas - HERMACO ERP

## 📋 Descripción

El **Orquestador** ejecuta automáticamente los 3 scripts de descarga en el siguiente orden:

1. ✅ **Descargador de Facturas de Ayer** (`descargador_diario copy.py`)
2. ✅ **Descargador de Remisiones** (`descargadorderemisiones.py`)
3. ✅ **Descargador de Gastos** (`descargadordegastos.py`)

## 🚀 Ejecución

### Comando básico:
```powershell
python Orquestador.py
```

### Ejecución programada (Windows Task Scheduler):
```powershell
# Ruta completa al Python y al script
C:\Python314\python.exe "J:\Henri\extractor-facturas-selenium-hermaco-main\Orquestador.py"
```

## 📊 Características

### ✅ Ejecución Automática
- Los scripts se ejecutan secuencialmente
- Si un script falla, continúa con el siguiente
- Modo headless (sin ventana del navegador)
- Cierre automático al terminar (sin intervención del usuario)

### 📈 Filtros Aplicados por Cada Script

| Script | Filtro Utilizado |
|--------|------------------|
| **Facturas** | Ayer (día anterior) |
| **Remisiones** | Ejercicio actual - Todas las remisiones nuevas |
| **Gastos** | Estado: Pagado - Tipo: Gastos (DTE-14) |

### 📄 Reporte de Ejecución

Al finalizar, genera automáticamente un archivo JSON con:
- ✅ Estado de cada script (exitoso/fallido)
- ⏱️ Duración de ejecución de cada uno
- 📁 Cantidad de archivos descargados (PDFs y JSONs)
- 🔍 Filtros utilizados en cada script
- 📊 Resumen general con totales

**Nombre del archivo:** `reporte_ejecucion_YYYYMMDD_HHMMSS.json`

**Ejemplo de ubicación:** `reporte_ejecucion_20251112_103000.json`

## 📁 Estructura de Carpetas

```
extractor-facturas-selenium-hermaco/
│
├── Orquestador.py                          # Script principal
│
├── descargador_diario copy.py              # Script 1: Facturas de ayer
├── descargadorderemisiones.py              # Script 2: Remisiones
├── descargadordegastos.py                  # Script 3: Gastos
│
├── descargas_diarias/                      # Facturas descargadas
├── descargas_remisiones/                   # Remisiones descargadas
├── descargas_gastos/                       # Gastos descargados
│
└── reporte_ejecucion_*.json                # Reportes generados
```

## 📊 Ejemplo de Salida en Consola

```
======================================================================
               ORQUESTADOR DE DESCARGAS - HERMACO ERP
======================================================================
📅 Fecha y hora de inicio: 2025-11-12 10:30:00
📂 Directorio de trabajo: J:\Henri\extractor-facturas-selenium-hermaco-main
🔧 Modo: Headless (sin interfaz gráfica)
📋 Scripts a ejecutar: 3
======================================================================

======================================================================
🚀 EJECUTANDO SCRIPT 1/3
======================================================================
📄 Script: Descargador de Facturas de Ayer
📝 Descripción: Descarga facturas del día anterior
📂 Archivo: descargador_diario copy.py
⏰ Hora de inicio: 10:30:05
======================================================================

[... salida del script ...]

✅ Script completado exitosamente
⏱️  Duración: 245.67 segundos

⏸️  Esperando 5 segundos antes del siguiente script...

[... continúa con los demás scripts ...]

======================================================================
                    RESUMEN FINAL DE EJECUCIÓN
======================================================================

✅ EXITOSO - Descargador de Facturas de Ayer
   📝 Descripción: Descarga facturas del día anterior
   🔍 Filtro usado: Ayer (facturas del día anterior)
   ⏱️  Duración: 245.67 segundos
   📁 Archivos descargados:
      • PDFs: 45
      • JSONs: 45
      • Total: 90

✅ EXITOSO - Descargador de Remisiones
   📝 Descripción: Descarga notas de remisión del ejercicio actual
   🔍 Filtro usado: Ejercicio actual - Todas las remisiones nuevas
   ⏱️  Duración: 320.45 segundos
   📁 Archivos descargados:
      • PDFs: 78
      • JSONs: 78
      • Total: 156

✅ EXITOSO - Descargador de Gastos
   📝 Descripción: Descarga todos los gastos con estado 'Pagado'
   🔍 Filtro usado: Estado: Pagado - Tipo: Gastos (DTE-14)
   ⏱️  Duración: 364.00 segundos
   📁 Archivos descargados:
      • PDFs: 33
      • JSONs: 33
      • Total: 66

----------------------------------------------------------------------
📊 Total de scripts ejecutados: 3
✅ Exitosos: 3
❌ Fallidos: 0

📦 Total de archivos descargados:
   • PDFs: 156
   • JSONs: 156
   • Total: 312

📅 Fecha y hora de finalización: 2025-11-12 10:45:30
⏱️  Duración total: 930.12s (15.50m)
======================================================================

📝 Generando reporte JSON de la ejecución...
📊 Reporte JSON generado: reporte_ejecucion_20251112_103000.json
```

## 🛠️ Requisitos

- ✅ Python 3.x
- ✅ Selenium instalado
- ✅ Chrome/Chromium instalado
- ✅ ChromeDriver en PATH del sistema
- ✅ Credenciales configuradas en cada script

## ⚙️ Configuración de Tarea Programada (Windows)

### 1. Abrir el Programador de Tareas
- Presiona `Win + R`
- Escribe `taskschd.msc`
- Presiona Enter

### 2. Crear Nueva Tarea
1. Clic derecho en "Biblioteca del Programador de tareas"
2. "Crear tarea básica..."
3. Nombre: `Orquestador HERMACO - Descargas Diarias`
4. Desencadenador: `Diariamente` a las `08:00 AM`
5. Acción: `Iniciar un programa`
   - Programa: `C:\Python314\python.exe`
   - Argumentos: `"J:\Henri\extractor-facturas-selenium-hermaco-main\Orquestador.py"`
   - Iniciar en: `J:\Henri\extractor-facturas-selenium-hermaco-main`

### 3. Configuraciones Adicionales
- ✅ Ejecutar aunque el usuario no haya iniciado sesión
- ✅ Ejecutar con los privilegios más altos
- ✅ Configurar para: Windows Server 2016 o posterior

## 🔧 Solución de Problemas

### El orquestador no ejecuta los scripts
- Verifica que los archivos existan en la ruta especificada
- Comprueba que Python esté en el PATH del sistema
- Revisa los permisos de ejecución

### Los scripts fallan en modo headless
- Verifica que Chrome esté instalado
- Comprueba que ChromeDriver esté actualizado
- Revisa las credenciales de acceso al ERP

### No se generan los reportes
- Verifica permisos de escritura en la carpeta
- Comprueba que los scripts finalicen correctamente

## 📞 Soporte

Para problemas o consultas, revisa:
- `FAQ.md` - Preguntas frecuentes
- `RESUMEN_CAMBIOS.md` - Registro de cambios
- `GUIA_INSTALACION_WINDOWS_SERVER.md` - Guía de instalación

---

**Última actualización:** 12 de noviembre de 2025
