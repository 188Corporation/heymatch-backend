import decimal
from datetime import datetime
from random import randint, uniform
from typing import Sequence

from django_google_maps.fields import GeoPt
from factory import random
from factory.fuzzy import BaseFuzzyAttribute
from psycopg2._range import Range
from shapely.geometry import Point, Polygon


class FuzzyGeoPt(BaseFuzzyAttribute):
    def __init__(self, precision=5):
        self.lat_low = -90
        self.lat_high = 90
        self.long_low = -180
        self.long_hgh = 180
        self.precision = precision

        super().__init__()

    def fuzz(self) -> GeoPt:
        return self.generate_geopt()

    def generate_geopt(self):
        lat_base = decimal.Decimal(
            str(random.randgen.uniform(self.lat_low, self.lat_high))
        )
        long_base = decimal.Decimal(
            str(random.randgen.uniform(self.long_low, self.long_hgh))
        )
        lat = lat_base.quantize(decimal.Decimal(10) ** -self.precision)
        long = long_base.quantize(decimal.Decimal(10) ** -self.precision)
        return GeoPt(lat, long)


class FuzzyGeoPtArray(FuzzyGeoPt):
    def __init__(self, precision=5, array_length=6):
        self.array_length = array_length

        super().__init__(precision=precision)

    def fuzz(self) -> Sequence[GeoPt]:
        result = []
        for _ in range(self.array_length):
            result.append(self.generate_geopt())
        return result


class FuzzyInt4Range(BaseFuzzyAttribute):
    def __init__(self, low: int, high: int, step=1):
        self.low = low
        self.high = high
        self.step = 1
        super().__init__()

    def fuzz(self):
        lower = int(random.randgen.randrange(self.low, self.high, self.step))
        upper = int(random.randgen.randrange(lower + 1, self.high + 1, self.step))
        return str(Range(lower=lower, upper=upper))


def generate_rand_geopt() -> GeoPt:
    return GeoPt(randint(-90, 90) / 1000000, randint(-180, 180) / 1000000)


def generate_rand_int4range(lower_range: randint, upper_range: randint) -> str:
    return str(Range(lower=lower_range, upper=upper_range))


def calculate_age_from_birthdate(birthdate: datetime) -> int:
    return int((datetime.now().date() - birthdate).days / 365.25)


def generate_rand_geoopt_within_boundary(boundary_geopts: Sequence[GeoPt]) -> GeoPt:
    """
    Get a certain GeoPt within Boundary (Sequence[GeoPt])
    """
    # convert list of geopts to list of (lat, lon)
    polygon = Polygon([(geopt.lat, geopt.lon) for geopt in boundary_geopts])
    minx, miny, maxx, maxy = polygon.bounds
    result = None
    while not result:
        pnt = Point(
            float(format(uniform(minx, maxx), ".6f")),
            float(format(uniform(miny, maxy), ".6f")),
        )
        if polygon.contains(pnt):
            result = GeoPt(lat=pnt.x, lon=pnt.y)
    return result


def is_geopt_within_boundary(geopt: GeoPt, boundary_geopts: Sequence[GeoPt]) -> bool:
    """
    Determine whether provided GeoPt resides within GeoPts in certain boundary.
    """
    polygon = Polygon([(geopt.lat, geopt.lon) for geopt in boundary_geopts])
    pnt = Point(geopt.lat, geopt.lon)
    return polygon.contains(pnt)
