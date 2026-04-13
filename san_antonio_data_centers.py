# The objective of this module is to identify data centers in the San Antonio area using OpenStreetMap data accessed via the Overpass API.
# The script queries for nodes and ways tagged as data centers within an expanded bounding box that includes Castroville to the west. 
# The results are saved to a JSON file and also plotted on a Folium map with purple server icons.
# This map is saved as datacenters.html and also serves as the basis for the more complex map in build_map_aquifer_overlay.py, which adds aquifer zones and the CPS service territory boundary.
# AI tools were used to collaborate and guide this process.  

import requests
import folium
import json

# Expanded bounding box to include Castroville and Medina County
BBOX = "29.0,-99.2,29.9,-97.8"

query = f"""
[out:json][timeout:90];
(
  node["telecom"="data_center"]({BBOX});
  way["telecom"="data_center"]({BBOX});
  relation["telecom"="data_center"]({BBOX});

  node["building"="data_center"]({BBOX});
  way["building"="data_center"]({BBOX});
  relation["building"="data_center"]({BBOX});

  node["man_made"="data_center"]({BBOX});
  way["man_made"="data_center"]({BBOX});
  relation["man_made"="data_center"]({BBOX});

  node["office"="data_center"]({BBOX});
  way["office"="data_center"]({BBOX});
  relation["office"="data_center"]({BBOX});

  node["amenity"="data_center"]({BBOX});
  way["amenity"="data_center"]({BBOX});
  relation["amenity"="data_center"]({BBOX});

  node["landuse"="data_center"]({BBOX});
  way["landuse"="data_center"]({BBOX});
  relation["landuse"="data_center"]({BBOX});

  node["industrial"="data_center"]({BBOX});
  way["industrial"="data_center"]({BBOX});
  relation["industrial"="data_center"]({BBOX});
);
out center;
"""

response = requests.get(
    "https://overpass.kumi.systems/api/interpreter",
    params={"data": query},
    timeout=90
)

print(f"Status code: {response.status_code}")
data = response.json()

elements = data.get("elements", [])
print(f"Total elements found: {len(elements)}")
for el in elements:
    name = el.get("tags", {}).get("name", "Unnamed")
    print(f"  - {name}")

with open("sa_datacenters.json", "w") as f:
    json.dump(data, f)

print(f"Found {len(data['elements'])} elements")

# Clean minimal basemap
m = folium.Map(location=[29.4241, -98.4936], zoom_start=11, tiles="CartoDB voyager")

# Add data center markers as a purple server icon
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

m.save("datacenters.html")
print("Map saved to datacenters.html")
