from typing import Any, Sequence

from factory import post_generation
from factory.django import DjangoModelFactory
from factory.faker import Faker

from heythere.apps.search.models import HotPlace
from heythere.utils.util import generate_rand_geopt

RANDOM_HOTPLACE_NAMES = [
    "압구정 로데오",
    "을지로 노가리거리",
    "홍대 젊음의거리",
]


class HotPlaceFactory(DjangoModelFactory):
    # Group GPS
    name = Faker("random_element", elements=RANDOM_HOTPLACE_NAMES)
    zone_color = Faker("color")
    zone_center_geoinfo = generate_rand_geopt()
    zone_boundary_geoinfos = [generate_rand_geopt() for _ in range(10)]

    class Meta:
        model = HotPlace

    @post_generation
    def groups(self, create: bool, extracted: Sequence[Any], **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                group.hotplace = self
                group.save()
