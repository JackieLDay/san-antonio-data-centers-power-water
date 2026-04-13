# The objective of this module is to output a geospatial representation of the CPS Energy service area. 
# February 2026, from the CPS Energy website (www.cpsenergy.com) a PDF file titled CPS Energy Service Territory and named "service_area_map_2011.pdf" was identified and downloaded. 
# Used PyMuPDF to render the first page as an image, then cropped to the map area. 
# Applied color thresholding in OpenCV to isolate the light blue region representing the service territory, and extracted contours. 
# The largest contour was converted from pixel coordinates to lat/lon using hardcoded geographic bounds, simplified with Shapely, and exported as a GeoJSON file. 
# This GeoJSON boundary is then loaded in build_map_aquifer_overlay.py to overlay on the Folium map with data centers and aquifer zones.
# AI tools were used to collaborate and guide this process.


import fitz  # PyMuPDF
import cv2
import numpy as np
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union
import json

# ============================================================
# CONFIGURATION
# ============================================================
PDF_PATH = "service_area_map_2011.pdf"
PAGE_NUMBER = 0
DPI = 300
OUTPUT_GEOJSON = "cps_boundary.geojson"

CROP = {
    "left":   0.08,
    "right":  0.97,
    "top":    0.05,
    "bottom": 0.97,
}

MAP_LON_LEFT   = -98.95
MAP_LON_RIGHT  = -97.98
MAP_LAT_TOP    =  29.82
MAP_LAT_BOTTOM =  29.08

# ============================================================
# STEP 1: Render PDF and crop
# ============================================================
print("Rendering PDF...")
doc = fitz.open(PDF_PATH)
page = doc[PAGE_NUMBER]
mat = fitz.Matrix(DPI / 72, DPI / 72)
pix = page.get_pixmap(matrix=mat)

img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
if pix.n == 4:
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
else:
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

h, w = img_bgr.shape[:2]
x1 = int(w * CROP["left"])
x2 = int(w * CROP["right"])
y1 = int(h * CROP["top"])
y2 = int(h * CROP["bottom"])
map_img = img_bgr[y1:y2, x1:x2]
cv2.imwrite("debug_cropped_map.png", map_img)

map_h, map_w = map_img.shape[:2]
print(f"Cropped map size: {map_w} x {map_h} px")

# ============================================================
# STEP 2: Pixel -> lat/lon using hardcoded geographic bounds
# ============================================================
def pixel_to_latlon(px, py):
    lon = MAP_LON_LEFT + (px / map_w) * (MAP_LON_RIGHT - MAP_LON_LEFT)
    lat = MAP_LAT_TOP  + (py / map_h) * (MAP_LAT_BOTTOM - MAP_LAT_TOP)
    return lon, lat

def latlon_to_pixel(lon, lat):
    px = int((lon - MAP_LON_LEFT) / (MAP_LON_RIGHT - MAP_LON_LEFT) * map_w)
    py = int((lat - MAP_LAT_TOP)  / (MAP_LAT_BOTTOM - MAP_LAT_TOP) * map_h)
    return px, py

cx, cy = map_w // 2, map_h // 2
clon, clat = pixel_to_latlon(cx, cy)
print(f"Center pixel ({cx}, {cy}) -> ({clat:.4f}N, {clon:.4f}W)  [expect ~29.45N, ~98.47W]")

# ============================================================
# STEP 3: Isolate the light blue region
# ============================================================
print("\nDetecting light blue region...")
hsv = cv2.cvtColor(map_img, cv2.COLOR_BGR2HSV)

lower_blue = np.array([95,  30, 150])
upper_blue = np.array([118, 120, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

kernel = np.ones((7, 7), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
cv2.imwrite("debug_mask.png", mask)

# ============================================================
# STEP 4: Find contours
# ============================================================
print("Finding contours...")
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

if not contours:
    print("ERROR: No contours found.")
    exit()

contours = sorted(contours, key=cv2.contourArea, reverse=True)
print(f"Found {len(contours)} contours:")
for i, c in enumerate(contours[:5]):
    print(f"  #{i}: area = {cv2.contourArea(c):.0f} px²")

# ============================================================
# STEP 5: Build polygons
# ============================================================
print("\nBuilding polygons...")
polygons = []
preview_img = map_img.copy()
MIN_AREA_PX = 5000

for i, contour in enumerate(contours[:1]):   # only keep the largest contour
    area = cv2.contourArea(contour)
    if area < MIN_AREA_PX:
        continue
    pts = contour.squeeze()
    if pts.ndim != 2 or len(pts) < 4:
        continue
    coords = [pixel_to_latlon(p[0], p[1]) for p in pts]
    coords.append(coords[0])
    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_valid and poly.area > 0:
            poly = poly.simplify(0.0005, preserve_topology=True)
            polygons.append(poly)
            # Draw contour on preview image
            cv2.drawContours(preview_img, [contour], -1, (0, 0, 255), 3)
            print(f"  Added contour #{i}: {len(pts)} pts")
    except Exception as e:
        print(f"  Skipped contour #{i}: {e}")

if not polygons:
    print("ERROR: No valid polygons built.")
    exit()

merged = unary_union(polygons) if len(polygons) > 1 else polygons[0]

# ============================================================
# STEP 6: Export GeoJSON
# ============================================================
print("\nWriting GeoJSON...")
feature = {
    "type": "Feature",
    "geometry": mapping(merged),
    "properties": {"name": "CPS Energy Service Territory"}
}
collection = {
    "type": "FeatureCollection",
    "features": [feature]
}
with open(OUTPUT_GEOJSON, "w") as f:
    json.dump(collection, f, indent=2)

print(f"Done! Saved: {OUTPUT_GEOJSON}")

# ============================================================
# STEP 7: Preview using cv2 (no matplotlib needed)
# ============================================================
cv2.imwrite("boundary_preview.png", preview_img)
print("Saved boundary_preview.png  (detected boundary drawn in red)")