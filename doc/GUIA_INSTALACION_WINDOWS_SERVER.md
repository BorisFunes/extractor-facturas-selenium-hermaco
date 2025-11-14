# 📘 GUÍA DE INSTALACIÓN Y CONFIGURACIÓN - WINDOWS SERVER
## Sistema de Descarga Automática de Facturas Hermaco ERP

---

## 📋 TABLA DE CONTENIDOS
1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Instalación de Python](#instalación-de-python)
3. [Instalación de Google Chrome](#instalación-de-google-chrome)
4. [Configuración del Proyecto](#configuración-del-proyecto)
5. [Instalación de Dependencias](#instalación-de-dependencias)
6. [Verificación de la Instalación](#verificación-de-la-instalación)
7. [Ejecución del Orquestador](#ejecución-del-orquestador)
8. [Programación de Tareas Automáticas](#programación-de-tareas-automáticas)
9. [Solución de Problemas](#solución-de-problemas)

---

## 🖥️ REQUISITOS DEL SISTEMA

- **Sistema Operativo**: Windows Server 2012 R2 o superior
- **RAM**: Mínimo 4 GB (recomendado 8 GB)
- **Espacio en Disco**: Mínimo 2 GB libres
- **Conexión a Internet**: Estable
- **Permisos**: Administrador para instalar software

---

## 🐍 1. INSTALACIÓN DE PYTHON

### Opción A: Descarga desde el sitio oficial

1. **Descargar Python 3.11 o superior**:
   - Visita: https://www.python.org/downloads/
   - Descarga la versión **Windows installer (64-bit)** más reciente
   - Archivo ejemplo: `python-3.11.x-amd64.exe`

2. **Ejecutar el instalador**:
   - ✅ **IMPORTANTE**: Marca la opción "Add Python to PATH"
   - Haz clic en "Install Now"
   - Espera a que termine la instalación

3. **Verificar la instalación**:
   Abre PowerShell y ejecuta:
   ```powershell
   python --version
   ```
   Debería mostrar: `Python 3.11.x`

### Verificar pip

```powershell
pip --version
```
Debería mostrar la versión de pip instalada.

---

## 🌐 2. INSTALACIÓN DE GOOGLE CHROME

### ⚠️ IMPORTANTE: Chrome es OBLIGATORIO

**Aunque los scripts ejecuten en modo headless (sin ventana visible), Google Chrome DEBE estar instalado en el sistema.**

- ✅ Selenium necesita Chrome para funcionar
- ✅ ChromeDriver se descarga automáticamente, pero Chrome no
- ✅ El modo headless solo oculta la ventana, pero Chrome sigue ejecutándose
- ❌ Sin Chrome instalado, los scripts fallarán inmediatamente

### Pasos de instalación:

1. **Descargar Google Chrome**:
   - Visita: https://www.google.com/chrome/
   - Descarga el instalador para Windows (64-bit)

2. **Instalar Chrome**:
   - Ejecuta el instalador descargado (`ChromeSetup.exe`)
   - Sigue las instrucciones en pantalla
   - Chrome se instalará automáticamente en: `C:\Program Files\Google\Chrome\`

3. **Verificar la instalación**:
   - Abre Chrome para asegurarte de que funciona correctamente
   - **Opcional**: Configura Chrome para que NO se abra automáticamente al iniciar Windows
   - Cierra Chrome después de verificar

4. **Mantener Chrome actualizado**:
   - Chrome se actualiza automáticamente
   - Si tienes problemas, actualiza manualmente: Menú → Ayuda → Información de Google Chrome

**NOTA**: No es necesario instalar ChromeDriver manualmente. El proyecto usa `webdriver-manager` que descarga la versión correcta automáticamente.

---

## 📂 3. CONFIGURACIÓN DEL PROYECTO

1. **Crear directorio para el proyecto** (si no existe):
   ```powershell
   cd C:\Dashboard
   cd "extractor de facturas"
   cd extractor-facturas-selenium-hermaco
   ```

2. **Verificar que los archivos estén presentes**:
   ```powershell
   dir
   ```
   
   Deberías ver:
   - ✅ `Orquestador.py`
   - ✅ `descargador_diario copy.py`
   - ✅ `descargadordegastos.py`
   - ✅ `descargadorderemisiones.py`

---

## 📦 4. INSTALACIÓN DE DEPENDENCIAS

### Librerias y Dependencias Necesarias

El proyecto requiere las siguientes librerías de Python:

1. **selenium** - Para automatización del navegador web
2. **webdriver-manager** - Para gestión automática de ChromeDriver
3. **urllib3** - Para manejo de solicitudes HTTP (dependencia de selenium)
4. **certifi** - Para validación de certificados SSL

### Instalación Automática (Recomendado)

Ejecuta el siguiente comando en PowerShell (en el directorio del proyecto):

```powershell
pip install selenium webdriver-manager urllib3 certifi
```

### Instalación con Versiones Específicas (Opcional)

Si prefieres instalar versiones específicas para evitar problemas de compatibilidad:

```powershell
pip install selenium==4.15.2 webdriver-manager==4.0.1 urllib3==2.1.0 certifi==2023.11.17
```

### Verificar las instalaciones

```powershell
pip list
```

Deberías ver en la lista:
```
selenium           4.x.x
webdriver-manager  4.x.x
urllib3            2.x.x
certifi            2023.x.x
```

---

## ✅ 5. VERIFICACIÓN DE LA INSTALACIÓN

### Crear script de prueba

Crea un archivo `test_instalacion.py` con el siguiente contenido:

```python
print("=== VERIFICACIÓN DE INSTALACIÓN ===\n")

# Verificar Python
import sys
print(f"✅ Python versión: {sys.version}")

# Verificar Selenium
try:
    import selenium
    print(f"✅ Selenium versión: {selenium.__version__}")
except ImportError as e:
    print(f"❌ Error al importar Selenium: {e}")

# Verificar webdriver-manager
try:
    from webdriver_manager.chrome import ChromeDriverManager
    print("✅ webdriver-manager instalado correctamente")
except ImportError as e:
    print(f"❌ Error al importar webdriver-manager: {e}")

# Verificar urllib3
try:
    import urllib3
    print(f"✅ urllib3 versión: {urllib3.__version__}")
except ImportError as e:
    print(f"❌ Error al importar urllib3: {e}")

# Verificar que Chrome esté instalado
try:
    import os
    import winreg
    
    # Buscar Chrome en el registro de Windows
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                             r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
        chrome_path = winreg.QueryValue(key, None)
        print(f"✅ Google Chrome encontrado en: {chrome_path}")
    except:
        print("⚠️ No se pudo encontrar Google Chrome en el registro")
        
except Exception as e:
    print(f"❌ Error al verificar Chrome: {e}")

print("\n=== FIN DE VERIFICACIÓN ===")
```

### Ejecutar el test

```powershell
python test_instalacion.py
```

Si todo está correcto, deberías ver varios ✅ sin errores.

---

## 🚀 6. EJECUCIÓN DEL ORQUESTADOR

### Ejecución Manual

Para ejecutar el sistema completo de descargas:

```powershell
# Navegar al directorio del proyecto
cd "C:\Dashboard\extractor de facturas\extractor-facturas-selenium-hermaco"

# Ejecutar el orquestador
python Orquestador.py
```

### ¿Qué hace el Orquestador?

El `Orquestador.py` ejecutará en secuencia:

1. **Descargador de Facturas de Ayer** (`descargador_diario copy.py`)
   - Descarga todas las facturas del día anterior
   - Guarda PDFs y JSONs en: `descargas_diarias/`

2. **Descargador de Gastos** (`descargadordegastos.py`)
   - Descarga todos los gastos con estado "Pagado"
   - Guarda PDFs y JSONs en: `descargas_gastos/`
   - Mantiene registro de descargados e ignorados

3. **Descargador de Remisiones** (`descargadorderemisiones.py`)
   - Descarga notas de remisión del ejercicio actual
   - Guarda PDFs y JSONs en: `descargas_remisiones/`

### Características del modo headless

- ✅ No abre ventanas de navegador visibles
- ✅ Consume menos recursos del sistema
- ✅ Ideal para ejecución en servidores sin monitor
- ✅ Puede ejecutarse en segundo plano
- ✅ Compatible con ejecución programada (Task Scheduler)

---

## ⏰ 7. PROGRAMACIÓN DE TAREAS AUTOMÁTICAS

### Usando el Programador de Tareas de Windows

#### Paso 1: Abrir el Programador de Tareas

1. Presiona `Win + R`
2. Escribe: `taskschd.msc`
3. Presiona Enter

#### Paso 2: Crear una Nueva Tarea

1. En el panel derecho, haz clic en **"Crear tarea..."**
2. En la pestaña **General**:
   - Nombre: `Descarga Facturas Hermaco`
   - Descripción: `Ejecuta el orquestador de descargas de facturas, gastos y remisiones`
   - ✅ Marca: "Ejecutar tanto si el usuario inició sesión o no"
   - ✅ Marca: "Ejecutar con los privilegios más altos"

#### Paso 3: Configurar el Desencadenador (Trigger)

1. Ve a la pestaña **Desencadenadores**
2. Haz clic en **Nuevo...**
3. Configuración sugerida para ejecución diaria:
   - **Iniciar la tarea**: Diariamente
   - **Iniciar**: Selecciona la hora (por ejemplo: 8:00 AM)
   - **Repetir cada**: (opcional) Puedes dejarlo sin repetir
   - ✅ Marca: "Habilitado"
4. Haz clic en **Aceptar**

#### Paso 4: Configurar la Acción

1. Ve a la pestaña **Acciones**
2. Haz clic en **Nueva...**
3. Configuración:
   - **Acción**: Iniciar un programa
   - **Programa o script**: 
     ```
     C:\Users\TU_USUARIO\AppData\Local\Programs\Python\Python311\python.exe
     ```
     (Ajusta la ruta según tu instalación de Python)
   
   - **Agregar argumentos**:
     ```
     Orquestador.py
     ```
   
   - **Iniciar en**:
     ```
     C:\Dashboard\extractor de facturas\extractor-facturas-selenium-hermaco
     ```
4. Haz clic en **Aceptar**

#### Paso 5: Configurar Condiciones (Opcional)

1. Ve a la pestaña **Condiciones**
2. Puedes ajustar:
   - ❌ Desmarcar: "Iniciar solo si el equipo usa alimentación de CA" (si es portátil)
   - ❌ Desmarcar: "Detener si el equipo deja de usar alimentación de CA"

#### Paso 6: Configurar Opciones

1. Ve a la pestaña **Configuración**
2. Sugerencias:
   - ✅ Marca: "Permitir que se ejecute la tarea a petición"
   - ✅ Marca: "Ejecutar la tarea lo antes posible después de un inicio programado perdido"
   - ✅ Marca: "Si la tarea falla, reiniciar cada": 10 minutos
   - Número de reintentos: 3
   - ❌ Desmarcar: "Detener la tarea si se ejecuta más de": (o poner 2 horas)

#### Paso 7: Guardar y Probar

1. Haz clic en **Aceptar**
2. Ingresa tu contraseña de Windows cuando se solicite
3. Para probar inmediatamente:
   - Busca la tarea en la lista
   - Haz clic derecho → **Ejecutar**
   - Verifica en la pestaña **Historial** que se ejecutó correctamente

### Script de PowerShell para crear la tarea automáticamente

Crea un archivo `crear_tarea_programada.ps1`:

```powershell
# Script para crear tarea programada automáticamente
# NOTA: Ejecutar como Administrador

$nombreTarea = "Descarga_Facturas_Hermaco"
$descripcion = "Ejecuta el orquestador de descargas de facturas, gastos y remisiones del ERP Hermaco"

# Ajusta estas rutas según tu instalación
$pythonExe = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe"
$scriptPath = "C:\Dashboard\extractor de facturas\extractor-facturas-selenium-hermaco"
$scriptFile = "Orquestador.py"

# Configurar la acción
$action = New-ScheduledTaskAction -Execute $pythonExe `
    -Argument $scriptFile `
    -WorkingDirectory $scriptPath

# Configurar el desencadenador (todos los días a las 8:00 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM

# Configurar las opciones
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Configurar el principal (usuario que ejecuta la tarea)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Registrar la tarea
Register-ScheduledTask -TaskName $nombreTarea `
    -Description $descripcion `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force

Write-Host "✅ Tarea programada creada exitosamente: $nombreTarea" -ForegroundColor Green
Write-Host "📅 Se ejecutará diariamente a las 8:00 AM" -ForegroundColor Cyan
Write-Host "🔍 Verifica la tarea en el Programador de Tareas de Windows" -ForegroundColor Yellow
```

Para ejecutar este script:
```powershell
# Como Administrador
powershell -ExecutionPolicy Bypass -File crear_tarea_programada.ps1
```

---

## 🔧 8. SOLUCIÓN DE PROBLEMAS

### Problema: "python no se reconoce como comando"

**Solución**:
1. Verifica que Python esté en el PATH:
   ```powershell
   $env:Path
   ```
2. Si no está, añádelo manualmente:
   - Panel de Control → Sistema → Configuración avanzada del sistema
   - Variables de entorno → Path → Editar
   - Agregar: `C:\Users\TU_USUARIO\AppData\Local\Programs\Python\Python311`

### Problema: "ModuleNotFoundError: No module named 'selenium'"

**Solución**:
```powershell
pip install --upgrade selenium webdriver-manager
```

### Problema: ChromeDriver no se descarga

**Solución**:
1. Verifica la conexión a internet
2. Ejecuta manualmente una vez para descargar ChromeDriver:
   ```powershell
   python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
   ```

### Problema: "SessionNotCreatedException: session not created"

**Solución**:
- Actualiza Google Chrome a la última versión
- Actualiza webdriver-manager:
  ```powershell
  pip install --upgrade webdriver-manager
  ```

### Problema: La tarea programada no se ejecuta

**Verificaciones**:
1. Revisa el historial de la tarea en el Programador de Tareas
2. Verifica que la ruta de Python sea correcta
3. Asegúrate de que el usuario tiene permisos
4. Ejecuta manualmente la tarea para ver errores

### Problema: Los archivos no se descargan

**Verificaciones**:
1. Verifica que las carpetas de descarga existan:
   - `descargas_diarias/`
   - `descargas_gastos/`
   - `descargas_remisiones/`
2. Verifica permisos de escritura en estas carpetas
3. Revisa los logs en la consola para errores específicos

### Problema: Error de credenciales en el ERP

**Solución**:
- Verifica que las credenciales en los scripts sean correctas
- Usuario: `Henri`
- Contraseña: `Bajmut`
- Si cambiaron, actualiza en cada script

---

## 📝 9. LOGS Y MONITOREO

### Logs generados automáticamente

Cada script genera archivos de tracking:

1. **Facturas de Ayer**:
   - `descargas_diarias/ultimo_exitoso.json` - Último DTE procesado
   - `descargas_diarias/reporte_fallidos_*.json` - Registros fallidos

2. **Gastos**:
   - `descargas_gastos/01descargados.json` - Gastos descargados
   - `descargas_gastos/02ignorados.json` - Gastos ignorados (no pagados)

3. **Remisiones**:
   - `descargas_remisiones/ultimo_exitoso.json` - Último correlativo procesado

### Redirigir salida a archivo de log

Para guardar la salida del orquestador en un archivo:

```powershell
python Orquestador.py > logs_ejecucion.txt 2>&1
```

O modificar la tarea programada para incluir redirección:
- En "Agregar argumentos": 
  ```
  Orquestador.py > C:\Dashboard\logs\log_%date:~-4,4%%date:~-10,2%%date:~-7,2%.txt 2>&1
  ```

---

## 🎯 10. RESUMEN DE COMANDOS RÁPIDOS

### Instalación completa (copiar y pegar en PowerShell como Admin)

```powershell
# Navegar al proyecto
cd "C:\Dashboard\extractor de facturas\extractor-facturas-selenium-hermaco"

# Instalar dependencias
pip install selenium webdriver-manager urllib3 certifi

# Verificar instalación
python test_instalacion.py

# Ejecutar orquestador
python Orquestador.py
```

---

## 📞 SOPORTE

Para problemas o dudas:
1. Revisa esta guía completa
2. Verifica los logs de ejecución
3. Consulta la sección de solución de problemas
4. Contacta al desarrollador del sistema

---

## ✅ CHECKLIST DE INSTALACIÓN

- [ ] Python 3.11+ instalado
- [ ] Python agregado al PATH
- [ ] Google Chrome instalado
- [ ] pip actualizado (`pip install --upgrade pip`)
- [ ] Selenium instalado
- [ ] webdriver-manager instalado
- [ ] urllib3 instalado
- [ ] certifi instalado
- [ ] Test de instalación ejecutado exitosamente
- [ ] Orquestador ejecutado manualmente al menos una vez
- [ ] Tarea programada creada (opcional)
- [ ] Tarea programada probada (opcional)

---

**Fecha de creación**: Noviembre 2025  
**Versión**: 1.0  
**Sistema**: Hermaco ERP - Descarga Automática de Documentos
