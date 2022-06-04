import random

from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from phone_verify.models import SMSVerification

from heythere.apps.group.models import Group
from heythere.apps.group.tests.factories import ActiveGroupFactory
from heythere.apps.search.tests.factories import (
    RANDOM_HOTPLACE_INFO,
    RANDOM_HOTPLACE_NAMES,
    HotPlaceFactory,
)
from heythere.apps.user.tests.factories import ActiveUserFactory, InactiveUserFactory
from heythere.utils.util import generate_rand_geoopt_within_boundary

User = get_user_model()

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
        self.generate_developer_users()

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
                # create users for each groups
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
            User.objects.create_superuser(  # superuser
                username="admin", phone_number="+821012341234", password="1234"
            )
        except IntegrityError:
            self.stdout.write(
                self.style.NOTICE("Integrity Error @ {}".format("create_superuser"))
            )
            pass
        self.stdout.write(
            self.style.SUCCESS("Successfully set up data for [Superuser]")
        )

    def generate_developer_users(self) -> None:
        try:
            User.objects.create_user(  # user 1
                username="developer1",
                phone_number="+821032433994",
                password="1234",
            )
        except IntegrityError:
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
