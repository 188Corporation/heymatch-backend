from django_google_maps.fields import GeoPt
from factory.django import DjangoModelFactory
from factory.faker import Faker

from heymatch.apps.hotplace.models import HotPlace
from heymatch.utils.util import FuzzyGeoPt, FuzzyGeoPtArray

RANDOM_HOTPLACE_INFO = {
    # "압구정 로데오": {
    #     "zone_center_geoinfo": GeoPt(37.5262894, 127.0395281),
    #     "zone_boundary_geoinfos": [
    #         GeoPt(37.530342, 127.0384723),
    #         GeoPt(37.5286403, 127.0360262),
    #         GeoPt(37.5232287, 127.036627),
    #         GeoPt(37.5242498, 127.0433218),
    #         GeoPt(37.5275172, 127.0437938),
    #         GeoPt(37.5284021, 127.039159),
    #         GeoPt(37.530342, 127.0384723),
    #     ],
    # },
    # "을지로 노가리거리": {
    #     "zone_center_geoinfo": GeoPt(37.5672038, 126.9916705),
    #     "zone_boundary_geoinfos": [
    #         GeoPt(37.5661493, 126.9897179),
    #         GeoPt(37.5666341, 126.9980435),
    #         GeoPt(37.5701547, 126.9977538),
    #         GeoPt(37.5705884, 126.9970135),
    #         GeoPt(37.5700952, 126.9895033),
    #         GeoPt(37.5661493, 126.9897179),
    #     ],
    # },
    # "홍대 젊음의거리": {
    #     "zone_center_geoinfo": GeoPt(37.5553504, 126.923767),
    #     "zone_boundary_geoinfos": [
    #         GeoPt(37.5626307, 126.92175),
    #         GeoPt(37.5584803, 126.9126519),
    #         GeoPt(37.551693, 126.9175014),
    #         GeoPt(37.5486138, 126.9238958),
    #         GeoPt(37.5538535, 126.9299253),
    #         GeoPt(37.556201, 126.9284661),
    #         GeoPt(37.55797, 126.925741),
    #         GeoPt(37.5626307, 126.92175),
    #     ],
    # },
    # "역삼 먹자골목": {
    #     "zone_center_geoinfo": GeoPt(37.4999072, 127.0373932),
    #     "zone_boundary_geoinfos": [
    #         GeoPt(37.5037138, 127.0225116),
    #         GeoPt(37.4907755, 127.0298072),
    #         GeoPt(37.4988792, 127.0483467),
    #         GeoPt(37.5058246, 127.0428535),
    #         GeoPt(37.5037138, 127.0225116),
    #     ],
    # },
    # "목동 테스트": {
    #     "zone_center_geoinfo": GeoPt(37.522858, 126.8731853),
    #     "zone_boundary_geoinfos": [
    #         GeoPt(37.5393979, 126.8765327),
    #         GeoPt(37.5138718, 126.8458911),
    #         GeoPt(37.510808, 126.8950721),
    #         GeoPt(37.5393979, 126.8765327),
    #     ],
    # },
    # "과천 테스트": {
    #     "zone_center_geoinfo": GeoPt(37.4124693, 126.9870088),
    #     "zone_boundary_geoinfos": [
    #         GeoPt(37.4630372, 126.9847772),
    #         GeoPt(37.3798751, 126.914911),
    #         GeoPt(37.3783746, 127.067518),
    #         GeoPt(37.4630372, 126.9847772),
    #     ],
    # },
    "대구 동성로": {
        "zone_center_geoinfo": GeoPt(35.8699661, 128.5957445),
        "zone_boundary_geoinfos": [
            GeoPt(35.8761561, 128.5879969),
            GeoPt(35.8738262, 128.5876536),
            GeoPt(35.8699314, 128.5872673),
            GeoPt(35.8660015, 128.5866236),
            GeoPt(35.8662798, 128.5878252),
            GeoPt(35.8642626, 128.5982966),
            GeoPt(35.8633583, 128.5994553),
            GeoPt(35.8628019, 128.6027598),
            GeoPt(35.8705988, 128.6045099),
            GeoPt(35.872157, 128.604691),
            GeoPt(35.8736871, 128.6031031),
            GeoPt(35.8765386, 128.5888981),
            GeoPt(35.8761561, 128.5879969),
        ],
        "zone_boundary_geoinfos_for_fake_chat": [
            GeoPt(35.8687555, 128.5969852),
            GeoPt(35.8682425, 128.5959231),
            GeoPt(35.8670688, 128.5956549),
            GeoPt(35.8659385, 128.5963951),
            GeoPt(35.8654603, 128.5991632),
            GeoPt(35.8664167, 128.5994421),
            GeoPt(35.8683382, 128.5994743),
            GeoPt(35.8687555, 128.5969852),
        ],
    },
    "서울 테스트": {
        "zone_center_geoinfo": GeoPt(37.4940738, 126.9840068),
        "zone_boundary_geoinfos": [
            GeoPt(37.5822636, 126.783446),
            GeoPt(37.4804146, 126.7491062),
            GeoPt(37.4100742, 126.7703971),
            GeoPt(37.3434901, 126.8720437),
            GeoPt(37.3342073, 127.0574796),
            GeoPt(37.3434901, 126.8720437),
            GeoPt(37.3778812, 127.1811036),
            GeoPt(37.4973084, 127.2065152),
            GeoPt(37.6660349, 127.0602267),
            GeoPt(37.6616855, 126.9008889),
            GeoPt(37.6252489, 126.8260275),
            GeoPt(37.5822636, 126.783446),
        ],
        "zone_boundary_geoinfos_for_fake_chat": [
            GeoPt(37.5822636, 126.783446),
            GeoPt(37.4804146, 126.7491062),
            GeoPt(37.4100742, 126.7703971),
            GeoPt(37.3434901, 126.8720437),
            GeoPt(37.3342073, 127.0574796),
            GeoPt(37.3434901, 126.8720437),
            GeoPt(37.3778812, 127.1811036),
            GeoPt(37.4973084, 127.2065152),
            GeoPt(37.6660349, 127.0602267),
            GeoPt(37.6616855, 126.9008889),
            GeoPt(37.6252489, 126.8260275),
            GeoPt(37.5822636, 126.783446),
        ],
    },
}

RANDOM_HOTPLACE_NAMES: list = list(RANDOM_HOTPLACE_INFO.keys())


class HotPlaceFactory(DjangoModelFactory):
    # Group GPS
    name = Faker("random_element", elements=RANDOM_HOTPLACE_NAMES)
    # zone_color = Faker("color")
    zone_center_geoinfo = FuzzyGeoPt(precision=5)
    zone_boundary_geoinfos = FuzzyGeoPtArray(precision=5, array_length=5)

    class Meta:
        model = HotPlace
        django_get_or_create = ("name",)
