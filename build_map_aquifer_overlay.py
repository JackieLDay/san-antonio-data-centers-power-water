# The objective of this module is to build a map of San Antonio data centers, overlaid with Edwards Aquifer zones and the CPS Energy service territory boundary,
# using data sources that are publicly available and pre-processed in the other modules included in this project.
# The map is built using the Folium library, which provides an interface to Leaflet.js for interactive web maps.
# The aquifer zones are loaded from a shapefile provided by the Edwards Aquifer Authority, and styled with colors for recharge, contributing, and artesian zones chosen to align with the visible
# representation in the EAA's online map. The CPS service territory boundary is loaded from a GeoJSON file generated in the Extract_service_boundary.py module, 
# which used OpenCV to extract the boundary from a PDF map.
# AI tools were used to collaborate and guide this process. 

import folium
import json
import geopandas as gpd

# Load data centers from saved file
with open("sa_datacenters.json", "r") as f:
    data = json.load(f)

print(f"Found {len(data['elements'])} elements")

# Load aquifer shapefile and reproject to WGS84 for Folium
aquifer = gpd.read_file(r"AquiferZones-1\AquiferZones.shp")
aquifer = aquifer.to_crs(epsg=4326)
print(f"Aquifer CRS: {aquifer.crs}")
print(f"Aquifer columns: {aquifer.columns.tolist()}")
print(aquifer['Symbolize'].unique())
print(aquifer['Name'].unique())

# Load CPS boundary GeoJSON
with open(r"cps_boundary.geojson", "r") as f:
    cps_boundary = json.load(f)

# Build map
#m = folium.Map(location=[29.4241, -98.4936], zoom_start=10, tiles="CartoDB voyager")
m = folium.Map(location=[29.4241, -98.4936], zoom_start=10, tiles="OpenStreetMap")


def aquifer_style(feature):
    zone = feature["properties"]["Symbolize"]
    color_map = {
        "Recharge Zone":     {"fillColor": "#4da6ff", "color": "#2980b9"},
        "Contributing Zone": {"fillColor": "#90ee90", "color": "#5cb85c"},
        "Artesian Zone":     {"fillColor": "#f39c12", "color": "#e67e22"},
    }
    style = color_map.get(zone, {"fillColor": "#95a5a6", "color": "#7f8c8d"})
    return {
        "fillColor": style["fillColor"],
        "color": style["color"],
        "weight": 2.5,
        "fillOpacity": 0.15
    }

folium.GeoJson(
    aquifer,
    name="Edwards Aquifer Zones",
    style_function=aquifer_style
).add_to(m)

# Add CPS service territory boundary as black outline
folium.GeoJson(
    cps_boundary,
    name="CPS Service Territory",
    style_function=lambda x: {
        "color": "#000000",
        "weight": 2.5,
        "fillOpacity": 0
    },
    tooltip="CPS Energy Service Territory"
).add_to(m)

# Add data center markers
for element in data["elements"]:
    lat = element.get("lat") or element.get("center", {}).get("lat")
    lon = element.get("lon") or element.get("center", {}).get("lon")
    name = element.get("tags", {}).get("name", "Unknown Data Center")
    if lat and lon:
        folium.Marker(
            location=[lat, lon],
            popup=name,
            icon=folium.Icon(color="darkpurple", icon="server", prefix="fa")
        ).add_to(m)

legend_html = """
<div style="
    position: fixed;
    bottom: 40px;
    left: 40px;
    z-index: 1000;
    background-color: white;
    padding: 15px 20px;
    border-radius: 8px;
    border: 1px solid #ccc;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    font-family: Arial, sans-serif;
    font-size: 13px;
    line-height: 1.8;
">
    <b style="font-size: 15px;">Legend</b><br>
    <hr style="margin: 6px 0;">
    <b style="font-size: 13px;">Edwards Aquifer Zones</b><br>
    <span style="background:#90ee90; border:1px solid #5cb85c; opacity:0.5; display:inline-block; width:16px; height:16px; margin-right:8px; vertical-align:middle;"></span>Contributing Zone<br>
    <span style="background:#4da6ff; border:1px solid #2980b9; opacity:0.5; display:inline-block; width:16px; height:16px; margin-right:8px; vertical-align:middle;"></span>Recharge Zone<br>
    <span style="background:#f39c12; border:1px solid #e67e22; opacity:0.5; display:inline-block; width:16px; height:16px; margin-right:8px; vertical-align:middle;"></span>Artesian Zone<br>
    <hr style="margin: 6px 0;">
    <b style="font-size: 13px;">Data Centers</b><br>
    <span style="display:inline-block; position:relative; width:18px; height:26px; margin-right:8px; vertical-align:middle;">
        <span style="
            display:flex;
            align-items:center;
            justify-content:center;
            position:absolute;
            top:0; left:0;
            width:18px; height:18px;
            background:#5B396B;
            border-radius:50% 50% 50% 0;
            transform:rotate(-45deg);
            border:1px solid rgba(0,0,0,0.2);
        ">
            <i class="fa fa-server" style="color:white; font-size:8px; transform:rotate(45deg);"></i>
        </span>
    </span>Data Center<br>
    <hr style="margin: 6px 0;">
    <b style="font-size: 13px;">CPS Service Area</b><br>
    <span style="display:inline-block; width:30px; height:3px; background:#000; margin-right:8px; vertical-align:middle;"></span>CPS Service Area (approximate)<br>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

title_html = """
<div style="
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    background-color: white;
    padding: 10px 24px;
    border-radius: 8px;
    border: 1px solid #ccc;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    font-family: Arial, sans-serif;
    text-align: center;
    white-space: nowrap;
">
    <div style="font-size: 16px; font-weight: bold;">
        San Antonio Area Data Centers, Edwards Aquifer Zones and CPS Service Area
    </div>
    <div style="font-size: 12px; color: #555; margin-top: 4px; font-weight: normal;">
        Data centers are significant consumers of both water and electricity. This map shows their locations relative to the Edwards Aquifer and the CPS Energy service area (approximate).
    </div>
</div>
"""

m.get_root().html.add_child(folium.Element(title_html))


# Layer control so users can toggle layers on/off
#folium.LayerControl(collapsed=False).add_to(m)

m.save(r"datacenters.html")
print("Map saved to datacenters.html")