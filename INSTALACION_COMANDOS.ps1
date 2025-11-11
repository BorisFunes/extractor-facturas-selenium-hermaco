# ============================================================================
# SCRIPT DE INSTALACIÓN AUTOMATIZADA
# Sistema de Descarga de Facturas Hermaco ERP
# ============================================================================
# IMPORTANTE: Ejecutar como Administrador
# ============================================================================

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "  INSTALACIÓN AUTOMATIZADA - SISTEMA DE DESCARGAS HERMACO ERP" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan

# ----------------------------------------------------------------------------
# PASO 1: VERIFICAR SI PYTHON ESTÁ INSTALADO
# ----------------------------------------------------------------------------

Write-Host "📍 PASO 1: Verificando instalación de Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python ya está instalado: $pythonVersion" -ForegroundColor Green
    
    # Verificar que sea Python 3.x
    if ($pythonVersion -match "Python 3\.\d+") {
        Write-Host "✅ Versión de Python es compatible (3.x)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  ADVERTENCIA: Se recomienda Python 3.11 o superior" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Python NO está instalado" -ForegroundColor Red
    Write-Host "`n📥 DESCARGA E INSTALACIÓN DE PYTHON:" -ForegroundColor Yellow
    Write-Host "   1. Visita: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "   2. Descarga Python 3.11 o superior (Windows installer 64-bit)" -ForegroundColor White
    Write-Host "   3. ⚠️  IMPORTANTE: Marca la opción 'Add Python to PATH'" -ForegroundColor Red
    Write-Host "   4. Ejecuta el instalador y sigue las instrucciones" -ForegroundColor White
    Write-Host "   5. Reinicia PowerShell después de instalar" -ForegroundColor White
    Write-Host "`n❌ Instala Python y ejecuta este script nuevamente" -ForegroundColor Red
    exit 1
}

# ----------------------------------------------------------------------------
# PASO 2: VERIFICAR PIP
# ----------------------------------------------------------------------------

Write-Host "`n📍 PASO 2: Verificando instalación de pip..." -ForegroundColor Yellow

try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip está instalado: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip NO está instalado" -ForegroundColor Red
    Write-Host "   Instalando pip..." -ForegroundColor Yellow
    python -m ensurepip --upgrade
    Write-Host "✅ pip instalado correctamente" -ForegroundColor Green
}

# ----------------------------------------------------------------------------
# PASO 3: ACTUALIZAR PIP
# ----------------------------------------------------------------------------

Write-Host "`n📍 PASO 3: Actualizando pip a la última versión..." -ForegroundColor Yellow

python -m pip install --upgrade pip

Write-Host "✅ pip actualizado correctamente" -ForegroundColor Green

# ----------------------------------------------------------------------------
# PASO 4: INSTALAR DEPENDENCIAS DESDE REQUIREMENTS.TXT
# ----------------------------------------------------------------------------

Write-Host "`n📍 PASO 4: Instalando dependencias del proyecto..." -ForegroundColor Yellow
Write-Host "   Leyendo archivo requirements.txt..." -ForegroundColor White

# Verificar que existe el archivo requirements.txt
if (Test-Path "requirements.txt") {
    Write-Host "✅ Archivo requirements.txt encontrado" -ForegroundColor Green
    
    Write-Host "`n📦 Instalando paquetes:" -ForegroundColor Cyan
    Write-Host "   - selenium" -ForegroundColor White
    Write-Host "   - webdriver-manager" -ForegroundColor White
    Write-Host "   - urllib3" -ForegroundColor White
    Write-Host "   - certifi" -ForegroundColor White
    Write-Host ""
    
    # Instalar dependencias
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Todas las dependencias se instalaron correctamente" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Hubo errores al instalar algunas dependencias" -ForegroundColor Red
        Write-Host "   Revisa los mensajes de error anteriores" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "❌ ERROR: No se encuentra el archivo requirements.txt" -ForegroundColor Red
    Write-Host "   Asegúrate de ejecutar este script en el directorio del proyecto" -ForegroundColor Yellow
    exit 1
}

# ----------------------------------------------------------------------------
# PASO 5: VERIFICAR INSTALACIÓN DE GOOGLE CHROME
# ----------------------------------------------------------------------------

Write-Host "`n📍 PASO 5: Verificando instalación de Google Chrome..." -ForegroundColor Yellow

$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

$chromeFound = $false
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        Write-Host "✅ Google Chrome encontrado en: $path" -ForegroundColor Green
        $chromeFound = $true
        break
    }
}

if (-not $chromeFound) {
    Write-Host "⚠️  Google Chrome NO está instalado" -ForegroundColor Red
    Write-Host "`n🌐 GOOGLE CHROME ES OBLIGATORIO:" -ForegroundColor Yellow
    Write-Host "   Aunque los scripts ejecuten en modo headless (sin ventana)," -ForegroundColor White
    Write-Host "   Chrome DEBE estar instalado en el sistema." -ForegroundColor White
    Write-Host "`n📥 DESCARGA E INSTALACIÓN DE CHROME:" -ForegroundColor Yellow
    Write-Host "   1. Visita: https://www.google.com/chrome/" -ForegroundColor White
    Write-Host "   2. Descarga el instalador para Windows" -ForegroundColor White
    Write-Host "   3. Ejecuta el instalador y sigue las instrucciones" -ForegroundColor White
    Write-Host "   4. Ejecuta este script nuevamente para verificar" -ForegroundColor White
    Write-Host "`n⚠️  IMPORTANTE: Sin Chrome, los scripts NO funcionarán" -ForegroundColor Red
}

# ----------------------------------------------------------------------------
# PASO 6: VERIFICAR INSTALACIÓN CON TEST
# ----------------------------------------------------------------------------

Write-Host "`n📍 PASO 6: Ejecutando test de instalación..." -ForegroundColor Yellow

if (Test-Path "test_instalacion.py") {
    Write-Host "   Ejecutando test_instalacion.py...`n" -ForegroundColor White
    python test_instalacion.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Test de instalación completado" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  El test encontró algunos problemas, revisa los mensajes anteriores" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Archivo test_instalacion.py no encontrado, saltando verificación" -ForegroundColor Yellow
}

# ----------------------------------------------------------------------------
# RESUMEN FINAL
# ----------------------------------------------------------------------------

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "  RESUMEN DE INSTALACIÓN" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan

Write-Host "✅ Python instalado y configurado" -ForegroundColor Green
Write-Host "✅ pip actualizado" -ForegroundColor Green
Write-Host "✅ Dependencias Python instaladas:" -ForegroundColor Green
Write-Host "   - selenium" -ForegroundColor White
Write-Host "   - webdriver-manager" -ForegroundColor White
Write-Host "   - urllib3" -ForegroundColor White
Write-Host "   - certifi" -ForegroundColor White

if ($chromeFound) {
    Write-Host "✅ Google Chrome instalado" -ForegroundColor Green
} else {
    Write-Host "⚠️  Google Chrome NO instalado (OBLIGATORIO)" -ForegroundColor Red
}

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "  PRÓXIMOS PASOS" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan

if ($chromeFound) {
    Write-Host "🚀 El sistema está listo para usarse!" -ForegroundColor Green
    Write-Host "`n📝 Para ejecutar el orquestador:" -ForegroundColor Yellow
    Write-Host "   python Orquestador.py" -ForegroundColor White
    Write-Host "`n📚 Documentación disponible:" -ForegroundColor Yellow
    Write-Host "   - README.md" -ForegroundColor White
    Write-Host "   - GUIA_INSTALACION_WINDOWS_SERVER.md" -ForegroundColor White
    Write-Host "   - FAQ.md" -ForegroundColor White
} else {
    Write-Host "⚠️  Instala Google Chrome antes de continuar" -ForegroundColor Red
    Write-Host "   Descarga: https://www.google.com/chrome/" -ForegroundColor White
}

Write-Host "`n============================================================================`n" -ForegroundColor Cyan
