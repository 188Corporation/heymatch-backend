from typing import Any, Sequence

from django.db.utils import IntegrityError
from factory import Faker, SubFactory, post_generation
from factory.django import DjangoModelFactory, ImageField
from unique_names_generator import get_random_name

from heymatch.apps.user.models import (
    MAX_HEIGHT_CM,
    MIN_HEIGHT_CM,
    User,
    UserOnBoarding,
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
    username = Faker(
        "random_element", elements=[get_random_name() for i in range(1000)]
    )
    phone_number = Faker("phone_number", locale="ko_KR")
    birthdate = Faker("date_of_birth")
    height_cm = Faker("pyint", min_value=MIN_HEIGHT_CM, max_value=MAX_HEIGHT_CM)

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
        seed = 0
        orig_username = kwargs["username"]
        while True:
            try:
                instance = manager.create(**kwargs)
                UserOnBoarding.objects.create(
                    user=instance,
                    onboarding_completed=True,
                )
                return instance
            except IntegrityError:
                kwargs["username"] = f"{orig_username}_{seed}"
                seed += 1


# class ActiveDeveloperUserFactory(ActiveUserFactory):
#     @classmethod
#     def _create(cls, model_class, *args, **kwargs):
#         """Override the default ``_create`` with our custom call."""
#         manager = User.active_objects
#         # developer should have getstream registered.
#         return manager.create(**kwargs)


class _ActiveMaleUserFactory(ActiveUserFactory):
    gender = User.GenderChoices.MALE
    birthdate = Faker(
        "random_element",
        elements=[
            "1993-03-01",
            "1992-03-01",
            "1995-03-01",
            "1994-03-01",
            "1991-03-01",
            "1996-03-01",
            "1990-03-01",
        ],
    )
    height_cm = Faker("random_element", elements=[178, 179, 180, 183, 185, 186])
    male_body_form = Faker("random_element", elements=["thin", "normal"])
    female_body_form = None


class _ActiveFemaleUserFactory(ActiveUserFactory):
    gender = User.GenderChoices.FEMALE
    birthdate = Faker(
        "random_element",
        elements=[
            "1995-03-01",
            "1994-03-01",
            "1996-03-01",
            "1997-03-01",
            "1998-03-01",
            "1992-03-01",
            "1991-03-01",
        ],
    )
    height_cm = Faker("random_element", elements=[164, 165, 166, 167, 168, 170])
    male_body_form = None
    female_body_form = Faker("random_element", elements=["thin", "slender"])


class ActiveCollegeMaleUserFactory(_ActiveMaleUserFactory):
    job_title = User.JobChoices.COLLEGE_STUDENT
    verified_school_name = Faker(
        "random_element", elements=["서울대학교", "고려대학교", "연세대학교", "서강대학교", None]
    )
    verified_company_name = None


class ActiveEmployeeMaleUserFactory(_ActiveMaleUserFactory):
    job_title = User.JobChoices.EMPLOYEE
    verified_school_name = None
    verified_company_name = Faker(
        "random_element",
        elements=["현대자동차", "LG 디스플레이", "구글코리아", "아마존코리아", "스타트업", "삼성전자", None],
    )


class ActivePractitionerMaleUserFactory(_ActiveMaleUserFactory):
    job_title = User.JobChoices.PRACTITIONER
    verified_school_name = None
    verified_company_name = Faker("random_element", elements=["의사", "회계사", "변호사", "약사"])


class ActiveEtcMaleUserFactory(_ActiveMaleUserFactory):
    job_title = Faker(
        "random_element",
        elements=[
            User.JobChoices.BUSINESSMAN,
            User.JobChoices.ETC,
            User.JobChoices.PART_TIME,
            User.JobChoices.SELF_EMPLOYED,
        ],
    )
    verified_school_name = None
    verified_company_name = None


class ActiveCollegeFemaleUserFactory(_ActiveFemaleUserFactory):
    job_title = User.JobChoices.COLLEGE_STUDENT
    verified_school_name = Faker(
        "random_element", elements=["서울대학교", "고려대학교", "연세대학교", "서강대학교", None]
    )
    verified_company_name = None


class ActiveEmployeeFemaleUserFactory(_ActiveFemaleUserFactory):
    job_title = User.JobChoices.EMPLOYEE
    verified_school_name = None
    verified_company_name = Faker(
        "random_element", elements=["대한항공", "LG 디스플레이", "아모레퍼시픽", "스타트업", "삼성전자", None]
    )


class ActivePractitionerFemaleUserFactory(_ActiveFemaleUserFactory):
    job_title = User.JobChoices.PRACTITIONER
    verified_school_name = None
    verified_company_name = Faker("random_element", elements=["의사", "회계사", "변호사", "약사"])


class ActiveEtcFemaleUserFactory(_ActiveFemaleUserFactory):
    job_title = Faker(
        "random_element",
        elements=[
            User.JobChoices.BUSINESSMAN,
            User.JobChoices.ETC,
            User.JobChoices.PART_TIME,
            User.JobChoices.SELF_EMPLOYED,
        ],
    )
    verified_school_name = None
    verified_company_name = None


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
    is_active = True


class InactiveUserFactory(ActiveUserFactory):
    is_active = False
    # joined_group = None


class AdminUserFactory(ActiveUserFactory):
    is_staff = True
    is_superuser = True
