# 📋 Lógica del Descargador Diario - Análisis Completo

## 🎯 Resumen Ejecutivo

El `descargador_diariocopy.py` descarga **todas las facturas de AYER**, continuando desde el último registro exitoso.

---

## 🔍 ¿Qué Hace el Script?

### 1️⃣ Filtra por "Ayer"
```python
# Líneas 638-657
- Abre el filtro de fecha
- Selecciona la opción "Ayer"
- Muestra TODOS los registros (opción -1 o "all")
```

**Resultado:** Solo muestra facturas del día anterior.

---

### 2️⃣ Carga el Último DTE Procesado

```python
# Línea 720
ultimo_dte_cargado = cargar_ultimo_exitoso()
```

**Lee:** `descargas_diarias/ultimo_exitoso.json`

```json
{
  "fecha_actualizacion": "2025-11-13T09:30:00",
  "ultimo_dte": "000000000000125"
}
```

---

### 3️⃣ Determina Desde Dónde Empezar

#### **Escenario A: Hay último DTE registrado**

```
✅ Busca el DTE en la tabla con Ctrl+F
```

**Sub-escenario A.1: Lo encuentra en la tabla**
```
✅ Empieza desde el registro ANTERIOR al último procesado
📊 Ejemplo:
   - Último procesado: índice 10
   - Empieza desde: índice 9
   - Dirección: ⬆️ Hacia índice 0 (más recientes)
```

**Sub-escenario A.2: NO lo encuentra en la tabla**

**🆕 NUEVA VALIDACIÓN:**
```
1. Busca archivos con ese DTE en la carpeta descargas_diarias/
2. Si encuentra PDFs o JSONs:
   ✅ "Ya fue descargado correctamente"
   ✅ "Todos los registros de ayer están procesados"
   🎉 Sale del programa (exit 0)
   
3. Si NO encuentra archivos:
   ⚠️ "El DTE puede estar en otra fecha"
   📍 Empieza desde el final (procesa TODO de ayer)
```

#### **Escenario B: NO hay último DTE registrado**

```
📍 Primera ejecución o archivo borrado
📍 Empieza desde el final de la tabla (índice total_filas - 1)
```

---

### 4️⃣ Procesa los Registros

```python
# Líneas 776-830
for idx in range(indice_inicio, -1, -1):  # De indice_inicio hacia 0
    # Procesar cada registro
    # Guardar PDFs y JSONs
    # Actualizar ultimo_exitoso.json
```

**Dirección:** ⬆️ **Hacia registros más recientes** (índices menores)

**Ejemplo:**
```
Tabla con 50 registros de ayer:
├── Índice 0:  Factura más reciente   ← Meta final
├── Índice 1:  Segunda más reciente
├── ...
├── Índice 48: Segunda más antigua
└── Índice 49: Factura más antigua    ← Punto de partida (si es primera vez)

Procesamiento:
49 → 48 → 47 → ... → 2 → 1 → 0
```

---

### 5️⃣ Guarda Cada Éxito

```python
# Línea 507
if dte:
    guardar_ultimo_exitoso(dte)
```

**Actualiza inmediatamente** `ultimo_exitoso.json` después de cada descarga exitosa.

---

## 🎯 Escenarios de Uso

### **Escenario 1: Primera Ejecución del Día**

```
📅 Día: 13 de noviembre
🕐 Hora: 18:00 (programada)

Estado inicial:
- ultimo_exitoso.json: {"ultimo_dte": "000000000000125"} (del día anterior)
- Registros de ayer: 10 facturas nuevas

Proceso:
1. ✅ Filtra por "Ayer" (12 de noviembre)
2. 🔍 Busca DTE 000000000000125
3. ❌ NO lo encuentra (es del 11 de noviembre)
4. 🔍 Busca archivos con ese DTE
5. ✅ Los encuentra en descargas_diarias/
6. 🎉 "Todos los registros ya procesados, saliendo..."
7. ✅ Sale sin procesar nada

Resultado: No descarga nada (correcto, ayer ya fue procesado)
```

---

### **Escenario 2: Interrupción Parcial**

```
📅 Día: 13 de noviembre
🕐 Hora: 18:00

Estado inicial:
- ultimo_exitoso.json: {"ultimo_dte": "000000000000130"}
- Ayer se interrumpió después de descargar 5 de 10 facturas

Proceso:
1. ✅ Filtra por "Ayer" (12 de noviembre)
2. 🔍 Busca DTE 000000000000130
3. ✅ Lo encuentra en índice 5
4. 📍 Empieza desde índice 4 (anterior)
5. ⬆️ Procesa: 4 → 3 → 2 → 1 → 0
6. 💾 Descarga las 5 facturas restantes

Resultado: Completa la descarga de ayer sin duplicar
```

---

### **Escenario 3: Primera Vez (Sin último_exitoso.json)**

```
📅 Día: 13 de noviembre
🕐 Hora: 18:00

Estado inicial:
- NO existe ultimo_exitoso.json
- Registros de ayer: 10 facturas

Proceso:
1. ✅ Filtra por "Ayer" (12 de noviembre)
2. 📍 No hay último DTE registrado
3. 📍 Empieza desde índice 9 (final)
4. ⬆️ Procesa: 9 → 8 → 7 → ... → 0
5. 💾 Descarga todas las 10 facturas

Resultado: Descarga completa de ayer
```

---

## 🔄 Flujo de Decisión

```
INICIO
  │
  ├─ Filtrar por "Ayer"
  │
  ├─ ¿Existe ultimo_exitoso.json?
  │   │
  │   ├─ NO → Empezar desde el final (índice más alto)
  │   │
  │   └─ SÍ → Cargar último DTE
  │           │
  │           ├─ ¿Se encuentra en tabla de ayer?
  │           │   │
  │           │   ├─ SÍ → Empezar desde registro anterior
  │           │   │
  │           │   └─ NO → ¿Existe archivo con ese DTE?
  │           │           │
  │           │           ├─ SÍ → 🎉 Ya procesado, SALIR
  │           │           │
  │           │           └─ NO → Empezar desde el final
  │
  ├─ Procesar registros (del final hacia el inicio)
  │   │
  │   ├─ Por cada registro:
  │   │   ├─ Descargar PDF
  │   │   ├─ Descargar JSON
  │   │   └─ Guardar ultimo_exitoso.json
  │
  └─ FIN
```

---

## 📊 Validaciones Implementadas

### ✅ Validación 1: Último DTE ya procesado
```python
if archivos_pdf or archivos_json:
    print("✅ Todos los registros de ayer ya están procesados")
    exit(0)
```

**Evita:** Reprocesar facturas ya descargadas cuando el último DTE no aparece en la tabla de ayer.

### ✅ Validación 2: Sin registros nuevos
```python
if indice_inicio < 0:
    print("⚠️ No hay registros nuevos para procesar")
    exit(0)
```

**Evita:** Errores cuando el índice calculado es negativo.

### ✅ Validación 3: Tabla vacía
```python
if total_filas == 0:
    print("⚠️ No hay registros para procesar de ayer")
    exit(0)
```

**Evita:** Procesar cuando no hay facturas de ayer.

---

## 📁 Archivos Generados

```
descargas_diarias/
├── hermaco-DTE-01-M001P001-000000000000125.pdf
├── hermaco-DTE-01-M001P001-000000000000125.json
├── hermaco-DTE-01-M001P001-000000000000126.pdf
├── hermaco-DTE-01-M001P001-000000000000126.json
├── ultimo_exitoso.json                          ← Rastrea progreso
└── reporte_fallidos_20251113_180545.json        ← Si hubo errores
```

---

## 🎯 Garantías del Script

| Garantía | ✅ Cumple | Explicación |
|----------|-----------|-------------|
| Filtra solo facturas de ayer | ✅ | Usa opción "Ayer" del filtro |
| Descarga TODAS las de ayer | ✅ | Selecciona "Mostrar todos" |
| No duplica descargas | ✅ | Valida archivo existe antes de reprocesar |
| Continúa desde último exitoso | ✅ | Busca último DTE y empieza desde ahí |
| Detecta cuando ya terminó | ✅ | Sale si encuentra archivos del último DTE |
| Maneja interrupciones | ✅ | Guarda progreso después de cada descarga |

---

## 🚀 Ejecución Programada

### En Programador de Tareas:
```
Hora: 18:00 (diariamente)
Script: descargador_diariocopy.py
Directorio: J:\Henri\extractor-facturas-selenium-hermaco-main\...

Comportamiento esperado:
- 18:00 → Descarga facturas de AYER (12 nov)
- Si ya se ejecutó hoy → Sale inmediatamente (0 descargas)
- Si se interrumpió → Completa las faltantes
- Si es primera vez → Descarga todas
```

---

## ⚡ Optimizaciones

### 1. Detección Inteligente
- ✅ Verifica archivos locales antes de reprocesar
- ✅ Sale temprano si no hay trabajo que hacer

### 2. Procesamiento Eficiente
- ✅ Procesa de más antiguo a más reciente (preserva orden)
- ✅ Actualiza progreso después de cada éxito

### 3. Manejo de Errores
- ✅ Guarda reportes de fallos
- ✅ Continúa con siguiente registro si uno falla
- ✅ Cierra ventanas huérfanas

---

## 📝 Notas Importantes

1. **"Ayer" siempre se refiere al día calendario anterior** (no últimas 24 horas)
2. **El script debe ejecutarse diariamente** para evitar acumulación
3. **Si se ejecuta 2+ veces al día**, solo la primera hará descargas
4. **El archivo `ultimo_exitoso.json` NO debe borrarse** manualmente
5. **Funciona en modo headless** (sin ventana visible)

---

**Versión:** 2.0  
**Última actualización:** 13 de noviembre de 2025  
**Mejora:** Validación de archivos existentes antes de reprocesar
