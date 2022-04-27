from django.core import management
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django_google_maps.fields import GeoPt
from phone_verify.models import SMSVerification

from heythere.apps.search.models import HotPlace
from heythere.apps.user.models import User

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

        # Superuser setup #
        # --------------------------------------- #
        try:
            User.objects.create_superuser(  # superuser
                username="admin", phone_number="+8212341234", password="1234"
            )
        except IntegrityError:
            pass
        # --------------------------------------- #
        self.stdout.write(
            self.style.SUCCESS("Successfully set up data for [Superuser]")
        )

        # User setup #
        # --------------------------------------- #
        try:
            User.objects.create_user(  # user 1
                username="jin",
                phone_number="+821032433994",
                password="Wjdwls93@",
            )
        except IntegrityError:
            pass
        SMSVerification.objects.get_or_create(  # sms for user 1
            phone_number="+821032433994",
            defaults={
                "security_code": "123456",
                "session_token": "sessiontoken1",
                "is_verified": True,
            },
        )
        # --------------------------------------- #
        self.stdout.write(self.style.SUCCESS("Successfully set up data for [User]"))

        # Hotplace setup #
        # --------------------------------------- #
        HotPlace.objects.get_or_create(  # hotplace 1
            name="압구정 로데오",
            defaults={
                "zone_color": "#1A41C7",
                "zone_boundary_info": [
                    GeoPt(37.530342, 127.0384723),
                    GeoPt(37.5286403, 127.0360262),
                    GeoPt(37.5232287, 127.036627),
                ],
            },
        )
        self.stdout.write(self.style.SUCCESS("Successfully set up data for [Hotplace]"))
