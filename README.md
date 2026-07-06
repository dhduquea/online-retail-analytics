# Análisis de Ventas — E-commerce (Online Retail)

Análisis exploratorio y de negocio sobre las transacciones de un retailer online del Reino Unido, con foco en KPIs comerciales, tendencias de ventas, desempeño de productos, distribución geográfica y segmentación de clientes (RFM), orientado a la toma de decisiones basada en datos.

## Fuente de datos

[UCI Machine Learning Repository — Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail) (datos abiertos).

Transacciones de un comercio online del Reino Unido entre el **01 dic 2010** y el **09 dic 2011**, con 541,909 registros.

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `Online_Retail.xlsx` | Dataset original en formato Excel |
| `Analisis_Ventas_Ecommerce.ipynb` | Notebook con el análisis completo (limpieza de datos, KPIs, tendencias, productos, geografía, segmentación RFM) |
| `reporte_ventas_ecommerce.html` | Reporte web interactivo con los resultados y gráficos |
| `reporte_ventas_ecommerce.js` | Script con la lógica de los gráficos del reporte web (debe estar en la misma carpeta que el `.html`) |
| `reporte_ejecutivo_ventas.md` | Resumen ejecutivo de una página con hallazgos y recomendaciones |
| `diccionario_datos.md` | Descripción de cada columna del dataset original y de las columnas derivadas del análisis |
| `app.py` | Dashboard interactivo en Streamlit con filtros dinámicos (fecha, país, segmento RFM) |
| `requirements.txt` | Librerías de Python necesarias para ejecutar el notebook y el dashboard |

## Cómo ejecutar el notebook

1. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Abre el notebook:

   ```bash
   jupyter notebook Analisis_Ventas_Ecommerce.ipynb
   ```

3. Ejecuta todas las celdas en orden (`Kernel > Restart & Run All`).

## Cómo ejecutar el dashboard interactivo (Streamlit)

1. Instala las dependencias (incluidas en `requirements.txt`):

   ```bash
   pip install -r requirements.txt
   ```

2. Estructura de carpetas esperada — `app.py` busca el Excel en una subcarpeta llamada `data`, ubicada junto a `app.py`:

   ```
   proyecto/
   ├── app.py
   └── data/
       └── Online_Retail.xlsx
   ```

   Si tu subcarpeta tiene otro nombre, ajusta la línea `DATA_PATH` al inicio de `app.py`.

3. Ejecuta el dashboard (funciona desde cualquier ubicación, no depende de la carpeta actual):

   ```bash
   streamlit run app.py
   ```

4. Se abrirá automáticamente en el navegador, normalmente en `http://localhost:8501`.

**Filtros interactivos disponibles:** rango de fechas, país, segmento de cliente (RFM) e inclusión de devoluciones/cancelaciones. Incluye pestañas para Tendencia, Productos, Geografía, Clientes (RFM) y Devoluciones, con tablas descargables en CSV.

## Cómo visualizar el reporte web

1. Asegúrate de que `reporte_ventas_ecommerce.html` y `reporte_ventas_ecommerce.js` estén en la **misma carpeta**.
2. Abre el archivo `.html` directamente en tu navegador (doble clic), o usa la extensión **Live Server** de VSCode para una vista con recarga automática.
3. Se requiere conexión a internet, ya que las fuentes y la librería de gráficos (Chart.js) se cargan desde un CDN externo.

## Resumen de hallazgos

- **Ingresos totales:** £10,666,684 · **Pedidos:** 19,960 · **Clientes:** 4,338 · **Ticket promedio:** £534.40
- Reino Unido concentra el **84.6%** de los ingresos; el resto del mundo (37 países) es aún un canal marginal.
- El **26.1%** de los clientes genera el **80%** de los ingresos (concentración tipo Pareto).
- Fuerte estacionalidad: pico de ventas en noviembre, sin actividad los sábados.
- Tasa de cancelación/devolución del **14.81%**, concentrada en pocas referencias.

El detalle completo de hallazgos y recomendaciones está en `reporte_ejecutivo_ventas.md`, en el reporte web y en el dashboard interactivo. Para el detalle de cada columna del dataset, ver `diccionario_datos.md`.

## Metodología

- Se excluyen del cálculo de ingresos las facturas canceladas (prefijo `C` en `InvoiceNo`) y las líneas con `Quantity` o `UnitPrice` ≤ 0.
- La segmentación de clientes utiliza el modelo **RFM** (Recencia, Frecuencia, Monetario) con puntuación por quintiles.
- Todas las cifras están expresadas en libras esterlinas (£).
