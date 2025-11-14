# 🚀 Sistema de Descarga Automática de Documentos - Hermaco ERP

Sistema automatizado para descargar facturas, gastos y remisiones del ERP de Hermaco utilizando Selenium en modo headless.

## 📋 Descripción

Este sistema ejecuta de forma secuencial tres descargadores que extraen documentos del ERP:

1. **Descargador de Facturas de Ayer** - Descarga todas las facturas del día anterior
2. **Descargador de Gastos** - Descarga gastos con estado "Pagado"
3. **Descargador de Remisiones** - Descarga notas de remisión del ejercicio actual

## ✨ Características

- ✅ **Modo Headless**: Ejecuta sin interfaz gráfica (ideal para servidores)
- ✅ **Orquestación Automática**: Ejecuta los scripts en secuencia
- ✅ **Gestión de Errores**: Continúa con el siguiente script si uno falla
- ✅ **Tracking Inteligente**: Guarda el progreso para evitar duplicados
- ✅ **Reportes Detallados**: Genera logs y resúmenes de ejecución
- ✅ **Programación Automática**: Compatible con Task Scheduler de Windows

## 🏗️ Estructura del Proyecto

```
extractor-facturas-selenium-hermaco/
│
├── Orquestador.py                    # Script principal que ejecuta todo
├── descargador_diario copy.py        # Descarga facturas de AYER
├── descargadordegastos.py            # Descarga gastos
├── descargadorderemisiones.py        # Descarga remisiones
│
├── requirements.txt                   # Dependencias del proyecto
├── test_instalacion.py               # Script para verificar instalación
├── GUIA_INSTALACION_WINDOWS_SERVER.md # Guía completa de instalación
├── README.md                         # Este archivo
│
├── descargas_diarias/                # PDFs y JSONs de facturas
├── descargas_gastos/                 # PDFs y JSONs de gastos
└── descargas_remisiones/             # PDFs y JSONs de remisiones
```

## 🔧 Requisitos

- **Python 3.11+**
- **Google Chrome** (última versión) - **OBLIGATORIO** ⚠️
  - Aunque ejecute en modo headless, Chrome debe estar instalado
  - ChromeDriver se descarga automáticamente, pero Chrome no
- **Windows Server 2012 R2+** (o Windows 10/11)
- **Conexión a Internet**

## 📦 Instalación Rápida

### 1. Instalar Dependencias

```powershell
pip install -r requirements.txt
```

### 2. Verificar Instalación

```powershell
python test_instalacion.py
```

### 3. Ejecutar el Sistema

```powershell
python Orquestador.py
```

## 📚 Guía Completa

Para una guía detallada de instalación en Windows Server, consulta:
**[GUIA_INSTALACION_WINDOWS_SERVER.md](GUIA_INSTALACION_WINDOWS_SERVER.md)**

La guía incluye:
- Instalación paso a paso de Python y Chrome
- Configuración del proyecto
- Programación de tareas automáticas con Task Scheduler
- Solución de problemas comunes
- Configuración de logs y monitoreo

## 🎯 Uso del Orquestador

El orquestador ejecuta los tres scripts en orden:

```powershell
python Orquestador.py
```

### Salida Esperada

```
======================================================================
               ORQUESTADOR DE DESCARGAS - HERMACO ERP
======================================================================
📅 Fecha y hora de inicio: 2025-11-11 08:00:00
📂 Directorio de trabajo: C:\Dashboard\extractor de facturas\...
🔧 Modo: Headless (sin interfaz gráfica)
📋 Scripts a ejecutar: 3
======================================================================

🚀 EJECUTANDO SCRIPT 1/3
...
```

## 📊 Archivos de Tracking

### Reporte de Ejecución del Orquestador
- `reporte_ejecucion_YYYYMMDD_HHMMSS.json` - Reporte completo de cada ejecución
  - Fecha y hora de inicio/fin
  - Duración total y por script
  - Estado de cada script (exitoso/fallido)
  - Conteo de archivos descargados (PDFs y JSONs)
  - Detalles de errores si los hay

### Facturas de Ayer
- `descargas_diarias/ultimo_exitoso.json` - Último DTE procesado
- `descargas_diarias/reporte_fallidos_*.json` - Registros fallidos

### Gastos
- `descargas_gastos/01descargados.json` - Gastos descargados
- `descargas_gastos/02ignorados.json` - Gastos ignorados (estado "Debido")

### Remisiones
- `descargas_remisiones/ultimo_exitoso.json` - Último correlativo procesado

## ⏰ Programación Automática

### Crear Tarea en Windows Task Scheduler

1. Abre el Programador de Tareas: `Win + R` → `taskschd.msc`
2. Crea una nueva tarea básica
3. Configura:
   - **Programa**: `C:\...\Python\python.exe`
   - **Argumentos**: `Orquestador.py`
   - **Directorio**: Ruta del proyecto
   - **Horario**: Diario a las 8:00 AM (o lo que prefieras)

Ver guía completa para detalles.

## 🔍 Solución de Problemas

### Error: "python no se reconoce como comando"
- Asegúrate de que Python esté en el PATH
- Reinstala Python marcando "Add Python to PATH"

### Error: "ModuleNotFoundError"
```powershell
pip install -r requirements.txt
```

### Error: ChromeDriver
```powershell
pip install --upgrade webdriver-manager
```

### Los archivos no se descargan
- Verifica credenciales en los scripts
- Verifica permisos de escritura en carpetas
- Revisa logs de ejecución

## 🛠️ Dependencias

- `selenium` - Automatización del navegador
- `webdriver-manager` - Gestión de ChromeDriver
- `urllib3` - Cliente HTTP
- `certifi` - Certificados SSL

## 📝 Notas Importantes

### Credenciales
Los scripts usan credenciales hardcodeadas:
- Usuario: `Henri`
- Contraseña: `Bajmut`

Si cambian, actualizar en cada script.

### Modo Headless
Todos los scripts están configurados para ejecutar sin interfaz gráfica:
```python
chrome_options.add_argument("--headless=new")
```

### Filtro de Fechas
- **descargador_diario copy.py**: Filtra por "Ayer"
- **descargadordegastos.py**: Filtra por "Ejercicio actual"
- **descargadorderemisiones.py**: Filtra por "Ejercicio actual"

## 🎨 Características de los Scripts Individuales

### Descargador de Facturas de Ayer
- Filtra facturas del día anterior
- Guarda progreso para continuar donde quedó
- Sistema de reintentos (3 intentos)
- Reportes de fallidos

### Descargador de Gastos
- Solo descarga gastos con estado "Pagado"
- Ignora gastos con estado "Debido"
- Verifica gastos ignorados en cada ejecución
- Sistema de tracking con JSON

### Descargador de Remisiones
- Descarga remisiones del ejercicio actual
- Guarda último correlativo procesado
- Procesa desde el último exitoso hacia adelante

## 🤝 Contribuciones

Para reportar problemas o sugerir mejoras, contacta al administrador del sistema.

## 📄 Licencia

Uso interno - Hermaco

## 📞 Soporte

Para soporte técnico:
1. Consulta la [Guía de Instalación](GUIA_INSTALACION_WINDOWS_SERVER.md)
2. Revisa los logs de ejecución
3. Ejecuta el test de instalación: `python test_instalacion.py`
4. Contacta al desarrollador del sistema

---

**Última actualización**: Noviembre 2025  
**Versión**: 1.0  
**Autor**: Sistema de Automatización Hermaco
