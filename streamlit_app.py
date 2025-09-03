import streamlit as st
import pandas as pd
import pydeck as pdk
import math

st.set_page_config(page_title="Warehouse Mapper", page_icon="🗺️", layout="wide")
st.title("🗺️ Warehouse Mapper")
st.caption("Upload a CSV with latitude in column A and longitude in column B (headers optional). Each point is drawn as a colored circle.")

# --- Helpers -----------------------------------------------------------------
def read_latlon_csv(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> pd.DataFrame:
    """
    Read a CSV that has lat in column A and lon in column B.
    Works with or without headers. Coerces to numeric and drops invalid rows.
    """
    # Try headerless first (most strict for the A/B requirement)
    try:
        df = pd.read_csv(uploaded_file, header=None)
    except Exception:
        # Fallback: Streamlit might need reset file pointer
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, header=None)

    if df.shape[1] < 2:
        # Try again assuming headers exist
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)

        if df.shape[1] < 2:
            raise ValueError("CSV must have at least two columns for latitude and longitude.")

        cols = list(df.columns)
        lat_col, lon_col = cols[0], cols[1]
        df = df.rename(columns={lat_col: "latitude", lon_col: "longitude"})
    else:
        df = df.rename(columns={0: "latitude", 1: "longitude"})

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
    return df[["latitude", "longitude"]]


def distinct_palette_rgba(n: int, alpha: int = 200):
    """
    Generate n distinct RGBA colors using an HSL sweep.
    Returns a list of [r,g,b,a] lists.
    """
    def hsl_to_rgb(h, s, l):
        # h in [0,1), s,l in [0,1]
        def hue2rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue2rgb(p, q, h + 1/3)
            g = hue2rgb(p, q, h)
            b = hue2rgb(p, q, h - 1/3)
        return [int(r*255), int(g*255), int(b*255)]

    palette = []
    for i in range(max(n, 1)):
        h = (i / max(n, 1)) % 1.0       # evenly spaced hue
        s = 0.65                         # fairly saturated
        l = 0.50                         # medium lightness
        r, g, b = hsl_to_rgb(h, s, l)
        palette.append([r, g, b, alpha])
    return palette


# --- UI ----------------------------------------------------------------------
with st.sidebar:
    st.header("Upload")
    uploaded = st.file_uploader("Upload CSV (lat in column A, lon in column B)", type=["csv"])
    point_radius = st.slider("Point radius (meters)", min_value=200, max_value=80000, value=3000, step=100)
    basemap = st.selectbox(
        "Basemap",
        ["CARTO Light", "CARTO Dark", "OpenStreetMap"],
        index=0
    )

# Load data
if not uploaded:
    st.info("Upload a CSV to display your warehouse locations.")
    st.stop()

try:
    df = read_latlon_csv(uploaded)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

# Assign a distinct color to every row
palette = distinct_palette_rgba(len(df), alpha=220)
df = df.copy()
df["fill_rgba"] = palette

# Choose basemap tiles
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
    data=df,
    get_position="[longitude, latitude]",
    get_fill_color="fill_rgba",
    get_radius=point_radius,
    pickable=True,
    auto_highlight=True,
)

# View
if len(df) > 0:
    center_lat = float(df["latitude"].mean())
    center_lon = float(df["longitude"].mean())
    zoom = 4 if len(df) > 1 else 8
else:
    center_lat, center_lon, zoom = 39.5, -98.35, 3

view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom, bearing=0, pitch=0)

deck = pdk.Deck(
    layers=[tile_layer, scatter],
    initial_view_state=view_state,
    map_style=None,
    tooltip={"text": "Lat: {latitude}\nLon: {longitude}"}
)

st.pydeck_chart(deck, use_container_width=True)
st.markdown("**Attribution**: © OpenStreetMap contributors; © CARTO basemaps.")

