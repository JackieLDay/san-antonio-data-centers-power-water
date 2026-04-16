# San Antonio Data Centers: Power & Water
Interactive map exploring data center locations, electric utility service territory, and Edwards Aquifer zones in San Antonio, TX area.
Built with Python, GeoPandas, and Folium.

## Overview
As data center development accelerates to support AI and other applications, San Antonio has emerged as a growing hub for digital infrastructure.  This project visualizes where data centers are locating relative to the electric utility service boundaries and the Edwards Aquifer - a critical and sensitive water supply for the region.  The result is an interactive map that layers infrastructure, energy and water in a single view.  

## Map Layers
- **Data Centers** — locations sourced from OpenStreetMap via the Overpass API
- **CPS Energy Service Territory** — Boundary derived from CPS Energy's published service territory map (see methods below)
- **Edwards Aquifer Zones** — boundary data provided by the Edwards Aquifer Authority

## Output
![Link to Output Map File](https://JackieLDay.github.io/san-antonio-data-centers-power-water/index.html)
