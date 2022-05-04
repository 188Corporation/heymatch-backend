import random
from typing import Any, Sequence

from django.contrib.auth import get_user_model
from factory import Faker
from factory import Sequence as FactorySequence
from factory import post_generation
from factory.django import DjangoModelFactory

from heythere.apps.user.models import GENDER_CHOICES, MAX_HEIGHT_CM, MIN_HEIGHT_CM, User

RANDOM_SCHOOLS = ["서울대학교", "고려대학교", "연세대학교"]


class UserFactory(DjangoModelFactory):
    username = FactorySequence(lambda n: "username{}".format(n))  # Unique values
    phone_number = Faker("phone_number", locale="ko_KR")
    birthdate = Faker("date_of_birth")
    gender = Faker("random_element", elements=[x[0] for x in GENDER_CHOICES])
    height_cm = Faker("pyint", min_value=MIN_HEIGHT_CM, max_value=MAX_HEIGHT_CM)
    workplace = Faker("company", locale="ko_KR")
    school = Faker("random_element", elements=RANDOM_SCHOOLS)

    # Group related
    is_group_leader = random.choice([True, False])

    # Other
    is_active = random.choice([True, False])

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ("username",)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = User.active_objects
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create(**kwargs)


class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True
