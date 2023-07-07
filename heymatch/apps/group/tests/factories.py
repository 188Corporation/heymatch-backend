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

FEMALE_REAL_CHOICES = [
    {
        "title": "엇 신기한 앱이 생겼당ㅎㅎ",
        "introduction": "이거 뭔가영 ㅎㅎㅎ 저희 2명이고요 25, 26, 24 이에용..ㅎㅎ 압구정이나 한남에서 미팅하실 분 구해요!!",
        "member_number": 2,
        "member_avg_age": 25,
    },
    {
        "title": "이거 뭐야ㅋㅋㅋ 역삼 직장인들 퇴근하고 한잔 고?",
        "introduction": "빠퇴하고 싶네요.. 무엇을 적어야할까.. 고민고민고민고민 미팅해여미팅~~",
        "member_number": 3,
        "member_avg_age": 26,
    },
    {
        "title": "훈남들 매칭 걸어줭~~ 저희 솔로임ㅋㅋ",
        "introduction": "훈남들만 받아요. 저희 외로워요. 같이 놀아요. 친구들 대기중. 빨리빨리!!",
        "member_number": 2,
        "member_avg_age": 29,
    },
    {
        "title": "이거 뭐에요~~?? 같이 놀아요 💗",
        "introduction": "저희 아직 학생이에용 언니랑 동생 두명 있어요. 매칭걸어줘용!",
        "member_number": 3,
        "member_avg_age": 24,
    },
    {
        "title": "잘생긴 오빠들만 연락해 ㅋㅋ",
        "introduction": "진짜 잘생긴 오빠들만 연락해랑.. 키 180이상 훈남들만. 미팅구함",
        "member_number": 2,
        "member_avg_age": 28,
    },
    {
        "title": "여의도 직장인 모여모영~",
        "introduction": "여의도 간맥하면 좋겠당 ㅎㅎ 관심있는 분들 매칭 보내줘용~~",
        "member_number": 3,
        "member_avg_age": 31,
    },
    {
        "title": "다음주쯤에 간맥하실분 없나요!!",
        "introduction": "장소는 그냥 서울 아무데서나???? 우리 3명인데 한명 늘어날수도 있어요~~",
        "member_number": 3,
        "member_avg_age": 27,
    },
    {
        "title": "그룹명을 신박하게 적고 싶은데..ㅎ",
        "introduction": "그룹명을 뭘 적어야할까.... 무엇을 적어야할까... 생각이 나지 않는다.. 그냥 좀 생긴 오빠들 연락줭",
        "member_number": 2,
        "member_avg_age": 26,
    },
    {
        "title": "야근 좀 그만 시켜줘..🥲",
        "introduction": "야근 죽이고 싶다. 퇴근하고 강남권 2명 연락줭용...ㅎㅎㅎㅎㅎ",
        "member_number": 2,
        "member_avg_age": 28,
    },
    {
        "title": "청담 맛집 잘 아시는분~",
        "introduction": "청담, 압구정 맛집 잘 아시는분!! 저희 3명인데 미팅 고고링~",
        "member_number": 3,
        "member_avg_age": 30,
    },
    {
        "title": "2:2 미팅 렛츠고고",
        "introduction": "우리 2명인데요~~ 그냥 아무나 매칭 걸어줘요!!",
        "member_number": 2,
        "member_avg_age": 27,
    },
]

MALE_REAL_CHOICES = [
    {
        "title": "빨리 매칭 걸어줘요 현기증 나요",
        "introduction": "빨리 매칭 걸어줘요 현기증 나요 누나들!!!",
        "member_number": 2,
        "member_avg_age": 27,
    },
    {
        "title": "의,약 훈남 3명이요",
        "introduction": "의사 약사 약사입니다 180 177 182 이구요 사진은 일단 매칭걸고 ㄱㄱ",
        "member_number": 3,
        "member_avg_age": 28,
    },
    {
        "title": "우리 훈남 2명이랑 미팅하실분ㅎ",
        "introduction": "우리 훈남임 믿고 매칭 걸어바바~~ 20자 채우기 채우기 채우기",
        "member_number": 2,
        "member_avg_age": 29,
    },
    {
        "title": "강남 직장인들 퇴근 후 달려갈 준비중ㅎ",
        "introduction": "강남 논현 역삼 삼성 다 가능 말만해요 저희 달려감 미팅 고고링",
        "member_number": 3,
        "member_avg_age": 32,
    },
    {
        "title": "이거 뭡니까",
        "introduction": "이거 뭡니까 이거 뭡니까 노실분들 매칭 고고고고",
        "member_number": 2,
        "member_avg_age": 31,
    },
    {
        "title": "ㅋㅋㅋ 뭘 적어야할까용 우리 좀 생겼다..?",
        "introduction": "우리 좀 생겼어요 사진 봐바요 맞죠? 그니까 매칭 걸어봐요~~",
        "member_number": 3,
        "member_avg_age": 30,
    },
    {
        "title": "야근하기 싫당..",
        "introduction": "야근 그만 하고 싶다.. 날씨도 너무 덥다 재밌게 놀고 싶다",
        "member_number": 3,
        "member_avg_age": 29,
    },
    {
        "title": "다들 금요일에 뭐해용 ㅎㅎ",
        "introduction": "금욜에 퇴근하고 강남쪽에서 시간 되시는 분들~~",
        "member_number": 2,
        "member_avg_age": 33,
    },
    {
        "title": "야근 좀 그만 시켜줘..🥲",
        "introduction": "간단하게 맥주 한잔 하실분들 없나용 ㅎㅎ 저희 2명입니당",
        "member_number": 2,
        "member_avg_age": 32,
    },
    {
        "title": "외국계 훈훈 2명 미팅하실분~~",
        "introduction": "훈훈한 외국계 다니는 29 31 대기중이요~~~ 미팅하실분 연락줘요!!",
        "member_number": 3,
        "member_avg_age": 30,
    },
]

INTRO_CHOICES = [
    "일주일 후에 압구정 레스토랑 예약해뒀어요~ 같이 얘기나눠요~~",
    "평균 키 180 이상, 의사 약사 외국계 대기업 종사자입니당 ㅎㅎ 아무나 연락 줘요~~",
    "안녕하세요!! 저희랑 재밌게 놀아요~",
    "이런거 처음 올려보지만... 재밌어 보여서 ㅎㅎㅎ 시간 되시는 분들 만나서 재밌게 놀아요!!",
]
MEETUP_PLACE_TITLE_CHOICES = [
    "신사동 주민센터",
    "압구정 포차",
    "성수동 주민센터",
    "한남동 주민센터",
]
MEETUP_PLACE_ADDR_CHOICES = [
    "서울특별시 강남구 압구정로 173 3층",
    "서울특별시 강남구 역삼1길 199-1",
    "서울특별시 성동구 성수동로 300",
    "서울특별시 용산구 한강로3가 11-34",
]

GPS_ADDR_CHOICES = [
    "서울특별시 강남구 압구정동",
    "서울특별시 강남구 역삼동",
    "서울특별시 성동구 성수동",
    "서울특별시 용산구 한남동",
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
    meetup_place_title = Faker("random_element", elements=MEETUP_PLACE_TITLE_CHOICES)
    meetup_place_address = Faker("random_element", elements=MEETUP_PLACE_ADDR_CHOICES)
    gps_point = FuzzyPointGangnam()
    gps_address = Faker("random_element", elements=GPS_ADDR_CHOICES)
    # gps_geoinfo = FuzzyGeoPt(precision=5)
    member_number = Faker("pyint", min_value=2, max_value=6)
    member_avg_age = Faker("pyint", min_value=22, max_value=35)
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


male_profile_image_filepath = [
    "male_profile_1.jpeg",
    "male_profile_2.jpeg",
    "male_profile_3.jpeg",
    "male_profile_4.jpeg",
    "male_profile_5.jpeg",
    "male_profile_6.jpeg",
    "male_profile_7.jpeg",
    "male_profile_8.jpeg",
    "male_profile_9.jpeg",
    "male_profile_10.jpeg",
]

female_profile_image_filepath = [
    "female_profile_1.jpeg",
    "female_profile_2.jpeg",
    "female_profile_3.jpeg",
    "female_profile_4.jpeg",
    "female_profile_5.jpeg",
    "female_profile_6.jpeg",
    "female_profile_7.jpeg",
    "female_profile_8.jpeg",
    "female_profile_9.jpeg",
    "female_profile_10.jpeg",
    "female_profile_11.jpeg",
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
