# Diccionario de Datos — Online Retail Dataset

Descripción de las columnas del archivo original `Online_Retail.xlsx`, obtenido de [UCI Machine Learning Repository — Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail) (datos abiertos).

**Registros totales:** 541,909 · **Periodo:** 01 dic 2010 – 09 dic 2011

---

| Columna | Tipo | Nulos | Descripción | Reglas de negocio / notas |
|---|---|---|---|---|
| `InvoiceNo` | texto (`object`) | 0 | Número de factura. Identifica de forma única cada transacción/pedido. | Si comienza con la letra **"C"** (ej. `C536379`), indica que la factura fue **cancelada** (devolución). Estas líneas tienen `Quantity` negativa. |
| `StockCode` | texto (`object`) | 0 | Código de producto (SKU). Identifica de forma única cada referencia del catálogo. | Algunos códigos no corresponden a productos físicos, por ejemplo `POST` (gastos de envío) o `M`/`MANUAL` (ajustes manuales). |
| `Description` | texto (`object`) | 1,454 | Nombre/descripción del producto. | Puede estar vacío cuando el `StockCode` no es un producto estándar o por errores de captura. No es única por `StockCode` en el 100% de los casos (pequeñas variaciones de texto). |
| `Quantity` | entero (`int64`) | 0 | Cantidad de unidades vendidas en esa línea de la factura. | **Valores negativos** corresponden a devoluciones o cancelaciones (coinciden en general con `InvoiceNo` que empieza en "C"). El análisis de ventas excluye `Quantity <= 0`. |
| `InvoiceDate` | fecha-hora (`datetime`) | 0 | Fecha y hora en que se generó la factura. | Rango: 2010-12-01 08:26 a 2011-12-09 12:50. Se usa para derivar año, mes, día de la semana y hora en el análisis. |
| `UnitPrice` | decimal (`float64`) | 0 | Precio unitario del producto, en libras esterlinas (£). | Existen valores en **cero** (ajustes, promociones o errores) y algunos **negativos** (2 casos, ajustes contables). El análisis de ventas excluye `UnitPrice <= 0`. |
| `CustomerID` | decimal (`float64`) | 135,080 (24.9%) | Identificador único del cliente. | Los nulos suelen corresponder a compras como invitado o transacciones administrativas; se excluyen del análisis de clientes (RFM), pero se mantienen en el análisis general de ventas. |
| `Country` | texto (`str`) | 0 | País de envío/facturación del cliente. | 38 valores únicos. Incluye `"United Kingdom"`, `"EIRE"` (Irlanda), `"Unspecified"` y `"European Community"` como categorías especiales, además de los países convencionales. |

---

## Columnas derivadas creadas durante el análisis

| Columna | Se calcula como | Uso |
|---|---|---|
| `EsCancelacion` | `InvoiceNo` empieza con `"C"` | Marca las facturas canceladas/devueltas |
| `ImporteTotal` | `Quantity × UnitPrice` | Valor monetario de cada línea de venta |
| `AnioMes` | Año-mes de `InvoiceDate` | Agregación de ventas mensuales |
| `DiaSemana` | Día de la semana de `InvoiceDate` | Análisis de estacionalidad semanal |
| `Hora` | Hora de `InvoiceDate` | Análisis de estacionalidad horaria |
| `Recencia` (RFM) | Días desde la última compra del cliente hasta la fecha de referencia | Segmentación RFM |
| `Frecuencia` (RFM) | Nº de facturas únicas por cliente | Segmentación RFM |
| `Monetario` (RFM) | Suma de `ImporteTotal` por cliente | Segmentación RFM |

## Filtros aplicados para el análisis de ventas

El dataset limpio usado en la mayoría de los cálculos de ingresos (`df_ventas`) excluye:
1. Facturas canceladas (`EsCancelacion == True`)
2. Líneas con `Quantity <= 0`
3. Líneas con `UnitPrice <= 0`

El análisis de devoluciones/cancelaciones utiliza específicamente el subconjunto excluido (`EsCancelacion == True`) para cuantificar su impacto.
