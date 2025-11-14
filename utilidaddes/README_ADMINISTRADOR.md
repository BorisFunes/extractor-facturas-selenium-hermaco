# 📋 ADMINISTRADOR DE FACTURAS - HERMACO

## 🎯 Descripción

El **Administrador de Facturas** es un script que organiza y distribuye automáticamente los archivos descargados (PDFs y JSONs) a las carpetas correspondientes según la sucursal y tipo de documento.

## ✨ Características Nuevas

### 🔧 Configuración Flexible de Rutas

El script ahora te permite especificar:

1. **Ruta de carpeta padre de ORIGEN**: Donde busca las carpetas de descargas
2. **Ruta de carpeta de DESTINO**: Donde distribuirá los archivos clasificados

### 📂 Estructura Esperada

#### Carpetas de Origen (Dentro de la carpeta padre)
El script busca automáticamente estas 3 carpetas:
- `descargas_diarias` - Facturas del día anterior (requiere clasificación)
- `descargas_gastos` - Gastos pagados (copia directa, sin clasificación)
- `descargas_remisiones` - Notas de remisión (copia directa, sin clasificación)

#### Carpetas de Destino (Se crean si no existen)
**Para archivos clasificados:**
- `SA` - Santa Ana
- `SS` - San Salvador  
- `SM` - San Miguel
- `notas_de_credito` - Notas de crédito

**Para archivos sin clasificar (copia directa):**
- `descargas_remisiones` - Remisiones (copia 1:1 desde origen)
- `descargas_gastos` - Gastos (copia 1:1 desde origen)

## 🚀 Cómo Usar

### 1. Ejecutar el Script

```powershell
cd utilidaddes
python administrador.py
```

### 2. Configuración Inicial

El script te pedirá dos rutas:

#### A. Carpeta Padre de Origen
```
📂 CARPETA DE ORIGEN (Padre)
   Esta carpeta debe contener las subcarpetas:
   - descargas_diarias
   - descargas_gastos
   - descargas_remisiones

Ingrese la ruta de la carpeta padre de origen: 
```

**Ejemplo:**
```
J:\Henri\extractor-facturas-selenium-hermaco-main\extractor-facturas-selenium-hermaco-main
```

El script verificará que existan las 3 carpetas dentro.

#### B. Carpeta de Destino
```
📂 CARPETA DE DESTINO
   Esta carpeta debe contener (o se crearán) las subcarpetas:
   - notas_de_credito
   - SA
   - SS
   - SM
   - descargas_remisiones
   - descargas_gastos

Ingrese la ruta de la carpeta de destino:
```

**Ejemplo:**
```
J:\Henri\FACTURAS_CLASIFICADAS
```

### 3. Verificación Automática

El script verificará y creará la estructura:
```
   ✗ No encontrada: notas_de_credito
   ✗ No encontrada: SA
   ✗ No encontrada: SS
   ✗ No encontrada: SM
   ✗ No encontrada: descargas_remisiones
   ✗ No encontrada: descargas_gastos

⚠️  Faltan carpetas de destino, se creará una nueva estructura

   ✓ Creada: notas_de_credito
   ✓ Creada: SA
   ✓ Creada: SS
   ✓ Creada: SM
   ✓ Creada: descargas_remisiones
   ✓ Creada: descargas_gastos
```

### 3. Menú de Opciones

Una vez configurado, verás el menú:

```
======================================================================
ADMINISTRADOR DE FACTURAS - HERMACO
======================================================================

Seleccione una opción:
  1. Distribuir archivos (mover)
  2. Distribuir archivos (copiar)
  3. Generar reporte sin mover archivos
  4. Reconfigurar rutas
  5. Salir
----------------------------------------------------------------------
```

## 📊 Opciones del Menú

### 1️⃣ Distribuir archivos (mover)
- **Mueve** los archivos de las carpetas origen a las carpetas destino
- Los archivos originales **desaparecen** de las carpetas origen
- ✅ Recomendado para uso normal

### 2️⃣ Distribuir archivos (copiar)
- **Copia** los archivos a las carpetas destino
- Los archivos originales **permanecen** en las carpetas origen
- ✅ Útil para respaldo o pruebas

### 3️⃣ Generar reporte sin mover archivos
- Solo **muestra** dónde se distribuiría cada archivo
- **No mueve ni copia** nada
- ✅ Perfecto para verificar antes de ejecutar

### 4️⃣ Reconfigurar rutas
- Permite cambiar las rutas de origen y destino
- Útil si cambias de servidor o carpetas

### 5️⃣ Salir
- Cierra el programa

## 🔍 Lógica de Clasificación

El script maneja dos tipos de procesamiento:

### 📋 Tipo 1: Archivos CON Clasificación (descargas_diarias)
Los archivos de `descargas_diarias` se clasifican según el **prefijo** en el nombre del archivo:

#### Por Sucursal (Primeros 4 caracteres)
- **M001xxxx** → `SA` (Santa Ana)
- **S001xxxx** → `SS` (San Salvador)
- **S002xxxx** → `SM` (San Miguel)
- **M002xxxx** → `SM` (San Miguel)
- **M003xxxx** → `SS` (San Salvador)

#### Por Tipo de Documento
- **DTE-05-M001xxxx** → `notas_de_credito` (Notas de crédito)

**Nota:** Los últimos 4 dígitos del prefijo pueden variar sin afectar la clasificación.

**Ejemplo:**
- `hermaco-DTE-01-M001P001-000000000000029.pdf` → Carpeta `SA`
- `hermaco-DTE-01-S001P001-000000000000015.pdf` → Carpeta `SS`
- `hermaco-DTE-05-M001P001-000000000000003.pdf` → Carpeta `notas_de_credito`

### 📦 Tipo 2: Archivos SIN Clasificación (Copia Directa)
Los archivos de estas carpetas se copian/mueven **directamente** sin analizar su contenido:

- **`descargas_remisiones`** → Se copian a carpeta `descargas_remisiones` en destino
- **`descargas_gastos`** → Se copian a carpeta `descargas_gastos` en destino

**No se analiza el prefijo**, simplemente se trasladan manteniendo su ubicación relativa.

## 📄 Archivos Procesados

### ✅ Se procesan:
- ✓ Archivos `.pdf`
- ✓ Archivos `.json` (excepto reportes)

### ❌ Se ignoran:
- Archivos JSON de control:
  - `registros_fallidos*.json`
  - `ultimo_*.json`
  - `duplicados*.json`
  - `sin_correlacion*.json`
  - `01descargados.json`
  - `02ignorados.json`

## 📊 Reporte Generado

Después de cada distribución, se genera un archivo de reporte:

**Nombre:** `reporte_distribucion_YYYYMMDD_HHMMSS.txt`

**Contiene:**
- Fecha y hora de ejecución
- Modo usado (mover/copiar/reporte)
- Carpetas origen y destino
- Estadísticas por sucursal (archivos clasificados)
- Estadísticas de remisiones y gastos (copia directa)
- Lista de archivos sin clasificar
- Prefijos no reconocidos
- Reglas de clasificación aplicadas

## ⚠️ Verificaciones Automáticas

### Al Configurar Origen:
- ✓ Verifica que la ruta exista
- ✓ Busca las 3 carpetas requeridas
- ⚠️ Advierte si falta alguna carpeta
- ❓ Pregunta si deseas continuar de todas formas

### Al Configurar Destino:
- ✓ Verifica que la ruta exista (o la crea)
- ✓ Busca las carpetas de destino
- ⚠️ **Si faltan carpetas:** Muestra mensaje y las crea automáticamente
- ✅ Crea la estructura completa si no existe

## 💡 Ejemplos de Uso

### Caso 1: Primera Ejecución
```powershell
python administrador.py

# Te pide carpeta origen
> J:\Henri\extractor-facturas-selenium-hermaco-main\extractor-facturas-selenium-hermaco-main

   ✓ Encontrada: descargas_diarias
   ✓ Encontrada: descargas_gastos
   ✓ Encontrada: descargas_remisiones

# Te pide carpeta destino
> J:\Henri\FACTURAS_CLASIFICADAS

   ✗ No encontrada: notas_de_credito
   ✗ No encontrada: SA
   ✗ No encontrada: SS
   ✗ No encontrada: SM
   ✗ No encontrada: descargas_remisiones
   ✗ No encontrada: descargas_gastos

⚠️  Faltan carpetas de destino, se creará una nueva estructura

   ✓ Creada: notas_de_credito
   ✓ Creada: SA
   ✓ Creada: SS
   ✓ Creada: SM
   ✓ Creada: descargas_remisiones
   ✓ Creada: descargas_gastos

✓ Estructura de carpetas creada correctamente
```

### Caso 2: Verificar Antes de Mover
```
Opción: 3 (Generar reporte)
- Muestra dónde iría cada archivo
- No mueve nada
- Verificas que todo esté correcto
```

### Caso 3: Distribuir Archivos
```
Opción: 1 (Distribuir archivos - mover)
- Confirmas la operación
- Los archivos se mueven a sus carpetas
- Se genera el reporte
```

## 🔧 Solución de Problemas

### "❌ No hay carpetas de origen configuradas"
**Solución:** Usa la opción 4 para reconfigurar las rutas

### "⚠️ Faltan X carpeta(s)"
**Solución:** 
- Verifica que las carpetas existan en la ruta indicada
- O confirma para continuar sin ellas

### "⚠️ Prefijo no reconocido"
**Solución:**
- Los archivos quedan sin clasificar
- Revisa el reporte generado
- Si es un prefijo nuevo, contacta al administrador para agregar la regla

### "❌ Error al crear carpeta"
**Solución:**
- Verifica permisos de escritura
- Verifica que la ruta sea válida
- Ejecuta como administrador si es necesario

## 📝 Notas Importantes

1. **No requiere permisos de administrador** (en la mayoría de casos)
2. **Procesa todas las carpetas origen** en una sola ejecución
3. **Crea carpetas automáticamente** si no existen en el destino
4. **Genera reportes detallados** de cada operación
5. **Permite reconfigurar** las rutas en cualquier momento
6. **Maneja emojis correctamente** en Windows Server
7. **Dos modos de procesamiento:**
   - 📋 Con clasificación: `descargas_diarias` (analiza prefijos)
   - 📦 Sin clasificación: `descargas_remisiones` y `descargas_gastos` (copia directa)

## 🎨 Codificación UTF-8

El script incluye configuración para manejar correctamente emojis en Windows:

```python
# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

---

**Versión:** 2.0  
**Última actualización:** 13 de noviembre de 2025  
**Características:** Rutas configurables, creación automática de estructura
