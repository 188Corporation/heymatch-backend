import pathlib
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from factory.django import ImageField
from phone_verify.models import SMSVerification
from tqdm import tqdm

from heymatch.apps.celery.tasks import aggregate_recent_24hr_top_ranked_group_address
from heymatch.apps.group.models import GroupV2
from heymatch.apps.group.tests.factories import (
    ActiveGroupFactory,
    GroupMemberFactory,
    GroupProfileImageFactory,
    GroupV2Factory,
    profile_image_filepath,
)
from heymatch.apps.hotplace.tests.factories import (
    RANDOM_HOTPLACE_INFO,
    RANDOM_HOTPLACE_NAMES,
    HotPlaceFactory,
)
from heymatch.apps.payment.models import PointItem
from heymatch.apps.user.models import AppInfo
from heymatch.apps.user.tests.factories import (
    ActiveUserFactory,
    UserProfileImageFactory,
)
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

        # -------------- Developer Users setup -------------- #
        if migrate_all or input("Create Developer User? [y/N]") == "y":
            self.generate_developer_users()

        # -------------- Normal Users setup -------------- #
        if migrate_all or input("Create Normal User? [y/N]") == "y":
            self.generate_normal_users()

        # -------------- Hotplace, Group, Users setup -------------- #
        if migrate_all or input("Create Groups? [y/N]") == "y":
            self.generate_groups()

        # -------------- Payment setup -------------- #
        if migrate_all or input("Create Payments? [y/N]") == "y":
            self.generate_payment_items()

        # -------------- Recent24HrTopGroupAddress setup -------------- #
        if migrate_all or input("Create Recent24HrTopGroupAddress? [y/N]") == "y":
            self.generate_24hr_top_group_address()

        # -------------- AppInfo setup -------------- #
        if migrate_all or input("Create App info? [y/N]") == "y":
            self.generate_app_info_item()

        # -------------- Done! -------------- #
        self.stdout.write(self.style.SUCCESS("Successfully set up all mocking data!"))

    def generate_superuser(self) -> None:
        self.stdout.write(self.style.SUCCESS("Setting up data for [Superuser]"))
        try:
            User.objects.create_superuser(  # superuser
                username=settings.DJANGO_ADMIN_ID,
                phone_number="+821000000000",
                password=settings.DJANGO_ADMIN_PASSWORD,
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

    def generate_developer_users(self) -> None:
        self.stdout.write(self.style.SUCCESS("Setting up data for [Developer]"))
        users = [
            ActiveUserFactory.create(phone_number="+821043509595"),
            ActiveUserFactory.create(phone_number="+821032433994"),
        ]
        for user in users:
            UserProfileImageFactory.create(
                user=user,
                image=ImageField(
                    from_path=f"{pathlib.Path().resolve()}/heymatch/data/{random.choice(profile_image_filepath)}"
                ),
            )

    def generate_normal_users(self) -> None:
        self.stdout.write(self.style.SUCCESS("Setting up data for [Users]"))
        users = ActiveUserFactory.create_batch(size=2)
        for user in users:
            UserProfileImageFactory.create(
                user=user,
                image=ImageField(
                    from_path=f"{pathlib.Path().resolve()}/heymatch/data/{random.choice(profile_image_filepath)}"
                ),
            )

    def generate_groups(self) -> None:
        # Invite Groups
        self.stdout.write(self.style.SUCCESS("Setting up data for [Groups.INVITE]"))
        SIZE = 500 if not settings.DEBUG else 20
        # pbar = tqdm(total=SIZE)
        # groups = GroupV2Factory.create_batch(size=SIZE, mode=GroupV2.GroupMode.INVITE)
        # for group in groups:
        #     users = ActiveUserFactory.create_batch(size=random.choice([2, 3, 4]))
        #     for idx, user in enumerate(users):
        #         UserProfileImageFactory.create(
        #             user=user,
        #             image=ImageField(
        #                 from_path=f"{pathlib.Path().resolve()}/heymatch/data/{random.choice(profile_image_filepath)}"
        #             ),
        #         )
        #         is_leader = False
        #         if idx == 0:
        #             is_leader = True
        #         GroupMemberFactory.create(
        #             group=group, user=user, is_user_leader=is_leader
        #         )
        #     pbar.update(1)
        # pbar.close()
        # Simple Groups
        self.stdout.write(self.style.SUCCESS("Setting up data for [Groups.SIMPLE]"))
        pbar = tqdm(total=SIZE)
        groups = GroupV2Factory.create_batch(size=SIZE, mode=GroupV2.GroupMode.SIMPLE)
        for group in groups:
            user = ActiveUserFactory.create()
            UserProfileImageFactory.create(
                user=user,
                image=ImageField(
                    from_path=f"{pathlib.Path().resolve()}/heymatch/data/{random.choice(profile_image_filepath)}"
                ),
            )
            GroupMemberFactory.create(group=group, user=user, is_user_leader=True)
            pbar.update(1)
        pbar.close()

    def generate_payment_items(self) -> None:
        self.stdout.write(self.style.SUCCESS("Setting up data for [Payments]"))
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
        # FreePassItem.objects.create(
        #     name="원데이 프리패스 (24h)",
        #     product_id="com.co188.heymatch.free_pass_item1",
        #     price_in_krw=12000,
        #     free_pass_duration_in_hour=24,
        #     best_deal_check=True,
        # )

    def generate_24hr_top_group_address(self) -> None:
        self.stdout.write(
            self.style.SUCCESS("Setting up data for [Recent24HrTopGroupAddress]")
        )
        aggregate_recent_24hr_top_ranked_group_address()

    def generate_app_info_item(self) -> None:
        self.stdout.write(self.style.SUCCESS("Setting up data for [AppInfo]"))
        faq = "https://docs.google.com/forms/d/e/1FAIpQLScJwGBy92H9EoZagufzgBXGSwtN1dOxQbfctVnNPa1kOocACA/viewform"
        AppInfo.objects.create(
            faq_url=faq,
            terms_of_service_url="https://www.hey-match.com/agreement",
            privacy_policy_url="https://www.hey-match.com/privacy-terms",
            terms_of_location_service_url="https://www.hey-match.com/location-terms",
            business_registration_url="https://www.hey-match.com/corporate",
        )

    # DEPRECATED
    def generate_hotplace_groups(self) -> None:
        for name in RANDOM_HOTPLACE_NAMES:
            # create hotplace
            hotplace = HotPlaceFactory(
                name=name,
                zone_center_geoinfo=RANDOM_HOTPLACE_INFO[name]["zone_center_geoinfo"],
                zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[name][
                    "zone_boundary_geoinfos"
                ],
                zone_boundary_geoinfos_for_fake_chat=RANDOM_HOTPLACE_INFO[name][
                    "zone_boundary_geoinfos_for_fake_chat"
                ],
            )
            # create groups for each hotplaces
            for image_path in profile_image_filepath:
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
                        from_path=f"{pathlib.Path().resolve()}/heymatch/data/{image_path}"
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
