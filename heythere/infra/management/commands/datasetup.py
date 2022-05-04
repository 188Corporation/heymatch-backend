from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from phone_verify.models import SMSVerification

from heythere.conftest import (
    generate_active_users,
    generate_inactive_users,
    generate_real_hotplaces,
)

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
        # --------------------------------------- #

        # -------------- User setup -------------- #
        # Create Developer Users
        self.generate_developer_users()

        # Create Normal Users (No group)
        generate_active_users()
        generate_inactive_users()

        self.stdout.write(self.style.SUCCESS("Successfully set up data for [User]"))
        # --------------------------------------- #

        # -------------- Hotplace setup -------------- #
        generate_real_hotplaces()  # This will create active groups and users
        self.stdout.write(self.style.SUCCESS("Successfully set up data for [Hotplace]"))
        # --------------------------------------- #

    def generate_developer_users(self) -> None:
        try:
            User.objects.create_user(  # user 1
                username="developer1",
                phone_number="+821032433994",
                password="Wjdwls93@",
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
