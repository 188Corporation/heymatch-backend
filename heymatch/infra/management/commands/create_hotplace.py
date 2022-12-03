from django.core.management.base import BaseCommand

from heymatch.apps.hotplace.models import HotPlace
from heymatch.apps.hotplace.tests.factories import (
    RANDOM_HOTPLACE_INFO,
    RANDOM_HOTPLACE_NAMES,
)


class Command(BaseCommand):
    help = "Command for creating hotplace data"

    def handle(self, *args, **options):
        """Rest DB and migrate"""

        for name in RANDOM_HOTPLACE_NAMES:
            HotPlace.objects.get_or_create(
                name=name,
                zone_center_geoinfo=RANDOM_HOTPLACE_INFO[name]["zone_center_geoinfo"],
                zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[name][
                    "zone_boundary_geoinfos"
                ],
                zone_boundary_geoinfos_for_fake_chat=RANDOM_HOTPLACE_INFO[name][
                    "zone_boundary_geoinfos_for_fake_chat"
                ],
            )

        self.stdout.write(self.style.SUCCESS("Successfully set up Hotplace!"))
