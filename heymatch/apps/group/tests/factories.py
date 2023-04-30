import datetime

from factory import SubFactory
from factory.django import DjangoModelFactory, ImageField
from factory.faker import Faker
from factory.fuzzy import FuzzyDate, FuzzyDateTime

from heymatch.apps.group.models import Group, GroupMember, GroupProfileImage, GroupV2
from heymatch.apps.hotplace.tests.factories import HotPlaceFactory
from heymatch.apps.user.tests.factories import ActiveUserFactory
from heymatch.utils.util import FuzzyGeoPt, FuzzyPointGangnam

TITLE_CHOICES = [
    "압구정 2:2 보실분!!",
    "저희 부산에서 놀라왔어요~~",
    "훈남 3명 (의, 약, 대기업) 대기중",
    "이거 뭐에요~~?? 놀아요!!",
    "잘생긴 오빠들만 :D",
]

INTRO_CHOICES = [
    "일주일 후에 압구정 레스토랑 예약해뒀어요~ 같이 얘기나눠요~~",
    "평균 키 180 이상, 의사 약사 외국계 대기업 종사자입니당 ㅎㅎ 아무나 연락 줘요~~",
    "안녕하세요!! 저희랑 재밌게 놀아요~",
    "이런거 처음 올려보지만... 재밌어 보여서 ㅎㅎㅎ 시간 되시는 분들 만나서 재밌게 놀아요!!",
]


class GroupV2Factory(DjangoModelFactory):
    class Meta:
        model = GroupV2

    mode = Faker("random_element", elements=[x[0] for x in GroupV2.GroupMode.choices])
    title = Faker("random_element", elements=TITLE_CHOICES)
    introduction = Faker("random_element", elements=INTRO_CHOICES)
    meetup_date = FuzzyDate(
        start_date=datetime.date.today(),
        end_date=datetime.date.today() + datetime.timedelta(days=10),
    )
    meetup_timerange = Faker(
        "random_element", elements=[x[0] for x in GroupV2.MeetUpTimeRange.choices]
    )
    gps_point = FuzzyPointGangnam()
    # gps_geoinfo = FuzzyGeoPt(precision=5)
    created_at = FuzzyDateTime(
        start_dt=datetime.datetime.now(tz=datetime.timezone.utc)
        - datetime.timedelta(days=10),
        end_dt=datetime.datetime.now(tz=datetime.timezone.utc),
    )

    # Group Lifecycle
    is_active = True


class GroupMemberFactory(DjangoModelFactory):
    class Meta:
        model = GroupMember

    group = SubFactory(GroupV2Factory)
    user = SubFactory(ActiveUserFactory)


class ActiveGroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    hotplace = SubFactory(HotPlaceFactory)
    # Group GPS
    gps_geoinfo = FuzzyGeoPt(precision=5)
    # gps_checked = True
    # gps_last_check_time = FuzzyDateTime(
    #     start_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    #              - datetime.timedelta(hours=10),
    # )

    # Group Profile
    title = Faker("sentence")
    introduction = Faker("paragraph", nb_sentences=3)
    male_member_number = Faker("pyint", min_value=2, max_value=3)
    female_member_number = Faker("pyint", min_value=0, max_value=2)
    member_average_age = Faker("pyint", min_value=20, max_value=35)
    # desired_other_group_member_number = Faker("pyint", min_value=1, max_value=5)
    # desired_other_group_member_avg_age_range = FuzzyInt4Range(low=20, high=60)

    # Group Lifecycle
    is_active = True

    # active_until = FuzzyDateTime(
    #     start_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE)),
    #     end_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    #     + datetime.timedelta(days=1),
    # )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = Group.objects
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create(**kwargs)


class InactiveGroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    is_active = False


profile_image_filepath = [
    "male_profile_1.jpeg",
    "male_profile_2.jpeg",
    "female_profile_1.jpeg",
    "female_profile_2.jpeg",
    "female_profile_3.jpeg",
]


class GroupProfileImageFactory(DjangoModelFactory):
    class Meta:
        model = GroupProfileImage

    group = SubFactory(ActiveGroupFactory)
    image = ImageField()


# ========================
#  DEPRECATED
# ========================
#
# class ActiveGroupInvitationCodeFactory(DjangoModelFactory):
#     class Meta:
#         model = GroupInvitationCode
#
#     user = SubFactory("heymatch.apps.user.tests.factories.ActiveUserFactory")
#     code = FuzzyInteger(1000, 9999)
#     is_active = True
#     active_until = FuzzyDateTime(
#         start_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE)),
#         end_dt=datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
#                + datetime.timedelta(minutes=5),
#     )
