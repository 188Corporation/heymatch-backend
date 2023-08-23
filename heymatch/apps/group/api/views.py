from typing import Any

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db.models import (
    Avg,
    Case,
    Count,
    F,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    When,
)
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import (
    CharFilter,
    DateFromToRangeFilter,
    DjangoFilterBackend,
    FilterSet,
    NumberFilter,
)
from django_google_maps.fields import GeoPt
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_gis.filters import DistanceToPointFilter

from heymatch.apps.chat.models import StreamChannel
from heymatch.apps.group.models import (
    Group,
    GroupMember,
    GroupProfilePhotoPurchased,
    GroupV2,
    Recent24HrTopGroupAddress,
    ReportedGroupV2,
)
from heymatch.apps.hotplace.models import HotPlace
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.payment.models import UserPointConsumptionHistory
from heymatch.apps.user.models import User
from heymatch.shared.exceptions import (
    GroupNotWithinSameHotplaceException,
    GroupProfilePhotoAlreadyPurchasedException,
    JoinedGroupNotMineException,
    MatchRequestNotMatchedException,
    OneGroupPerUserException,
    ReportMyGroupException,
    UserGPSNotWithinHotplaceException,
    UserNotGroupLeaderException,
    UserNotJoinedGroupException,
    UserPointBalanceNotEnoughException,
)
from heymatch.shared.permissions import (
    IsGroupCreationAllowed,
    IsUserActive,
    IsUserJoinedGroup,
)
from heymatch.utils.util import NaverGeoAPI, is_geopt_within_boundary

from .serializers import (
    FullGroupProfileByHotplaceSerializer,
    FullGroupProfileSerializer,
    GroupCreationRequestBodySerializer,
    GroupCreationSerializer,
    GroupsTopAddressSerializer,
    GroupUpdateSerializer,
    ReportGroupRequestBodySerializer,
    ReportGroupSerializer,
    RestrictedGroupProfileByHotplaceSerializer,
    V2GroupCreateUpdateSerializer,
    V2GroupFullFieldSerializer,
    V2GroupLimitedFieldSerializer,
)

# User = get_user_model()
stream = settings.STREAM_CLIENT
NAVER_GEO_API = NaverGeoAPI()


class GroupV2Filter(FilterSet):
    meetup_date = DateFromToRangeFilter(field_name="meetup_date")
    # height = RangeFilter(method="filter_avg_heights_in_group")
    # gender = CharFilter(method="filter_gender_type_in_group")
    member_num = NumberFilter(method="filter_member_number_in_group")
    order_by = CharFilter(method="filter_sort_by_in_group")

    class Meta:
        model = GroupV2
        fields = [
            "meetup_date",
        ]

    def filter_avg_heights_in_group(self, queryset, field_name, value):
        # Define subquery to get the height of each user
        if not value:
            return queryset

        height_subquery = Subquery(
            User.objects.filter(id=OuterRef("user_id")).values("height_cm")[:1]
        )
        # Define subquery to get the group IDs
        # group_subquery = Subquery(
        #     GroupV2.objects.filter(id=OuterRef("group_id")).values("id")[:1]
        # )
        # Define subquery to get the average height for each group
        avg_height_subquery = (
            GroupMember.objects.filter(group_id=OuterRef("group_id"))
            .annotate(height_cm=Coalesce(height_subquery, 0))
            .values("group_id")
            .annotate(avg_height=Avg("height_cm", output_field=IntegerField()))
            .values("avg_height")
        )
        # Define the final queryset
        gm_queryset = (
            GroupMember.objects.annotate(height_cm=Coalesce(height_subquery, 0))
            # .annotate(group_anno_id=Coalesce(group_subquery, 0))
            .annotate(avg_height=Coalesce(avg_height_subquery, 0))
            .filter(avg_height__gte=value.start, avg_height__lte=value.stop)
            .distinct("group_id")
        )
        # Get final GroupV2 QS
        queryset = queryset.filter(
            id__in=list(gm_queryset.values_list("group_id", flat=True))
        )
        return queryset

    def filter_member_number_in_group(self, queryset, field_name, value):
        if not value:
            return queryset
        if value < 5:
            return queryset.filter(member_number=value)
        return queryset.filter(member_number__gte=value)

    def filter_sort_by_in_group(self, queryset, field_name, value):
        if not value:
            return queryset
        if value == "meetup_date":
            return queryset.order_by("meetup_date")
        if value == "created_at":
            return queryset.order_by("-created_at")

    # def filter_member_number_in_group(self, queryset, field_name, value):
    #     if not value:
    #         return queryset
    #
    #     # Define a subquery for filtering GroupMembers with Users
    #     group_member_subquery = GroupMember.objects.filter(
    #         user__in=User.objects.all()
    #     ).values("id", "group_id", "user_id")
    #
    #     # Use the subquery to group GroupMembers by group_id
    #     group_member_groups = group_member_subquery.values("group_id").annotate(
    #         total_members=Count("id")
    #     )
    #     # Filter the groups with exactly two members
    #     if value < 5:
    #         groups_with_members = group_member_groups.filter(total_members=value)
    #     else:
    #         groups_with_members = group_member_groups.filter(total_members__gte=value)
    #
    #     # Extract the group ids as a list
    #     queryset = queryset.filter(
    #         id__in=list(groups_with_members.values_list("group_id", flat=True))
    #     )
    #     return queryset

    # def filter_gender_type_in_group(self, queryset, field_name, value):
    #     query_filter = {
    #         "male_only": "m",
    #         "female_only": "f",
    #         "mixed": "x",
    #     }
    #     if not value:
    #         return queryset
    #
    #     if value not in query_filter.keys():
    #         return queryset
    #
    #     # Filter male_only, female_only
    #     if query_filter[value] in ["m", "f"]:
    #         groupmember = (
    #             GroupMember.objects.annotate(
    #                 gender=Subquery(
    #                     User.objects.filter(id=OuterRef("user_id")).values("gender")[:1]
    #                 )
    #             )
    #             .select_related("group")
    #             .values("group_id")
    #             .distinct()
    #         )
    #         gm_queryset = (
    #             groupmember.annotate(num_members=Count("user_id", distinct=True))
    #             .annotate(
    #                 num_target_members=Sum(
    #                     Case(
    #                         When(Q(gender=query_filter[value]), then=1),
    #                         default=0,
    #                         output_field=IntegerField(),
    #                     ),
    #                 )
    #             )
    #             .filter(num_members=F("num_target_members"))
    #         )
    #
    #     # Filter mixed
    #     else:
    #         gm_queryset = (
    #             GroupMember.objects.annotate(
    #                 gender=Subquery(
    #                     User.objects.filter(id=OuterRef("user_id")).values("gender")[:1]
    #                 )
    #             )
    #             .values("group_id")
    #             .annotate(
    #                 num_users=Count("user_id", distinct=True),
    #                 num_male_members=Count(
    #                     Case(
    #                         When(Q(gender="m"), then=1),
    #                         output_field=IntegerField(),
    #                     ),
    #                     distinct=True,
    #                 ),
    #                 num_female_members=Count(
    #                     Case(
    #                         When(Q(gender="f"), then=1),
    #                         output_field=IntegerField(),
    #                     ),
    #                     distinct=True,
    #                 ),
    #             )
    #             .filter(
    #                 num_users__gt=1,
    #                 num_male_members__gt=0,
    #                 num_female_members__gt=0,
    #             )
    #         )
    #
    #     queryset = queryset.filter(
    #         id__in=list(gm_queryset.values_list("group_id", flat=True))
    #     )
    #     return queryset


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 15


class GroupV2GeneralViewSet(viewsets.ModelViewSet):
    queryset = (
        GroupV2.objects.all()
        .filter(is_active=True)
        .prefetch_related(
            "group_member_group",
            "group_member_group__user",
            "group_member_group__user__user_profile_images",
        )
    )
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = V2GroupCreateUpdateSerializer
    distance_filter_field = "gps_point"
    filter_backends = [DjangoFilterBackend, DistanceToPointFilter]
    filterset_class = GroupV2Filter
    pagination_class = StandardResultsSetPagination

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        1) "검색 장소 기준 반경 km" 나누고
            dist=5000&point=127.03952,37.52628
        2) "만남날짜"로 나누고
            meetup_date_after=2023-01-01&meetup_date_before=2023-01-05
        3) "멤버수"로 나누고
            member_num=3
        4) "평균키"로 나누고
            height_min=130&height_max=180
        5) "성별"로 나누고
            gender=male_only or gender=female_only or gender=mixed
        6) 마지막 pagination
            page=3

        예시) 압구정역 기준 반경 5km 내 미팅날짜가 2023-01-01~2023-01-05 사이고 멤버들의 평균키가 130cm-180cm 사이인 그룹들
            GET ../api/groups/
                    ?dist=5000&point=127.03952,37.52628
                    &meetup_date_after=2023-01-01&meetup_date_before=2023-01-05
                    &height_min=130&height_max=180
                    &page=1

        예시2) 압구정역 기준 반경 5km 내 멤버들의 평균키가 130cm-180cm 사이인 남성 그룹들
            GET ../api/groups/
                    ?dist=5000&point=127.03952,37.52628
                    &height_min=130&height_max=180
                    &gender=male_only
                    &page=1
        """
        qs = self.get_queryset()
        filtered_qs = self.filter_queryset(queryset=qs)
        paginated_qs = self.paginate_queryset(filtered_qs)
        purchased_group_ids = GroupProfilePhotoPurchased.objects.filter(
            buyer=request.user
        ).values_list("seller_id", flat=True)
        serializer = V2GroupLimitedFieldSerializer(
            paginated_qs,
            many=True,
            context={"user_purchased_group_profile_ids": list(purchased_group_ids)},
        )
        return self.get_paginated_response(data=serializer.data)

    def get_queryset(self) -> QuerySet:
        qs = self.queryset
        # 0) Exclude same gender groups
        qs = self.filter_other_gender_groups(qs)

        # 1) Exclude my group
        q = Q(user=self.request.user) & Q(is_active=True)

        # 2) Exclude blocked school/company
        #   a) 나의 block_my_school_or_company_users=True일때
        #    - 내꺼랑 똑같은 사람은 exclude하기
        #   b) 나의 block_my_school_or_company_users=False일때
        #    - GroupMember중에 block_my_school_or_company_users=True면서 내꺼랑 똑같은 사람 exclude하기
        my_school_name = self.request.user.verified_school_name
        my_company_name = self.request.user.verified_company_name
        block_q = Q(user__block_my_school_or_company_users=True)
        school_q = Q(user__verified_school_name=my_school_name)
        company_q = Q(user__verified_company_name=my_company_name)

        if not self.request.user.block_my_school_or_company_users:
            if my_school_name:
                q |= block_q & school_q
            if my_company_name:
                q |= block_q & company_q
        else:
            if my_school_name:
                q |= school_q
            if my_company_name:
                q |= company_q

        blocked_group_ids = list(
            GroupMember.objects.filter(q).values_list("group_id", flat=True)
        )

        # 3) Exclude Matched (chat) groups
        # TODO: future job

        # 4) Exclude reported by me groups
        reported_group_ids = list(
            ReportedGroupV2.objects.filter(reported_by=self.request.user).values_list(
                "reported_group_id", flat=True
            )
        )

        return qs.exclude(id__in=reported_group_ids + blocked_group_ids)

    def filter_other_gender_groups(self, queryset):
        other_gender = "m" if self.request.user.gender == "f" else "f"
        groupmember = (
            GroupMember.objects.annotate(
                gender=Subquery(
                    User.objects.filter(id=OuterRef("user_id")).values("gender")[:1]
                )
            )
            .select_related("group")
            .values("group_id")
            .distinct()
        )
        gm_queryset = (
            groupmember.annotate(num_members=Count("user_id", distinct=True))
            .annotate(
                num_target_members=Sum(
                    Case(
                        When(Q(gender=other_gender), then=1),
                        default=0,
                        output_field=IntegerField(),
                    ),
                )
            )
            .filter(num_members=F("num_target_members"))
        )
        queryset = queryset.filter(
            id__in=list(gm_queryset.values_list("group_id", flat=True))
        )
        return queryset

    @swagger_auto_schema(request_body=V2GroupCreateUpdateSerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = self.perform_create(serializer)
        return Response(
            data=V2GroupLimitedFieldSerializer(instance=group).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer) -> GroupV2:
        # Get members
        # qs = User.active_objects.all()
        # user_ids = serializer.validated_data.get("user_ids")
        # parse gps_point
        gps_point = serializer.validated_data.get("gps_point")
        gps = gps_point.split(",")
        serializer.validated_data["gps_point"] = Point(x=float(gps[0]), y=float(gps[1]))
        serializer.validated_data["gps_address"] = NAVER_GEO_API.reverse_geocode(
            long=gps[0], lat=gps[1]
        )

        # INVITE Mode
        # if user_ids:
        #     serializer.validated_data.pop("user_ids")
        #     users = [get_object_or_404(qs, id=user_id) for user_id in user_ids]
        #     group = GroupV2.objects.create(
        #         **serializer.validated_data, mode=GroupV2.GroupMode.INVITE
        #     )
        #     # add myself as group leader
        #     GroupMember.objects.create(
        #         group=group, user=self.request.user, is_user_leader=True
        #     )
        #     for user in users:
        #         GroupMember.objects.create(
        #             group=group,
        #             user=user,
        #         )
        # SIMPLE Mode
        qs = GroupMember.objects.filter(
            user=self.request.user, group__is_active=True, is_active=True
        )
        if qs.exists():
            raise OneGroupPerUserException()

        group = GroupV2.objects.create(
            **serializer.validated_data, mode=GroupV2.GroupMode.SIMPLE
        )
        GroupMember.objects.create(
            group=group, user=self.request.user, is_user_leader=True
        )
        return group


class GroupV2TagsViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
    ]

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        about_group_tags = []
        for tag in GroupV2.GroupWhoWeAreTag.choices:
            split = tag[1].split(",")
            about_group_tags.append(
                {"value": tag[0], "label": split[0], "color": split[1]}
            )

        desired_meeting_tags = []
        for tag in GroupV2.GroupWantToMeetTag.choices:
            split = tag[1].split(",")
            desired_meeting_tags.append(
                {"value": tag[0], "label": split[0], "color": split[1]}
            )

        return Response(
            data={
                "about_group_tags": about_group_tags,
                "desired_meeting_tags": desired_meeting_tags,
            }
        )


class GroupV2DetailViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = V2GroupFullFieldSerializer

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = GroupV2.objects.all().filter(is_active=True)
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        # Check if my group
        if GroupMember.objects.filter(user=request.user, group=group).exists():
            serializer = self.get_serializer(
                instance=group, context={"force_original_image": True}
            )
            purchase_info = {"profile_photo_purchased": True}
            return Response(
                data={**serializer.data, **purchase_info}, status=status.HTTP_200_OK
            )
        # Check whether photo purchased
        purchase_info = {"profile_photo_purchased": False}
        gps = GroupProfilePhotoPurchased.objects.filter(
            seller=group, buyer=request.user
        )
        # if one of case exists, send original profile photo
        if gps.exists():
            purchase_info["profile_photo_purchased"] = True
            serializer = self.get_serializer(
                instance=group, context={"force_original_image": True}
            )
        else:
            serializer = self.get_serializer(instance=group)
        return Response(
            data={**serializer.data, **purchase_info}, status=status.HTTP_200_OK
        )

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # only leader can destroy
        qs = GroupMember.objects.filter(
            user=request.user, group_id=kwargs["group_id"], is_active=True
        )
        if not qs.exists():
            raise JoinedGroupNotMineException()

        gm = qs.first()
        if not gm.is_user_leader:
            raise UserNotGroupLeaderException()

        # Inactivate GroupMember
        gm.is_active = False
        gm.save(update_fields=["is_active"])
        group = gm.group
        # Inactivate MatchRequest
        qs = MatchRequest.active_objects.filter(
            Q(sender_group=group) | Q(receiver_group=group)
        )
        qs.update(is_active=False)
        # Inactivate Group
        group.is_active = False
        group.save(update_fields=["is_active"])
        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=V2GroupCreateUpdateSerializer)
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # only leader can update
        qs = GroupMember.objects.filter(
            user=request.user, group_id=kwargs["group_id"], is_active=True
        )
        if not qs.exists():
            raise JoinedGroupNotMineException()

        gm = qs.first()
        if not gm.is_user_leader:
            raise UserNotGroupLeaderException()

        group = gm.group
        group.title = request.data.get("title", group.title)
        group.introduction = request.data.get("introduction", group.introduction)
        if request.data.get("gps_point", None):
            gps_point = request.data.get("gps_point")
            gps = gps_point.split(",")
            group.gps_point = Point(x=float(gps[0]), y=float(gps[1]))
            group.gps_address = NAVER_GEO_API.reverse_geocode(long=gps[0], lat=gps[1])
        group.meetup_date = request.data.get("meetup_date", group.meetup_date)
        group.meetup_place_title = request.data.get(
            "meetup_place_title", group.meetup_place_title
        )
        group.meetup_place_address = request.data.get(
            "meetup_place_address", group.meetup_place_address
        )
        group.member_number = request.data.get("member_number", group.member_number)
        group.member_avg_age = request.data.get("member_avg_age", group.member_avg_age)
        group.save(
            update_fields=[
                "title",
                "introduction",
                "gps_point",
                "gps_address",
                "meetup_date",
                "meetup_place_title",
                "meetup_place_address",
                "member_number",
                "member_avg_age",
            ]
        )
        serializer = self.get_serializer(group)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=no_body)
    def purchase_photo(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = GroupV2.objects.all().filter(is_active=True)
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        # if one of case exists, prohibit
        gps = GroupProfilePhotoPurchased.objects.filter(
            seller=group, buyer=request.user
        )
        if gps.exists():
            raise GroupProfilePhotoAlreadyPurchasedException()

        # deduct point
        user = request.user
        if user.point_balance < group.photo_point:
            raise UserPointBalanceNotEnoughException()

        user.point_balance = user.point_balance - group.photo_point
        user.save(update_fields=["point_balance"])
        GroupProfilePhotoPurchased.objects.create(seller=group, buyer=request.user)

        # Record ConsumptionHistory
        UserPointConsumptionHistory.objects.create(
            user=user,
            consumed_point=group.photo_point,
            consumed_reason=UserPointConsumptionHistory.ConsumedReasonChoice.OPENED_PROFILE_PHOTO,
        )

        serializer = self.get_serializer(
            instance=group, context={"force_original_image": True}
        )
        purchase_info = {"profile_photo_purchased": True}
        return Response(
            data={**serializer.data, **purchase_info}, status=status.HTTP_200_OK
        )


class GroupsTopAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = GroupsTopAddressSerializer

    @method_decorator(cache_page(60 * 5))  # cache every 5min
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = Recent24HrTopGroupAddress.objects.first()
        serializer = self.get_serializer(queryset)
        data = serializer.data
        # re-order
        data["result"] = {
            k: v
            for k, v in sorted(data["result"].items(), key=lambda x: x[1], reverse=True)
        }
        return Response(data=data, status=status.HTTP_200_OK)


class GroupV2MatchRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = GroupV2.objects.all().filter(is_active=True)
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        # If I do not have group
        qs = GroupMember.objects.filter(user=request.user, is_active=True)
        if not qs.exists():
            raise UserNotJoinedGroupException()
        gm = qs.first()
        my_group = gm.group

        # If not my match-request
        qs = MatchRequest.active_objects.filter(
            Q(sender_group=my_group, receiver_group=group)
            | Q(sender_group=group, receiver_group=my_group)
        )
        if not qs.exists():
            raise MatchRequestNotMatchedException()

        mr = qs.first()
        data = {
            "id": group.id,
            "status": mr.status,
            "type": "SENT" if mr.sender_group == my_group else "RECEIVED",
        }

        return Response(data=data, status=status.HTTP_200_OK)


class GroupReportViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        # IsUserActive,
    ]
    serializer_class = ReportGroupSerializer

    @swagger_auto_schema(request_body=ReportGroupRequestBodySerializer)
    def report(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        qs = GroupMember.objects.filter(
            user=request.user, group_id=kwargs["group_id"], is_active=True
        )
        if qs.exists():
            raise ReportMyGroupException()

        queryset = GroupV2.objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        reported_reason = request.data.get("reported_reason", "")

        rg = ReportedGroupV2.objects.create(
            reported_group=group,
            reported_reason=reported_reason,
            reported_by=user,
        )
        serializer = self.get_serializer(rg)

        # Deactivate MatchRequest sent or received by reported group
        my_group_ids = GroupMember.objects.filter(
            user=request.user, is_active=True
        ).values_list("group_id", flat=True)
        mr_qs = MatchRequest.active_objects.select_related().filter(
            (Q(sender_group_id=group.id) & Q(receiver_group_id__in=list(my_group_ids)))
            | (
                Q(sender_group_id__in=list(my_group_ids))
                & Q(receiver_group_id=group.id)
            )
        )
        mr_qs.update(is_active=False)

        # Soft-delete chat channel of me + reported group
        my_scs_cids = set(
            StreamChannel.objects.filter(
                group_member__user_id=str(user.id)
            ).values_list("cid", flat=True)
        )
        other_scs_cids = set(
            StreamChannel.objects.filter(
                group_member__group_id=str(group.id)
            ).values_list("cid", flat=True)
        )
        to_delete_cids = my_scs_cids & other_scs_cids
        sc = StreamChannel.objects.filter(cid__in=list(to_delete_cids))
        sc.update(is_active=False)
        if len(list(to_delete_cids)) > 0:
            stream.delete_channels(cids=list(to_delete_cids))

        # Notify via slack
        slack_webhook = settings.SLACK_REPORT_GROUP_BOT
        slack_webhook.send(
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🚨*그룹 신고가 들어왔어요!*🚨"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Django Admin에서 확인 후 조치를 취해주세요!",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• *Environment*: {str(settings.DJANGO_ENV).upper()} \n "
                        f"• *신고한 유저 정보* \n "
                        f"    - id: {str(request.user.id)} \n "
                        f"    - 휴대폰번호: {str(request.user.phone_number)} \n "
                        f"• *신고된 그룹 정보*  \n"
                        f"    - id: {str(group.id)} \n"
                        f"    - 제목: {str(group.title)} \n"
                        f"    - 소개: {str(group.introduction)} \n",
                    },
                },
            ]
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)


##################
# Deprecated - V1
##################


class V1GroupsGenericViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating Groups
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
    ]
    parser_classes = [MultiPartParser]
    serializer_class = RestrictedGroupProfileByHotplaceSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # Should exclude groups that I reported
        rg_qs = ReportedGroupV2.objects.filter(reported_by=request.user)
        exclude_group_ids = [rg.reported_group.id for rg in rg_qs]

        # Should exclude groups that reported me
        if request.user.joined_group:
            rg_qs = ReportedGroupV2.objects.filter(
                reported_group=request.user.joined_group
            )
            for rg in rg_qs:
                joined_group = rg.reported_by.joined_group
                if joined_group:
                    exclude_group_ids.append(joined_group.id)

        group_qs = Group.active_objects.all().exclude(id__in=exclude_group_ids)

        # prefetch related according to hotplace
        queryset = HotPlace.active_objects.prefetch_related(
            Prefetch("groups", queryset=group_qs)
        )

        # Automatically checks if user joined group
        # if joined group, will give out original profile photo of groups in the hotplace
        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=GroupCreationRequestBodySerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
            IsUserActive,
        ]
        if self.request.method == "POST":
            permission_classes.append(IsGroupCreationAllowed)
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        context = super(V1GroupsGenericViewSet, self).get_serializer_context()
        if self.request.method == "POST":
            return context
        if (
            hasattr(self.request.user, "joined_group")
            and self.request.user.joined_group
        ):
            context.update({"hotplace_id": self.request.user.joined_group.hotplace.id})
        return context

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GroupCreationSerializer
        if (
            hasattr(self.request.user, "joined_group")
            and self.request.user.joined_group
        ):
            return FullGroupProfileByHotplaceSerializer
        return self.serializer_class

    def get_parsers(self):
        parsers = super(V1GroupsGenericViewSet, self).get_parsers()
        if self.request.method == "GET":
            parsers = [JSONParser]
        return parsers


class GroupDetailViewSet(viewsets.ModelViewSet):
    """
    ViewSet for detail view of Groups

    If user does not belong to any group, deny.
    """

    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserJoinedGroup,
    ]
    serializer_class = FullGroupProfileSerializer

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = Group.active_objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])
        if request.user.joined_group.hotplace.id != group.hotplace.id:
            raise GroupNotWithinSameHotplaceException()
        serializer = self.get_serializer(group)
        return Response(serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        queryset = Group.active_objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        if user.joined_group.id != group.id:
            raise JoinedGroupNotMineException()

        # Unlink from User
        user.joined_group = None
        user.save(update_fields=["joined_group"])

        # Deactivate Group
        group.is_active = False
        group.save(update_fields=["is_active"])

        # Deactivate MatchRequest
        MatchRequest.active_objects.filter(sender_group=group).update(is_active=False)
        MatchRequest.active_objects.filter(receiver_group=group).update(is_active=False)

        # Note: Stream chat will not be deleted. User should exit chat room explicitly from chat tab
        #  Thus, even though group is deleted, chat will still appear.
        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=GroupUpdateSerializer)
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        queryset = Group.active_objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        if user.joined_group.id != group.id:
            raise JoinedGroupNotMineException()

        gps_geoinfo = request.data.get("gps_geoinfo", group.gps_geoinfo)
        # validate gps
        try:
            gpt = GeoPt(gps_geoinfo)
        except ValidationError:
            raise UserGPSNotWithinHotplaceException()

        if not is_geopt_within_boundary(gpt, group.hotplace.zone_boundary_geoinfos):
            raise UserGPSNotWithinHotplaceException()

        group.gps_geoinfo = gps_geoinfo
        group.title = request.data.get("title", group.title)
        group.introduction = request.data.get("introduction", group.introduction)

        group.save(update_fields=["gps_geoinfo", "title", "introduction"])
        serializer = GroupUpdateSerializer(group)

        return Response(data=serializer.data, status=status.HTTP_200_OK)
