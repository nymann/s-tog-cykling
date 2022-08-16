#!/usr/bin/env python3
import json
from typing import Any

from bs4 import BeautifulSoup
from devtools import debug
import requests
import typer

res = requests.get("https://da.wikipedia.org/wiki/S-togsstationer").text
stations = {}
lines = {}
soup = BeautifulSoup(markup=res, features="html.parser")
table = soup.find("table", attrs={"class": "wikitable sortable"})
if table is None:
    raise Exception()

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

ALL_STATIONS = requests.get("https://www.dsb.dk/api/stations/getstationlist", headers=headers).json()


class Station:
    def __init__(
        self,
        name: str,
        lines: list[str],
        lat: float,
        lon: float,
    ) -> None:
        self.name: str = name
        self.lines: list[str] = lines
        self.lat: float = lat
        self.lon: float = lon

    def dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "lines": self.lines,
            "lat": self.lat,
            "lon": self.lon,
        }

    @classmethod
    def from_row(cls, row) -> "Station":
        cols = row.find_all("td")
        name = cols[0].text.strip()
        if "[" in name:
            name = name[: name.index("[")]
        if "Høvelte" in name:
            raise KeyError("Don't use høvelte")

        lines = []
        for link in cols[2].find_all("a"):
            lines.append(link["title"].replace("Linje ", ""))
        for station in ALL_STATIONS:
            if name in station["stationName"]:
                station_name = station["stationName"]
                lat = float(station["stationLatitude"])
                lon = float(station["stationLongitude"])
                return cls(name=station_name, lines=lines, lat=lat, lon=lon)
        raise Exception(f"{name}, not found in stations from DSB")


table_body = table.find("tbody")
rows = table_body.find_all("tr")[1:]
# header = [ele.text.strip() for ele in rows[0].find_all("th")]
with typer.progressbar(rows) as progress:
    for row in progress:
        try:
            station = Station.from_row(row=row)
        except KeyError:
            continue

        stations[station.name] = station.dict()
        for line in station.lines:
            if line not in lines:
                lines[line] = []
            lines[line].append(station.dict())

with open("stations.json", "w") as stations_file:
    stations_file.write(json.dumps(stations, indent=2, ensure_ascii=False))

with open("lines.json", "w") as lines_file:
    lines_file.write(json.dumps(lines, indent=2, ensure_ascii=False))
