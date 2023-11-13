from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from heymatch.apps.group.models import GroupMember
from heymatch.apps.user.models import UserOnBoarding

User = get_user_model()
stream = settings.STREAM_CLIENT
onesignal_client = settings.ONE_SIGNAL_CLIENT

logger = get_task_logger(__name__)


@shared_task(soft_time_limit=120)
def send_notification_to_group_not_made_users():
    """그룹 안 만든 사람들에게 알림 보내기"""

    # Select users that did not make any groups
    gm_user_ids = list(GroupMember.objects.all().values_list("user_id", flat=True))

    no_group_users = User.objects.exclude(id__in=gm_user_ids)
    onboarding_completed_user_ids = UserOnBoarding.objects.filter(
        user__in=no_group_users, onboarding_completed=True
    ).values_list("user_id", flat=True)

    # 10분, 1시간, 하루동안 생성된 유저들 중에 알림 안보낸 유저에게 보내기
    ten_min_ago = timezone.now() - timezone.timedelta(minutes=10)
    one_hr_ago = timezone.now() - timezone.timedelta(hours=1)
    one_day_ago = timezone.now() - timezone.timedelta(days=1)
    users = User.objects.filter(id__in=onboarding_completed_user_ids)
    users_within_ten_min_not_notified = users.filter(
        date_joined__gte=ten_min_ago,
        notified_to_make_first_group_after_join_10min=False,
    )
    users_within_one_hour_not_notified = users.filter(
        date_joined__gte=one_hr_ago,
        date_joined__lte=ten_min_ago,
        notified_to_make_first_group_after_join_1hr=False,
    )
    users_within_one_day_not_notified = users.filter(
        date_joined__gte=one_day_ago,
        date_joined__lte=one_hr_ago,
        notified_to_make_first_group_after_join_1day=False,
    )

    # Send notification
    if users_within_ten_min_not_notified.exists():
        onesignal_client.send_notification_to_specific_users(
            title="첫 그룹을 만들어 보세요!",
            content="방금 가입하셨네요! 첫 그룹을 만들고 미팅팸 구해봐요! 🥳",
            user_ids=[str(user.id) for user in users_within_ten_min_not_notified],
            data={
                "route_to": "MainTabs",
            },
        )
        users_within_ten_min_not_notified.update(
            notified_to_make_first_group_after_join_10min=True
        )

    if users_within_one_hour_not_notified.exists():
        onesignal_client.send_notification_to_specific_users(
            title="첫 그룹을 만들어 보세요!",
            content="아직 늦지 않았어요! 첫 그룹을 만들고 매칭해봐요! 😍",
            user_ids=[str(user.id) for user in users_within_one_hour_not_notified],
            data={
                "route_to": "MainTabs",
            },
        )
        users_within_one_hour_not_notified.update(
            notified_to_make_first_group_after_join_1hr=True
        )

    if users_within_one_day_not_notified.exists():
        onesignal_client.send_notification_to_specific_users(
            title="첫 그룹을 만들어 보세요!",
            content="벌써 많은 그룹이 만들어졌어요! 오늘이 가기 전에 첫 그룹을 만들고 매칭해봐요! 👀",
            user_ids=[str(user.id) for user in users_within_one_day_not_notified],
            data={
                "route_to": "MainTabs",
            },
        )
        users_within_one_day_not_notified.update(
            notified_to_make_first_group_after_join_1day=True
        )
