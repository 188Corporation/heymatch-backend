import pathlib
import random

from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from factory.django import ImageField
from phone_verify.models import SMSVerification

from heymatch.apps.group.models import Group
from heymatch.apps.group.tests.factories import (
    ActiveGroupFactory,
    GroupProfileImageFactory,
    profile_image_filepath,
)
from heymatch.apps.hotplace.models import HotPlace
from heymatch.apps.hotplace.tests.factories import (
    RANDOM_HOTPLACE_INFO,
    RANDOM_HOTPLACE_NAMES,
    HotPlaceFactory,
)
from heymatch.apps.match.tests.factories import MatchRequestFactory
from heymatch.apps.payment.models import FreePassItem, PointItem
from heymatch.apps.user.models import AppInfo
from heymatch.apps.user.tests.factories import ActiveUserFactory
from heymatch.utils.util import generate_rand_geoopt_within_boundary

User = get_user_model()
# stream = settings.STREAM_CLIENT

"""
Note that Custom Commands are only available in LOCAL environment.
See config/settings/local.py
"""


class Command(BaseCommand):
    help = "Command for initial data setup in devel environment"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset_db",
            action="store_true",
            help="Rest DB before datasetup",
        )
        parser.add_argument(
            "--noinput",
            action="store_true",
            help="Bypass input from command",
        )
        parser.add_argument(
            "--migrate_all",
            action="store_true",
            help="Migrate all steps",
        )

    def handle(self, *args, **options):
        """Rest DB and migrate"""

        migrate_all = False
        if options["migrate_all"]:
            self.stdout.write(
                self.style.WARNING(
                    "You selected `migrate all`. Will migrate all steps."
                )
            )
            migrate_all = True

        if options["reset_db"]:
            if options["noinput"]:
                management.call_command("reset_db", "--noinput")
            else:
                management.call_command("reset_db")

        # it is user's responsibility
        management.call_command("migrate", "--noinput")

        # -------------- Superuser setup -------------- #
        if migrate_all or input("Create Superuser? [y/N]") == "y":
            self.generate_superuser()

        # -------------- Normal Users setup -------------- #
        if migrate_all or input("Create Normal User? [y/N]") == "y":
            self.generate_normal_users()

        # -------------- Hotplace, Group, Users setup -------------- #
        if migrate_all or input("Create Hotplace+Groups? [y/N]") == "y":
            self.generate_hotplace_groups()

        # -------------- Developer setup -------------- #
        if migrate_all or input("Create Developer? [y/N]") == "y":
            self.generate_developer_users()

        # -------------- Payment setup -------------- #
        if migrate_all or input("Create Payments? [y/N]") == "y":
            self.generate_payment_items()

        # -------------- AppInfo setup -------------- #
        if migrate_all or input("Create App info? [y/N]") == "y":
            self.generate_app_info_item()

        # -------------- Done! -------------- #
        self.stdout.write(self.style.SUCCESS("Successfully set up all mocking data!"))

    def generate_superuser(self) -> None:
        try:
            User.objects.create_superuser(  # superuser
                username="admin", phone_number="+821000000000", password="1234"
            )
            # Register Stream token
            # stream.upsert_user({"id": str(u.id), "role": "user"})
        except IntegrityError:
            # u = User.objects.get(username="admin")
            # stream.upsert_user({"id": str(u.id), "role": "user"})
            self.stdout.write(
                self.style.NOTICE("Integrity Error @ {}".format("create_superuser"))
            )
            pass
        SMSVerification.objects.get_or_create(  # sms for user 1
            phone_number="+821000000000",
            defaults={
                "security_code": "098765",
                "session_token": "sessiontoken2",
                "is_verified": True,
            },
        )
        self.stdout.write(
            self.style.SUCCESS("Successfully set up data for [Superuser]")
        )

    def generate_developer_users(self) -> None:
        developer_phone_numbers = ["+821032433994"]

        for phone_number in developer_phone_numbers:
            try:
                developer = User.active_objects.create(  # user 1
                    phone_number=phone_number
                )
            except IntegrityError:
                continue

            SMSVerification.objects.get_or_create(  # sms for user 1
                phone_number=phone_number,
                defaults={
                    "security_code": "123456",
                    "session_token": "sessiontoken1",
                    "is_verified": True,
                },
            )
            # Create Group
            geopt = generate_rand_geoopt_within_boundary(
                RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
            )
            hotplace = HotPlace.objects.all().first()
            group = ActiveGroupFactory.create(
                hotplace=hotplace,
                gps_geoinfo=geopt,
            )
            # Create group profile image
            GroupProfileImageFactory.create(
                group=group,
                image=ImageField(
                    from_path=f"{pathlib.Path().resolve()}/heymatch/data/{random.choice(profile_image_filepath)}"
                ),
            )
            developer.joined_group = group
            developer.save()

            # Create MatchRequest
            first_group = Group.objects.all().filter(hotplace=hotplace)[0]
            last_group = Group.objects.all().filter(hotplace=hotplace)[1]
            MatchRequestFactory.create(
                sender_group=group,
                receiver_group=first_group,
            )
            MatchRequestFactory.create(
                sender_group=last_group,
                receiver_group=group,
            )

        self.stdout.write(
            self.style.SUCCESS("Successfully set up data for [Developer]")
        )

    def generate_normal_users(self) -> None:
        ActiveUserFactory.create_batch(size=2, joined_group=None)
        # InactiveUserFactory.create_batch(size=10)  # "joined_group=None" by default
        self.stdout.write(self.style.SUCCESS("Successfully set up data for [Users]"))

    def generate_hotplace_groups(self) -> None:
        for name in RANDOM_HOTPLACE_NAMES:
            # create hotplace
            hotplace = HotPlaceFactory(
                name=name,
                zone_center_geoinfo=RANDOM_HOTPLACE_INFO[name]["zone_center_geoinfo"],
                zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[name][
                    "zone_boundary_geoinfos"
                ],
            )
            # create groups for each hotplaces
            for _ in range(random.randint(2, 4)):
                geopt = generate_rand_geoopt_within_boundary(
                    RANDOM_HOTPLACE_INFO[name]["zone_boundary_geoinfos"]
                )
                group = ActiveGroupFactory.create(
                    hotplace=hotplace,
                    gps_geoinfo=geopt,
                )
                # Create group profile image
                GroupProfileImageFactory.create(
                    group=group,
                    image=ImageField(
                        from_path=f"{pathlib.Path().resolve()}/heymatch/data/{random.choice(profile_image_filepath)}"
                    ),
                )
                # Create users for each groups
                # NOTE: For now, only one user is mapped to one group so size is 1
                ActiveUserFactory.create_batch(
                    size=1,
                    joined_group=group,
                )
                # Group.objects.register_group_leader_user(group, users[0])
                # Group.objects.register_normal_users(group, users[1:])

        self.stdout.write(
            self.style.SUCCESS("Successfully set up data for [Hotplaces/Groups/User]")
        )

    def generate_payment_items(self) -> None:
        # Point Items
        PointItem.objects.create(
            name="캔디 5개",
            product_id="com.co188.heymatch.point_item1",
            price_in_krw=4400,
            default_point=5,
        )
        PointItem.objects.create(
            name="캔디 10개+1개",
            product_id="com.co188.heymatch.point_item2",
            price_in_krw=9900,
            default_point=10,
            bonus_point=2,
        )
        PointItem.objects.create(
            name="캔디 15개+5개",
            product_id="com.co188.heymatch.point_item3",
            price_in_krw=14000,
            default_point=15,
            bonus_point=5,
            best_deal_check=True,
        )
        PointItem.objects.create(
            name="캔디 30개+15개",
            product_id="com.co188.heymatch.point_item4",
            price_in_krw=22000,
            default_point=25,
            bonus_point=15,
        )
        PointItem.objects.create(
            name="캔디 50개+35개",
            product_id="com.co188.heymatch.point_item5",
            price_in_krw=39000,
            default_point=50,
            bonus_point=30,
        )
        # Freepass Items
        FreePassItem.objects.create(
            name="원데이 프리패스 (24h)",
            product_id="com.co188.heymatch.free_pass_item1",
            price_in_krw=12000,
            free_pass_duration_in_hour=24,
            best_deal_check=True,
        )
        self.stdout.write(self.style.SUCCESS("Successfully set up data for [Payments]"))

    def generate_app_info_item(self) -> None:
        AppInfo.objects.create(
            faq_url="",
            terms_of_service_url="https://meowing-yew-938.notion.site/2f51b1339cfb407e93c13eba311f8c54",
            privacy_policy_url="https://meowing-yew-938.notion.site/55160a02379a4bcd9dd28b4c1aced5db",
            terms_of_location_service_url="https://meowing-yew-938.notion.site/1d45f72c0e42499f80e5749974dd065d",
            business_registration_url="https://meowing-yew-938.notion.site/28ec816aa9e54771991c843f2689ca6e",
        )
        self.stdout.write(self.style.SUCCESS("Successfully set up data for [AppInfo]"))
