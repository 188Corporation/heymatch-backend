import datetime

import pytz
from django.conf import settings
from factory import SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyDateTime, FuzzyInteger

from heythere.apps.group.models import Group, GroupInvitationCode
from heythere.utils.util import FuzzyGeoPt, FuzzyInt4Range


class ActiveGroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    # Group GPS
    gps_geoinfo = FuzzyGeoPt(precision=5)
    gps_checked = True
    gps_last_check_time = FuzzyDateTime(
        start_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
        - datetime.timedelta(hours=10),
    )

    # Group Profile
    title = Faker("sentence")
    introduction = Faker("paragraph", nb_sentences=3)
    desired_other_group_member_number = Faker("pyint", min_value=1, max_value=5)
    desired_other_group_member_avg_age_range = FuzzyInt4Range(low=20, high=60)

    # Group Lifecycle
    is_active = True
    active_until = FuzzyDateTime(
        start_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE)),
        end_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
        + datetime.timedelta(days=1),
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = Group.active_objects
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create(**kwargs)


class InactiveGroupFactory(ActiveGroupFactory):
    is_active = False


class ActiveGroupInvitationCodeFactory(DjangoModelFactory):
    class Meta:
        model = GroupInvitationCode

    user = SubFactory("heythere.apps.user.tests.factories.ActiveUserFactory")
    code = FuzzyInteger(1000, 9999)
    is_active = True
    active_until = FuzzyDateTime(
        start_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE)),
        end_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
        + datetime.timedelta(minutes=5),
    )
