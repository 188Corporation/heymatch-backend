from typing import Any, Sequence

from factory import Faker, post_generation
from factory.django import DjangoModelFactory

from heymatch.apps.user.models import MAX_HEIGHT_CM, MIN_HEIGHT_CM, User

# RANDOM_SCHOOLS = [
#     "서울대학교",
#     "고려대학교",
#     "연세대학교",
#     "카이스트",
#     "서강대학교",
#     "한양대학교",
#     "성균관대학교",
#     "Harvard University",
#     "Stanford University",
#     "Yale University",
#     "Cornell University",
# ]


class ActiveUserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    id = Faker("uuid4")
    phone_number = Faker("phone_number", locale="ko_KR")
    birthdate = Faker("date_of_birth")
    gender = Faker(
        "random_element", elements=[x[0] for x in User.GenderChoices.choices]
    )
    height_cm = Faker("pyint", min_value=MIN_HEIGHT_CM, max_value=MAX_HEIGHT_CM)
    male_body_form = Faker(
        "random_element", elements=[x[0] for x in User.MaleBodyFormChoices.choices]
    )
    female_body_form = Faker(
        "random_element", elements=[x[0] for x in User.FemaleBodyFormChoices.choices]
    )
    # workplace = Faker("company", locale="ko_KR")
    # school = Faker("random_element", elements=RANDOM_SCHOOLS)

    # Group related
    # joined_group = SubFactory(ActiveGroupFactory)
    # is_group_leader = False

    # Other
    is_active = True
    agreed_to_terms = True

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

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = User.active_objects
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create(**kwargs)


class InactiveUserFactory(ActiveUserFactory):
    is_active = False
    joined_group = None


class AdminUserFactory(ActiveUserFactory):
    is_staff = True
    is_superuser = True
