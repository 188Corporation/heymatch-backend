from typing import Any, Sequence

from factory import Faker, SubFactory, post_generation
from factory.django import DjangoModelFactory, ImageField

from heymatch.apps.user.models import (
    MAX_HEIGHT_CM,
    MIN_HEIGHT_CM,
    User,
    UserProfileImage,
)
from heymatch.utils.util import load_company_domain_file, load_school_domain_file

COMPANY_DOMAIN_FILE = load_company_domain_file()
SCHOOL_DOMAIN_FILE = load_school_domain_file()


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
    job_title = Faker(
        "random_element", elements=[x[0] for x in User.JobChoices.choices]
    )
    verified_school_name = Faker(
        "random_element", elements=["서울대학교", "고려대학교", "연세대학교", "서강대학교", None]
    )
    verified_company_name = Faker(
        "random_element", elements=["Amazon", "스타트업", "삼성전자", None]
    )

    # Other
    is_temp_user = False
    is_active = True

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
        return manager.fake_create(**kwargs)


profile_image_filepath = [
    "male_profile_1.jpeg",
    "male_profile_2.jpeg",
    "female_profile_1.jpeg",
    "female_profile_2.jpeg",
    "female_profile_3.jpeg",
]


class UserProfileImageFactory(DjangoModelFactory):
    class Meta:
        model = UserProfileImage

    user = SubFactory(ActiveUserFactory)
    image = ImageField()

    status = UserProfileImage.StatusChoices.ACCEPTED
    is_main = True


class InactiveUserFactory(ActiveUserFactory):
    is_active = False
    # joined_group = None


class AdminUserFactory(ActiveUserFactory):
    is_staff = True
    is_superuser = True
