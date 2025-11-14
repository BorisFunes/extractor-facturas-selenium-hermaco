# ❓ PREGUNTAS FRECUENTES (FAQ)

## 🌐 Sobre Google Chrome e Instalación

### ❓ ¿Necesito instalar Google Chrome si los scripts ejecutan en modo headless?

**✅ SÍ, Google Chrome es OBLIGATORIO**, incluso en modo headless.

**Explicación:**
- **Modo headless** significa que el navegador NO muestra ventana visible
- **PERO** el navegador Chrome sigue ejecutándose en segundo plano
- Selenium necesita que Chrome esté instalado en el sistema para poder controlarlo
- El modo headless es solo una opción de configuración, no reemplaza la instalación de Chrome

**Analogía:**
```
Modo headless = Conducir un auto con las ventanas polarizadas negras
- El auto (Chrome) debe existir y funcionar
- Solo no puedes ver hacia afuera (sin interfaz gráfica)
- Pero el motor, volante, frenos siguen ahí
```

### ❓ ¿Qué pasa si NO instalo Chrome?

**❌ Los scripts fallarán inmediatamente** con errores como:

```
selenium.common.exceptions.SessionNotCreatedException: 
Message: session not created: Chrome failed to start
```

o

```
WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

### ❓ ¿Necesito instalar ChromeDriver manualmente?

**✅ NO**, ChromeDriver se descarga automáticamente.

- El proyecto usa `webdriver-manager`
- Esta librería descarga la versión correcta de ChromeDriver automáticamente
- Se actualiza solo cuando Chrome se actualiza

**Lo que SÍ necesitas:**
- ✅ Chrome instalado
- ✅ `webdriver-manager` instalado (viene en requirements.txt)

**Lo que NO necesitas:**
- ❌ Descargar ChromeDriver manualmente
- ❌ Configurar PATH para ChromeDriver
- ❌ Preocuparte por versiones de ChromeDriver

---

## 📊 Sobre el Reporte JSON

### ❓ ¿Qué contiene el reporte JSON generado?

El archivo `reporte_ejecucion_YYYYMMDD_HHMMSS.json` contiene:

1. **Información general:**
   - Fecha y hora de inicio/fin
   - Duración total de la ejecución
   - Resumen de éxitos/fallos

2. **Por cada script ejecutado:**
   - Nombre y archivo del script
   - Estado (exitoso/fallido)
   - Duración de ejecución
   - Cantidad de archivos descargados (PDFs y JSONs)
   - Detalles del error (si falló)

3. **Estadísticas:**
   - Tasa de éxito (%)
   - Total de scripts ejecutados
   - Conteo de exitosos y fallidos

**Ver ejemplo completo en:** `ejemplo_reporte_ejecucion.json`

### ❓ ¿Dónde se guarda el reporte JSON?

- **Ubicación:** En el mismo directorio del proyecto (raíz)
- **Nombre:** `reporte_ejecucion_YYYYMMDD_HHMMSS.json`
- **Ejemplo:** `reporte_ejecucion_20251111_080000.json`

### ❓ ¿Se genera un reporte aunque falle algún script?

**✅ SÍ**, el reporte siempre se genera al final, independientemente de si los scripts tuvieron éxito o no.

- Si un script falla, se marca como "fallido" con el mensaje de error
- El orquestador continúa con los siguientes scripts
- Al final se genera el reporte completo con todos los resultados

### ❓ ¿Cómo sé cuántos archivos se descargaron realmente?

El reporte JSON cuenta automáticamente:

```json
"archivos_descargados": {
  "pdfs": 45,      // Archivos PDF descargados
  "jsons": 45,     // Archivos JSON descargados
  "total": 90      // Total de archivos
}
```

**NOTA:** Excluye archivos de tracking como:
- `ultimo_exitoso.json`
- `01descargados.json`
- `02ignorados.json`
- `reporte_fallidos_*.json`

### ❓ ¿Puedo usar el JSON para monitoreo automático?

**✅ SÍ, absolutamente**. El JSON está diseñado para integración:

**Casos de uso:**
1. **Alertas por email:** Si `resumen.fallidos > 0`, enviar alerta
2. **Dashboard:** Leer el JSON y mostrar estadísticas
3. **Base de datos:** Importar datos del JSON para histórico
4. **Scripts de análisis:** Procesar múltiples reportes para tendencias
5. **Integración con sistemas de monitoreo:** Zabbix, Nagios, etc.

**Ejemplo de script de monitoreo:**
```python
import json

with open('reporte_ejecucion_20251111_080000.json', 'r') as f:
    reporte = json.load(f)

if reporte['resumen']['fallidos'] > 0:
    print("⚠️ ALERTA: Hubo fallos en la ejecución")
    # Enviar email, notificación, etc.
else:
    print("✅ Ejecución exitosa")
```

---

## ⏰ Sobre Ejecución Programada

### ❓ ¿Puedo programar la ejecución en Windows Server sin interfaz gráfica?

**✅ SÍ, completamente posible**.

**Opciones:**
1. **Task Scheduler de Windows** (recomendado)
   - No requiere sesión activa
   - Funciona en modo headless
   - Ver guía en: `GUIA_INSTALACION_WINDOWS_SERVER.md`

2. **Script PowerShell programado**
3. **Servicio de Windows**
4. **Tareas CRON (si usas WSL)**

### ❓ ¿La tarea programada funciona sin que nadie esté logueado?

**✅ SÍ**, si configuras correctamente:

En Task Scheduler:
- ✅ Marca: "Ejecutar tanto si el usuario inició sesión o no"
- ✅ Marca: "Ejecutar con los privilegios más altos"
- ✅ NO marques: "Ejecutar solo cuando el usuario haya iniciado sesión"

### ❓ ¿Cuánto tiempo toma una ejecución completa?

**Varía según la cantidad de documentos**, pero típicamente:

- **Facturas de ayer:** 3-8 minutos
- **Gastos:** 5-15 minutos
- **Remisiones:** 4-10 minutos

**Total estimado:** 12-35 minutos

**Factores que influyen:**
- Cantidad de documentos a descargar
- Velocidad de internet
- Carga del servidor ERP
- Recursos del servidor (RAM, CPU)

---

## 🔧 Solución de Problemas

### ❓ Error: "Chrome failed to start"

**Causa:** Chrome no está instalado o no se puede ejecutar

**Solución:**
1. Verifica que Chrome esté instalado: `C:\Program Files\Google\Chrome\Application\chrome.exe`
2. Si no está, instala desde: https://www.google.com/chrome/
3. Reinicia el servidor después de instalar

### ❓ Error: "ModuleNotFoundError: No module named 'selenium'"

**Causa:** Dependencias no instaladas

**Solución:**
```powershell
pip install -r requirements.txt
```

### ❓ Los archivos no se descargan

**Verificaciones:**
1. ✅ ¿Chrome está instalado?
2. ✅ ¿Las carpetas de descarga existen?
3. ✅ ¿Hay permisos de escritura en las carpetas?
4. ✅ ¿Las credenciales son correctas?
5. ✅ ¿El servidor ERP está accesible?

### ❓ El script se queda "colgado"

**Posibles causas:**
1. Conexión a internet lenta o inestable
2. El servidor ERP está lento
3. Hay un modal o popup inesperado en el ERP

**Solución temporal:**
- Presiona `Ctrl+C` para detener
- Revisa los logs
- Ejecuta de nuevo

**Solución permanente:**
- Aumentar los timeouts en el código
- Mejorar la conexión a internet
- Contactar al equipo de soporte del ERP

---

## 📁 Sobre Archivos y Estructura

### ❓ ¿Puedo borrar los archivos JSON de tracking?

**⚠️ NO recomendado** mientras el sistema esté en uso.

**Archivos de tracking:**
- `ultimo_exitoso.json` - Guarda el progreso para continuar desde donde quedó
- `01descargados.json` - Evita descargar duplicados
- `02ignorados.json` - Registra documentos ignorados

**Si los borras:**
- El sistema empezará desde cero
- Puede re-descargar documentos ya descargados
- Perderás el historial de ignorados

**Cuándo sí puedes borrarlos:**
- Si quieres forzar una descarga completa desde cero
- Si hay problemas de corrupción de datos
- Si quieres "resetear" el sistema

### ❓ ¿Dónde se guardan los archivos descargados?

```
proyecto/
├── descargas_diarias/      # Facturas de ayer
├── descargas_gastos/        # Gastos
└── descargas_remisiones/    # Remisiones
```

**Cada carpeta contiene:**
- `*.pdf` - Documentos en PDF
- `*.json` - Datos del documento en JSON
- Archivos de tracking

### ❓ ¿Los reportes de ejecución se acumulan?

**✅ SÍ**, cada ejecución genera un nuevo archivo:

```
reporte_ejecucion_20251111_080000.json
reporte_ejecucion_20251111_200000.json
reporte_ejecucion_20251112_080000.json
...
```

**Recomendación:**
- Crear un proceso para archivar reportes antiguos
- O borrar reportes después de X días
- O importarlos a una base de datos

**Script de limpieza (ejemplo):**
```powershell
# Borrar reportes más antiguos de 30 días
Get-ChildItem -Path . -Filter "reporte_ejecucion_*.json" | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
  Remove-Item
```

---

## 🔒 Sobre Seguridad

### ❓ ¿Las credenciales están seguras?

**⚠️ ADVERTENCIA:** Actualmente las credenciales están hardcodeadas en los scripts.

**Credenciales actuales:**
- Usuario: `Henri`
- Contraseña: `Bajmut`

**Riesgos:**
- Cualquiera con acceso al código puede verlas
- Se guardan en texto plano

**Mejoras recomendadas para producción:**
1. Usar variables de entorno
2. Usar un archivo de configuración cifrado
3. Usar Windows Credential Manager
4. Usar Azure Key Vault (si está en la nube)

**Ejemplo con variables de entorno:**
```python
import os
username = os.getenv('ERP_USERNAME')
password = os.getenv('ERP_PASSWORD')
```

### ❓ ¿Puedo cambiar las credenciales?

**✅ SÍ**, pero debes hacerlo en **3 archivos**:

1. `descargador_diario copy.py`
2. `descargadordegastos.py`
3. `descargadorderemisiones.py`

Busca estas líneas y cámbialas:
```python
username_input.send_keys("Henri")
password_input.send_keys("Bajmut")
```

---

## 📞 Soporte

**¿Más preguntas?**

1. Consulta: `GUIA_INSTALACION_WINDOWS_SERVER.md`
2. Consulta: `README.md`
3. Ejecuta: `python test_instalacion.py`
4. Revisa los reportes JSON generados
5. Contacta al desarrollador del sistema

---

**Última actualización:** Noviembre 2025  
**Versión:** 1.1
