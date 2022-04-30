import datetime
from random import randint
from typing import Any, Sequence

from factory import post_generation
from factory.django import DjangoModelFactory
from factory.faker import Faker

from heythere.apps.group.models import Group
from heythere.utils.util import generate_rand_geopt, generate_rand_int4range


class ActiveGroupFactory(DjangoModelFactory):
    # Group GPS
    gps_geo_location = generate_rand_geopt()
    gps_checked = True
    gps_last_check_time = Faker("date")

    # Group Profile
    title = Faker("sentence")
    introduction = Faker("paragraph", nb_sentences=3)
    desired_other_group_member_number = Faker("pyint", min_value=1, max_value=5)
    desired_other_group_member_avg_age_range = generate_rand_int4range(
        randint(20, 29), randint(30, 50)
    )

    # Group Lifecycle
    is_active = True
    active_until = datetime.datetime.today() + datetime.timedelta(days=1)

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
        manager = cls._get_manager(model_class)
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create(**kwargs)
