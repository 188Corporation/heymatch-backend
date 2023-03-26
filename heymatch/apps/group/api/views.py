from typing import Any

from django.conf import settings
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
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import (
    CharFilter,
    DateFromToRangeFilter,
    DjangoFilterBackend,
    FilterSet,
    RangeFilter,
)
from django_google_maps.fields import GeoPt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_gis.filters import DistanceToPointFilter

from heymatch.apps.chat.models import StreamChannel
from heymatch.apps.group.models import Group, GroupMember, GroupV2, ReportedGroup
from heymatch.apps.hotplace.models import HotPlace
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.user.models import User
from heymatch.shared.exceptions import (
    GroupNotWithinSameHotplaceException,
    JoinedGroupNotMineException,
    ReportMyGroupException,
    UserGPSNotWithinHotplaceException,
)
from heymatch.shared.permissions import (
    IsGroupCreationAllowed,
    IsUserActive,
    IsUserJoinedGroup,
)
from heymatch.utils.util import is_geopt_within_boundary

from .serializers import (
    FullGroupProfileByHotplaceSerializer,
    FullGroupProfileSerializer,
    GroupCreationRequestBodySerializer,
    GroupCreationSerializer,
    GroupUpdateSerializer,
    ReportGroupRequestBodySerializer,
    ReportGroupSerializer,
    RestrictedGroupProfileByHotplaceSerializer,
    V2GroupCreationRequestBodySerializer,
    V2GroupFilteredListSerializer,
)

# User = get_user_model()
stream = settings.STREAM_CLIENT


class GroupV2Filter(FilterSet):
    meetup_date = DateFromToRangeFilter(field_name="meetup_date")
    height = RangeFilter(method="filter_avg_heights_in_group")
    gender = CharFilter(method="filter_gender_type_in_group")

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
        group_subquery = Subquery(
            GroupV2.objects.filter(id=OuterRef("group_id")).values("id")[:1]
        )
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
            .annotate(group_anno_id=Coalesce(group_subquery, 0))
            .annotate(avg_height=Coalesce(avg_height_subquery, 0))
            .filter(avg_height__gte=value.start, avg_height__lte=value.stop)
            .distinct("group_id")
        )
        # Get final GroupV2 QS
        queryset = queryset.filter(
            id__in=list(gm_queryset.values_list("group_id", flat=True))
        )
        return queryset

    def filter_gender_type_in_group(self, queryset, field_name, value):
        if value not in ["m", "f"]:
            return queryset

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
                        When(Q(gender=value), then=1),
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


class GroupsGenericViewSet(viewsets.ModelViewSet):
    queryset = GroupV2.objects.all()
    permission_classes = [
        # IsAuthenticated,
        # IsUserActive,
    ]
    parser_classes = [MultiPartParser]
    serializer_class = V2GroupCreationRequestBodySerializer
    distance_filter_field = "gps_point"
    filter_backends = [DjangoFilterBackend, DistanceToPointFilter]
    filterset_class = GroupV2Filter

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        1) 거리로 QS 나누고
            ?dist=5000&point=127.03952,37.52628
        2) Date로 나누고
            ?meetup_date_after=2023-01-01&meetup_date_before=2023-01-05
        3) height로 나누고
            ?height_min=130&height_max=180

        예시) 압구정역 기준 반경 5km 내 미팅날짜가 2023-01-01~2023-01-05 사이고 멤버들의 평균키가 130cm-180cm 사이인 그룹들
            GET ../api/groups/
                    ?dist=5000&point=127.03952,37.52628
                    ?meetup_date_after=2023-01-01&meetup_date_before=2023-01-05
                    ?height_min=130&height_max=180

        """
        filtered_qs = self.filter_queryset(self.get_queryset())
        print(filtered_qs)
        serializer = V2GroupFilteredListSerializer(filtered_qs, many=True)
        # print(serializer.data)

        # GET /api/groups/?gps_geoinfo=37.1234,128.1234
        #   &meetup_date_range=2023-01-01,2023-01-05
        #   &gender=f
        #   &height_cm=170,188
        #   &max_distance_km=30

        # Get search bar GPS info
        # Fetch Group, GroupMember, Member's profile
        # filter
        #  1. default 15km
        #  2. ....
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=V2GroupCreationRequestBodySerializer)
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=status.HTTP_201_CREATED)

    def perform_create(self, serializer) -> None:
        # Get members
        user_ids = serializer.validated_data.get("user_ids")
        qs = User.active_objects.all()
        users = [get_object_or_404(qs, id=user_id) for user_id in user_ids]
        # create Group
        serializer.validated_data.pop("user_ids")
        group = GroupV2.objects.create(**serializer.validated_data)
        # create GroupMember
        for user in users:
            GroupMember.objects.create(
                group=group,
                user=user,
            )
        # add myself as group leader
        GroupMember.objects.create(
            group=group, user=self.request.user, is_user_leader=True
        )


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
        rg_qs = ReportedGroup.objects.filter(reported_by=request.user)
        exclude_group_ids = [rg.reported_group.id for rg in rg_qs]

        # Should exclude groups that reported me
        if request.user.joined_group:
            rg_qs = ReportedGroup.objects.filter(
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


class GroupReportViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        IsUserActive,
        IsUserJoinedGroup,
    ]
    serializer_class = ReportGroupSerializer

    @swagger_auto_schema(request_body=ReportGroupRequestBodySerializer)
    def report(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        queryset = Group.objects.all()
        group = get_object_or_404(queryset, id=kwargs["group_id"])

        if user.joined_group.id == group.id:
            raise ReportMyGroupException()

        reported_reason = request.data.get("reported_reason", "")

        rg = ReportedGroup.objects.create(
            reported_group=group,
            reported_reason=reported_reason,
            reported_by=user,
        )
        serializer = self.get_serializer(rg)

        # Deactivate MatchRequest sent or received by reported group
        mr_qs = MatchRequest.active_objects.select_related().filter(
            (Q(sender_group_id=group.id) & Q(receiver_group_id=user.joined_group.id))
            | (Q(sender_group_id=user.joined_group.id) & Q(receiver_group_id=group.id))
        )
        mr_qs.update(is_active=False)

        # Soft-delete chat channel of me + reported group
        scs = StreamChannel.objects.filter(participants__users__contains=str(user.id))
        to_be_deleted_cids = set()
        for sc in scs:
            groups = sc.participants["groups"]
            if str(group.id) not in groups:
                continue
            # if found stream chat channel with reported group, delete
            to_be_deleted_cids.add(sc.cid)
        if to_be_deleted_cids:
            stream.delete_channels(cids=list(to_be_deleted_cids))

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
