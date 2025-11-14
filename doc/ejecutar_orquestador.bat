@echo off
REM ============================================
REM EJECUTOR DEL ORQUESTADOR - HERMACO ERP
REM ============================================

echo.
echo ============================================
echo  ORQUESTADOR DE DESCARGAS - HERMACO ERP
echo ============================================
echo.
echo Iniciando ejecucion...
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Mostrar directorio actual
echo Directorio de trabajo: %CD%
echo.

REM Ejecutar el orquestador con Python
REM Ruta confirmada de Python en Windows Server
"C:\Program Files\Python314\python.exe" Orquestador.py

REM Verificar el resultado
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo  EJECUCION COMPLETADA EXITOSAMENTE
    echo ============================================
) else (
    echo.
    echo ============================================
    echo  ERROR EN LA EJECUCION
    echo  Codigo de error: %ERRORLEVEL%
    echo ============================================
)

REM Descomentar la siguiente linea si quieres que se pause al ejecutar manualmente
REM pause

exit /b %ERRORLEVEL%
