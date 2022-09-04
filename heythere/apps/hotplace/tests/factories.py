from django_google_maps.fields import GeoPt
from factory.django import DjangoModelFactory
from factory.faker import Faker

from heythere.apps.hotplace.models import HotPlace
from heythere.utils.util import FuzzyGeoPt, FuzzyGeoPtArray

RANDOM_HOTPLACE_INFO = {
    "압구정 로데오": {
        "zone_center_geoinfo": GeoPt(37.5262894, 127.0395281),
        "zone_boundary_geoinfos": [
            GeoPt(37.530342, 127.0384723),
            GeoPt(37.5286403, 127.0360262),
            GeoPt(37.5232287, 127.036627),
            GeoPt(37.5242498, 127.0433218),
            GeoPt(37.5275172, 127.0437938),
            GeoPt(37.5284021, 127.039159),
            GeoPt(37.530342, 127.0384723),
        ],
    },
    "을지로 노가리거리": {
        "zone_center_geoinfo": GeoPt(37.5672038, 126.9916705),
        "zone_boundary_geoinfos": [
            GeoPt(37.5661493, 126.9897179),
            GeoPt(37.5666341, 126.9980435),
            GeoPt(37.5701547, 126.9977538),
            GeoPt(37.5705884, 126.9970135),
            GeoPt(37.5700952, 126.9895033),
            GeoPt(37.5661493, 126.9897179),
        ],
    },
    "홍대 젊음의거리": {
        "zone_center_geoinfo": GeoPt(37.5553504, 126.923767),
        "zone_boundary_geoinfos": [
            GeoPt(37.5626307, 126.92175),
            GeoPt(37.5584803, 126.9126519),
            GeoPt(37.551693, 126.9175014),
            GeoPt(37.5486138, 126.9238958),
            GeoPt(37.5538535, 126.9299253),
            GeoPt(37.556201, 126.9284661),
            GeoPt(37.55797, 126.925741),
            GeoPt(37.5626307, 126.92175),
        ],
    },
    "역삼 먹자골목": {
        "zone_center_geoinfo": GeoPt(37.4999072, 127.0373932),
        "zone_boundary_geoinfos": [
            GeoPt(37.5037138, 127.0225116),
            GeoPt(37.4907755, 127.0298072),
            GeoPt(37.4988792, 127.0483467),
            GeoPt(37.5058246, 127.0428535),
            GeoPt(37.5037138, 127.0225116),
        ],
    },
    "목동 테스트": {
        "zone_center_geoinfo": GeoPt(37.522858, 126.8731853),
        "zone_boundary_geoinfos": [
            GeoPt(37.5393979, 126.8765327),
            GeoPt(37.5138718, 126.8458911),
            GeoPt(37.510808, 126.8950721),
            GeoPt(37.5393979, 126.8765327),
        ],
    },
    "과천 테스트": {
        "zone_center_geoinfo": GeoPt(37.4124693, 126.9870088),
        "zone_boundary_geoinfos": [
            GeoPt(37.4630372, 126.9847772),
            GeoPt(37.3798751, 126.914911),
            GeoPt(37.3783746, 127.067518),
            GeoPt(37.4630372, 126.9847772),
        ],
    },
}

RANDOM_HOTPLACE_NAMES: list = list(RANDOM_HOTPLACE_INFO.keys())


class HotPlaceFactory(DjangoModelFactory):
    # Group GPS
    name = Faker("random_element", elements=RANDOM_HOTPLACE_NAMES)
    zone_color = Faker("color")
    zone_center_geoinfo = FuzzyGeoPt(precision=5)
    zone_boundary_geoinfos = FuzzyGeoPtArray(precision=5, array_length=5)

    class Meta:
        model = HotPlace
        django_get_or_create = ("name",)
