from datetime import datetime
from random import randint

from django_google_maps.fields import GeoPt
from psycopg2._range import Range


def generate_rand_geopt() -> GeoPt:
    return GeoPt(randint(-90, 90) / 1000000, randint(-180, 180) / 1000000)


def generate_rand_int4range(lower_range: randint, upper_range: randint) -> str:
    return str(Range(lower=lower_range, upper=upper_range))


def calculate_age_from_birthdate(birthdate: datetime) -> int:
    return int((datetime.now().date() - birthdate).days / 365.25)
