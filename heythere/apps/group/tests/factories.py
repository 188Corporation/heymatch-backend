import datetime
from typing import Any, Sequence

import pytz
from django.conf import settings
from factory import post_generation
from factory.django import DjangoModelFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyDateTime

from heythere.apps.group.models import Group
from heythere.utils.util import FuzzyGeoPt, FuzzyInt4Range


class ActiveGroupFactory(DjangoModelFactory):
    # Group GPS
    gps_geo_location = FuzzyGeoPt(precision=5)
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

    class Meta:
        model = Group

    @post_generation
    def members(self, create: bool, extracted: Sequence[Any], **kwargs):
        if not create:
            return

        if extracted:
            for i, member in enumerate(extracted):
                if i == 0:
                    member.is_group_leader = True
                member.joined_group = self
                member.save()

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = Group.active_objects
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create(**kwargs)
