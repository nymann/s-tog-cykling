from dataclasses import dataclass
from datetime import timedelta
import json
from typing import Optional
import webbrowser

from devtools import debug
import folium
import polyline
import requests
import typer

app = typer.Typer()

# LINE = {
#    "A": "#33B9FB",
#    "B": "#4BAA47",
#    "Bx": "#77C044",
#    "C": "#F68620",
#    "E": "#6B67AF",
#    "F": "#FFC225",
#    "H": "#EF4236",
# }

LINE = {
    "A": "lightblue",
    "B": "green",
    "Bx": "lightgreen",
    "C": "orange",
    "E": "darkpurple",
    "F": "white",
    "H": "darkred",
}
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


@dataclass
class Location:
    lat: float
    lon: float

    def tuple(self) -> tuple[float, float]:
        return (
            self.lat,
            self.lon,
        )


@dataclass
class Route:
    a: Location
    b: Location
    steps: bool = False
    hints: bool = False

    def get(self):
        response = requests.get(
            f"https://osrm.nymann.dev/route/v1/bicycle/{self.a.lon},{self.a.lat};{self.b.lon},{self.b.lat}",
            params=dict(steps="false", generate_hints="false"),
        )
        res = response.json()
        r = res["routes"][0]

        return {
            "route": polyline.decode(r["geometry"]),
            "distance": r["distance"],
            "duration": str(timedelta(seconds=r["duration"])),
            "start_point": self.a.tuple(),
            "end_point": self.b.tuple(),
        }


def address_to_coords(q: str) -> Location:
    params = {
        "q": q,
        "polygon_geojson": "1",
        "format": "jsonv2",
    }

    response = requests.get(
        "https://nominatim.openstreetmap.org/search.php",
        params=params,
        headers=headers,
    )
    results = response.json()
    if isinstance(results, list):
        result = results[0]
    else:
        result = results
    return Location(lat=float(result["lat"]), lon=float(result["lon"]))


def draw_lines_to_map(m: folium.Map) -> folium.Map:
    with open("lines.json", "r") as lines_file:
        lines = json.loads(lines_file.read())
        for line, stations in lines.items():
            for station in stations:
                loc = station["lat"], station["lon"]
                color = LINE[line]
                folium.Marker(
                    tooltip=station["name"],
                    location=loc,
                    icon=folium.Icon(
                        color=color,
                        icon="circle",
                    ),
                    draggable=False,
                ).add_to(m)
    return m


@app.command()
def route(a: str, b: str) -> None:
    a_l = address_to_coords(a)
    b_l = address_to_coords(b)
    result = Route(a=a_l, b=b_l).get()
    r = result["route"]
    m = folium.Map(
        location=[
            (result["start_point"][0] + result["end_point"][0]) / 2,
            (result["start_point"][1] + result["end_point"][1]) / 2,
        ],
        zoom_start=13,
    )

    folium.PolyLine(r, weight=8, color="blue", opacity=0.6).add_to(m)

    draw_lines_to_map(m)
    folium.Marker(
        location=result["start_point"],
        icon=folium.Icon(color="green"),
    ).add_to(m)

    folium.Marker(location=result["end_point"], icon=folium.Icon(color="red")).add_to(m)
    m.save("map.html")
    webbrowser.open("map.html")


if __name__ == "__main__":
    app()
