import pathlib
import random

from django.conf import settings
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
from heymatch.apps.hotplace.tests.factories import (
    RANDOM_HOTPLACE_INFO,
    RANDOM_HOTPLACE_NAMES,
    HotPlaceFactory,
)
from heymatch.apps.user.tests.factories import ActiveUserFactory, InactiveUserFactory
from heymatch.utils.util import generate_rand_geoopt_within_boundary

User = get_user_model()
stream = settings.STREAM_CLIENT

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

    def handle(self, *args, **options):
        """Rest DB and migrate"""

        if options["reset_db"]:
            if options["noinput"]:
                management.call_command("reset_db", "--noinput")
            else:
                management.call_command("reset_db")
        # it is user's responsibility
        management.call_command("migrate", "--noinput")

        # -------------- Superuser setup -------------- #
        self.generate_superuser()
        # self.generate_developer_users()

        # -------------- Normal Users setup -------------- #
        ActiveUserFactory.create_batch(size=10, joined_group=None)
        InactiveUserFactory.create_batch(size=10)  # "joined_group=None" by default
        self.stdout.write(
            self.style.SUCCESS("Successfully set up data for [Users(Active, Inactive)]")
        )

        # -------------- Hotplace, Group, Users setup -------------- #
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
            for _ in range(random.randint(3, 5)):
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
                users = ActiveUserFactory.create_batch(
                    size=random.randint(2, 5),
                    joined_group=group,
                )
                Group.objects.register_group_leader_user(group, users[0])
                Group.objects.register_normal_users(group, users[1:])

        self.stdout.write(
            self.style.SUCCESS("Successfully set up data for [Hotplaces/Groups/User]")
        )

        # -------------- Done! -------------- #
        self.stdout.write(self.style.SUCCESS("Successfully set up all mocking data!"))

    def generate_superuser(self) -> None:
        try:
            u = User.objects.create_superuser(  # superuser
                username="admin", phone_number="+821000000000", password="1234"
            )
            # Register Stream token
            stream.upsert_user({"id": str(u.id), "role": "user"})
        except IntegrityError:
            u = User.objects.get(username="admin")
            stream.upsert_user({"id": str(u.id), "role": "user"})
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
        try:
            u = User.objects.create_superuser(  # user 1
                username="developer1",
                phone_number="+821032433994",
                password="1234",
            )
            # Register Stream token
            stream.upsert_user({"id": str(u.id), "role": "user"})

        except IntegrityError:
            u = User.objects.get(username="developer1")
            stream.upsert_user({"id": str(u.id), "role": "user"})
            self.stdout.write(
                self.style.NOTICE(
                    "Integrity Error @ {}".format("generate_developer_users")
                )
            )
            pass
        SMSVerification.objects.get_or_create(  # sms for user 1
            phone_number="+821032433994",
            defaults={
                "security_code": "123456",
                "session_token": "sessiontoken1",
                "is_verified": True,
            },
        )
        self.stdout.write(
            self.style.SUCCESS("Successfully set up data for [Users(Developer)]")
        )
