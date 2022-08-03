from dataclasses import dataclass

from devtools import debug
import requests
import typer

app = typer.Typer()

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


@dataclass
class RouteInput:
    a: Location
    b: Location
    steps: bool = False
    hints: bool = False


def get_route(route_input: RouteInput):
    route = requests.get(
        f"https://osrm.nymann.dev/route/v1/bicycle/{route_input.a.lon},{route_input.a.lat};{route_input.b.lon},{route_input.b.lat}",
        params=dict(steps="false", generate_hints="false"),
    )
    route.raise_for_status()
    return route.json()


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
    return Location(lat=result["lat"], lon=result["lon"])


@app.command()
def route(a: str, b: str) -> None:
    a_l = address_to_coords(a)
    b_l = address_to_coords(b)
    route_input = RouteInput(a=a_l, b=b_l)
    result = get_route(route_input)
    debug(result)


if __name__ == "__main__":
    app()
