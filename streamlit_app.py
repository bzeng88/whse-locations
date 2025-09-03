import streamlit as st
import pandas as pd
import pydeck as pdk
import random

st.set_page_config(page_title="Warehouse Mapper", page_icon="🗺️", layout="wide")

st.title("🗺️ Warehouse Mapper")
st.caption("Basemaps: CARTO + OpenStreetMap. Upload a CSV: Column A = latitude, Column B = longitude.")

with st.sidebar:
    st.header("Upload")
    uploaded = st.file_uploader("Upload CSV (lat in col A, lon in col B)", type=["csv"])
    use_sample = st.checkbox("Use sample data instead", value=not uploaded)

def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.shape[1] < 2:
        raise ValueError("CSV must have at least two columns (latitude in column A and longitude in column B).")
    cols = list(df.columns)
    df = df.rename(columns={cols[0]: "latitude", cols[1]: "longitude"})
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
    if "color" not in df.columns:
        df["color"] = None
    return df[["latitude", "longitude", "color"]]

if use_sample and not uploaded:
    df = pd.read_csv("sample_data/warehouses.csv")
    df = _prepare_dataframe(df)
else:
    if uploaded:
        df_raw = pd.read_csv(uploaded, header=None)
        if df_raw.shape[1] < 2:
            uploaded.seek(0)
            df_raw = pd.read_csv(uploaded)
        df = _prepare_dataframe(df_raw)
    else:
        df = pd.DataFrame(columns=["latitude", "longitude", "color"])

st.subheader("Step 1 — Assign Colors")
st.write("Edit the color hex codes (#RRGGBB) for each warehouse point.")

def _random_color_hex():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

if df.shape[0] > 0:
    if df["color"].isna().all() or (df["color"] == "").all():
        df["color"] = [_random_color_hex() for _ in range(len(df))]

edited = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
)

st.download_button(
    "⬇️ Download edited CSV",
    data=edited.to_csv(index=False).encode("utf-8"),
    file_name="warehouses_edited.csv",
    mime="text/csv",
)

st.markdown("---")
st.subheader("Step 2 — Basemap & Styling")

basemap = st.selectbox(
    "Choose basemap",
    ["CARTO Light", "CARTO Dark", "OpenStreetMap Standard"],
    index=0,
)

point_radius = st.slider("Point radius (meters)", min_value=100, max_value=80000, value=2000, step=100)

def hex_to_rgb(h):
    if not isinstance(h, str) or not h.startswith("#") or len(h) not in (4, 7):
        return [0, 122, 204, 200]
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join([c*2 for c in h])
    try:
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return [r, g, b, 200]
    except Exception:
        return [0, 122, 204, 200]

if edited.shape[0] > 0:
    edited = edited.copy()
    edited["fill_rgba"] = edited["color"].apply(hex_to_rgb)

if basemap == "CARTO Light":
    tile_url = "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
elif basemap == "CARTO Dark":
    tile_url = "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
else:
    tile_url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

tile_layer = pdk.Layer(
    "TileLayer",
    data=tile_url,
    min_zoom=0,
    max_zoom=20,
    tile_size=256,
)

scatter = pdk.Layer(
    "ScatterplotLayer",
    data=edited if edited.shape[0] > 0 else pd.DataFrame(columns=["latitude", "longitude", "fill_rgba"]),
    get_position="[longitude, latitude]",
    get_fill_color="fill_rgba",
    get_radius=point_radius,
    pickable=True,
    auto_highlight=True,
)

if edited.shape[0] > 0:
    center_lat = float(edited["latitude"].mean())
    center_lon = float(edited["longitude"].mean())
    zoom = 4 if edited.shape[0] > 1 else 8
else:
    center_lat, center_lon, zoom = 39.5, -98.35, 3

view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom, bearing=0, pitch=0)

r = pdk.Deck(
    layers=[tile_layer, scatter],
    initial_view_state=view_state,
    map_style=None,
    tooltip={"text": "Lat: {latitude}\nLon: {longitude}"},
)

st.pydeck_chart(r, use_container_width=True)

st.markdown("**Attribution**: © OpenStreetMap contributors; © CARTO basemaps.")
