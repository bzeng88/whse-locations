# 🗺️ Streamlit Warehouse Mapper (v2)

This Streamlit app maps warehouse locations from a CSV upload and lets you customize the color (hex code) for each plotted point.
Basemaps: **CARTO** and **OpenStreetMap**.

## ✅ CSV Format
- Column A: latitude
- Column B: longitude
- Optional: `color` column with hex values (e.g., `#FF0000`).

## ▶️ Quickstart (Local)
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 🧪 Sample Data
See `sample_data/warehouses.csv`.

## 🗺️ Basemap Sources
- CARTO: `https://basemaps.cartocdn.com/*`
- OpenStreetMap: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`

> Attribution: © OpenStreetMap contributors; © CARTO basemaps.
