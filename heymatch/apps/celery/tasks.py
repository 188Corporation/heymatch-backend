import datetime
from collections import Counter

from celery import shared_task
from celery.utils.log import get_task_logger
from celery_singleton import Singleton
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from config.celery_app import app
from heymatch.apps.group.models import (
    Group,
    GroupMember,
    GroupProfilePhotoPurchased,
    GroupV2,
    Recent24HrTopGroupAddress,
)
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.payment.models import UserPurchase
from heymatch.apps.user.models import (
    DeleteScheduledUser,
    UserOnBoarding,
    UserProfileImage,
)
from heymatch.utils.util import detect_faces_with_aws_rekognition

User = get_user_model()
stream = settings.STREAM_CLIENT
onesignal_client = settings.ONE_SIGNAL_CLIENT

logger = get_task_logger(__name__)

# ================================================
# == System-wide Tasks
# ================================================


@app.task(base=Singleton, lock_expiry=60 * 30)
def verify_main_profile_images():
    logger.debug("==================================================")
    logger.debug("=== 'verify_main_profile_images' task started! ===")
    logger.debug("==================================================")

    logger.debug("[1] Get target profile images to be verified")
    target_upi_qs = UserProfileImage.all_objects.filter(
        Q(is_main=True)
        & Q(status=UserProfileImage.StatusChoices.NOT_VERIFIED)
        & Q(is_active=False)
        & Q(expected_verification_datetime__lt=timezone.now())
    )
    logger.debug(f"[1] Target images to be verified: {target_upi_qs}")

    for upi in target_upi_qs:  # type: UserProfileImage
        result, reason = detect_faces_with_aws_rekognition(upi.image.url)
        result = True
        if result is True:
            # delete previous
            previous = UserProfileImage.all_objects.filter(
                Q(user=upi.user)
                & Q(is_main=True)
                & Q(status=UserProfileImage.StatusChoices.ACCEPTED)
                & Q(is_active=True)
            )
            previous.delete()

            # set accepted as active
            upi.status = UserProfileImage.StatusChoices.ACCEPTED
            upi.is_active = True
            upi.save(update_fields=["status", "is_active"])

            # set user flag
            uob = UserOnBoarding.objects.get(user=upi.user)
            uob.onboarding_completed = True
            uob.profile_photo_under_verification = False
            uob.profile_photo_rejected = False
            uob.profile_photo_rejected_reason = None
            uob.save(
                update_fields=[
                    "onboarding_completed",
                    "profile_photo_under_verification",
                    "profile_photo_rejected",
                    "profile_photo_rejected_reason",
                ]
            )

            logger.debug(f"UserProfile(id={upi.id}) ACCEPTED!")

            # Send notification
            onesignal_client.send_notification_to_specific_users(
                title="프로필 사진 통과!",
                content="메인 프로필 사진 심사 통과 하셨습니다! 이제 헤이매치를 이용해봐요 😀",
                user_ids=[str(upi.user.id)],
                data={
                    "route_to": "MainTabs",
                },
            )
        else:
            # set user flag
            uob = UserOnBoarding.objects.get(user=upi.user)
            uob.profile_photo_under_verification = False
            uob.profile_photo_rejected = True
            uob.profile_photo_rejected_reason = reason

            uob.save(
                update_fields=[
                    "profile_photo_under_verification",
                    "profile_photo_rejected",
                    "profile_photo_rejected_reason",
                ]
            )
            logger.debug(f"UserProfile(id={upi.id}) REJECTED!")

            route_to = "MainTabs"
            if not uob.onboarding_completed:
                route_to = "ProfilePhotoRejectedScreen"
            onesignal_client.send_notification_to_specific_users(
                title="프로필 사진 심사 거절",
                content="프로필 사진 심사에 통과하지 못했어요. 새로운 사진을 올려주세요 😢",
                user_ids=[str(upi.user.id)],
                data={
                    "route_to": route_to,
                },
            )
            upi.delete()


@shared_task(soft_time_limit=120)
def aggregate_recent_24hr_top_ranked_group_address():
    """
    Aggregate Top Ranked Group addresses within recent 24 hours for recommendation feature
    """
    logger.debug(
        "======================================================================="
    )
    logger.debug(
        "=== 'aggregate_recent_24hr_top_ranked_group_address' task started! ==="
    )
    logger.debug(
        "======================================================================="
    )
    # date_from = timezone.now() - datetime.timedelta(days=1)
    last_24_group_addresses = list(
        GroupV2.objects.filter(is_active=True).values_list("gps_address", flat=True)
    )
    if len(last_24_group_addresses) > 0:
        top_10_counter = dict(Counter(last_24_group_addresses).most_common(10))
        Recent24HrTopGroupAddress.objects.create(result=top_10_counter)


@shared_task(soft_time_limit=120)
def fill_up_available_ads_point_for_all_users():
    """
    Fill up avail. num of ads point for all users for every day
    """
    logger.debug(
        "======================================================================="
    )
    logger.debug("=== 'fill_up_available_ads_point_for_all_users' task started! ===")
    logger.debug(
        "======================================================================="
    )
    users = User.active_objects.all()
    users.update(num_of_available_ads=3)


@shared_task(soft_time_limit=120)
def aggregate_business_report():
    slack_webhook = settings.SLACK_BUSINESS_REPORT_BOT

    last_24hrs = timezone.now() - datetime.timedelta(days=1)

    # User related
    users_all = User.objects.all()
    male_users_all = users_all.filter(gender=User.GenderChoices.MALE)
    female_users_all = users_all.filter(gender=User.GenderChoices.FEMALE)
    users_today = users_all.filter(created_at__gte=last_24hrs)
    male_users_today = users_today.filter(gender=User.GenderChoices.MALE)
    female_users_today = users_today.filter(gender=User.GenderChoices.FEMALE)

    # Group
    groups_all = GroupV2.objects.all().prefetch_related(
        "group_member_group",
        "group_member_group__user",
    )
    male_groups_all = groups_all.filter(
        group_member_group__user__gender=User.GenderChoices.MALE
    )
    female_groups_all = groups_all.filter(
        group_member_group__user__gender=User.GenderChoices.FEMALE
    )
    groups_today = groups_all.filter(created_at__gte=last_24hrs)
    male_groups_today = male_groups_all.filter(created_at__gte=last_24hrs)
    female_groups_today = female_groups_all.filter(created_at__gte=last_24hrs)

    # Photo purchased related
    photo_purchased_all = GroupProfilePhotoPurchased.objects.all()
    photo_purchased_by_male_all = photo_purchased_all.filter(
        buyer__gender=User.GenderChoices.MALE
    )
    photo_purchased_by_female_all = photo_purchased_all.filter(
        buyer__gender=User.GenderChoices.FEMALE
    )
    photo_purchased_today = photo_purchased_all.filter(created_at__gte=last_24hrs)
    photo_purchased_by_male_today = photo_purchased_today.filter(
        buyer__gender=User.GenderChoices.MALE
    )
    photo_purchased_by_female_today = photo_purchased_today.filter(
        buyer__gender=User.GenderChoices.FEMALE
    )

    # MatchRequest
    match_request_all = MatchRequest.objects.all()
    match_request_all_by_male = match_request_all.filter(
        sender_group__in=male_groups_all
    )
    match_request_all_by_female = match_request_all.filter(
        sender_group__in=female_groups_all
    )
    match_request_today = match_request_all.filter(created_at__gte=last_24hrs)
    match_request_today_by_male = match_request_today.filter(
        sender_group__in=male_groups_all
    )
    match_request_today_by_female = match_request_today.filter(
        sender_group__in=female_groups_all
    )

    # Candy
    candy_spent_all = (
        photo_purchased_all.count() * settings.POINT_NEEDED_FOR_PHOTO
        + match_request_all.count() * settings.POINT_NEEDED_FOR_MATCH
    )
    candy_spent_by_male_all = (
        photo_purchased_by_male_all.count() * settings.POINT_NEEDED_FOR_PHOTO
        + match_request_all_by_male.count() * settings.POINT_NEEDED_FOR_MATCH
    )
    candy_spent_by_female_all = (
        photo_purchased_by_female_all.count() * settings.POINT_NEEDED_FOR_PHOTO
        + match_request_all_by_female.count() * settings.POINT_NEEDED_FOR_MATCH
    )
    candy_spent_today = (
        photo_purchased_today.count() * settings.POINT_NEEDED_FOR_PHOTO
        + match_request_today.count() * settings.POINT_NEEDED_FOR_MATCH
    )
    candy_spent_by_male_today = (
        photo_purchased_by_male_today.count() * settings.POINT_NEEDED_FOR_PHOTO
        + match_request_today_by_male.count() * settings.POINT_NEEDED_FOR_MATCH
    )
    candy_spent_by_female_today = (
        photo_purchased_by_female_today.count() * settings.POINT_NEEDED_FOR_PHOTO
        + match_request_today_by_female.count() * settings.POINT_NEEDED_FOR_MATCH
    )

    # Payment
    payment_all = UserPurchase.objects.all().filter(purchase_processed=True)
    krw_all = sum_up_payments(payment_all)

    payment_all_by_male = payment_all.filter(user__gender=User.GenderChoices.MALE)
    male_krw_all = sum_up_payments(payment_all_by_male)
    payment_all_by_female = payment_all.filter(user__gender=User.GenderChoices.FEMALE)
    female_krw_all = sum_up_payments(payment_all_by_female)
    payment_today = payment_all.filter(purchased_at=last_24hrs)
    krw_today = sum_up_payments(payment_today)
    payment_today_by_male = payment_today.filter(user__gender=User.GenderChoices.MALE)
    male_krw_today = sum_up_payments(payment_today_by_male)
    payment_today_by_female = payment_today.filter(
        user__gender=User.GenderChoices.FEMALE
    )
    female_krw_today = sum_up_payments(payment_today_by_female)

    # Top Hotplaces
    top_hotplaces = Recent24HrTopGroupAddress.objects.filter(
        aggregated_at__gte=last_24hrs
    ).first()

    slack_webhook.send(
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "안녕하세요! 👋 \n 오늘의 헤이매치 사용 현황 리포트 드립니다!",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*👶 신규 유저수*: \n "
                    f"  - 오늘: {users_today.count()}명 "
                    f"(남성-{male_users_today.count()}명 / 여성-{female_users_today.count()}명) \n "
                    f"  - 전체: {users_all.count()}명 "
                    f"(남성-{male_users_all.count()}명 / 여성-{female_users_all.count()}명) \n ",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*👯‍그룹 생성 개수*: \n "
                    f"  - 오늘: {groups_today.count()}개 "
                    f"(남성-{male_groups_today.count()}개 / 여성-{female_groups_today.count()}개) \n "
                    f"  - 전체: {groups_all.count()}개 "
                    f"(남성-{male_groups_all.count()}개 / 여성-{female_groups_all.count()}개) \n ",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📸 사진 열람 개수*: \n "
                    f"  - 오늘: {photo_purchased_today.count()}개 "
                    f"(남성-{photo_purchased_by_male_today.count()}개 "
                    f"/ 여성-{photo_purchased_by_female_today.count()}개) \n "
                    f"  - 전체: {photo_purchased_all.count()}개 "
                    f"(남성-{photo_purchased_by_male_all.count()}개 "
                    f"/ 여성-{photo_purchased_by_female_all.count()}개) \n ",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📬 매칭 요청 개수*: \n "
                    f"  - 오늘: {match_request_today.count()}개 "
                    f"(남성-{match_request_today_by_male.count()}개 "
                    f"/ 여성-{match_request_today_by_female.count()}개) \n "
                    f"  - 전체: {match_request_all.count()}개 "
                    f"(남성-{match_request_all_by_male.count()}개 "
                    f"/ 여성-{match_request_all_by_female.count()}개) \n ",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🍬 사용 캔디 개수*: \n "
                    f"  - 오늘: {candy_spent_today}개 "
                    f"(남성-{candy_spent_by_male_today}개 "
                    f"/ 여성-{candy_spent_by_female_today}개) \n "
                    f"  - 전체: {candy_spent_all}개 "
                    f"(남성-{candy_spent_by_male_all}개 "
                    f"/ 여성-{candy_spent_by_female_all}개) \n ",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💰 결제 대금*: \n "
                    f"  - 오늘: {krw_today}원 (남성-{male_krw_today}원 / 여성-{female_krw_today}원) \n "
                    f"  - 전체: {krw_all}원 (남성-{male_krw_all}원 / 여성-{female_krw_all}원) \n ",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔥 Top 핫플레이스*: \n "
                    f"  - {top_hotplaces.result if top_hotplaces else '수집중..'}",
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": "👀 오늘도 수고하셨습니다 :)"}],
            },
        ]
    )


def sum_up_payments(payments):
    krw = 0
    for payment in payments:
        krw += payment.point_item.price_in_krw
    return krw


@shared_task(soft_time_limit=60)
def delete_scheduled_users():
    logger.debug("======================================")
    logger.debug("=== 'Delete Scheduled User' task started! ===")
    logger.debug("======================================")

    logger.debug("[1] Get users that are scheduled for deletion")
    ds_users = DeleteScheduledUser.objects.filter(
        Q(status=DeleteScheduledUser.DeleteStatusChoices.WAITING)
        & Q(delete_schedule_at__lt=timezone.now())
    )
    logger.debug(f"[1] Target users to be deleted: {ds_users}")

    # process deletion for each user
    for dsu in ds_users:
        user = dsu.user
        logger.debug(f"=== Target user: {user.id} ===")
        logger.debug("[2.1] Deactivate joined_group if any")

        # Disable group
        gms = GroupMember.objects.filter(user=user)
        group_ids = gms.values_list("group_id", flat=True)
        groups = GroupV2.objects.filter(id__in=list(group_ids))
        # TODO: If more users are joined in one group (e.g friend invitation..), should not disable group,
        #  but instead promot other user to be group leader, and remove schedule-deleted user.
        gms.update(is_active=False)
        groups.update(is_active=False)

        # Deactivate MatchRequest
        logger.debug("[2.2] Deactivate all MatchRequests")
        MatchRequest.active_objects.filter(sender_group_id__in=list(group_ids)).update(
            is_active=False
        )
        MatchRequest.active_objects.filter(
            receiver_group_id__in=list(group_ids)
        ).update(is_active=False)

        # Soft-delete Stream Chat
        logger.debug("[2.3] Deactivate all Stream Chats")
        channels = stream.query_channels(
            filter_conditions={
                "members": {"$in": [str(user.id)]},
            }
        )
        cids = [ch["channel"]["cid"] for ch in channels["channels"]]
        if len(cids) > 0:
            stream.delete_channels(cids=cids)

        # Mark user as deleted
        logger.debug("[2.4] Mark user as `deleted`")
        # user.joined_group = None
        user.is_deleted = True
        user.save(update_fields=["is_deleted"])

        # Mark DeleteScheduledUser as processed
        logger.debug("[2.5] Mark DeleteScheduledUser as `completed`")
        dsu.status = DeleteScheduledUser.DeleteStatusChoices.COMPLETED
        dsu.save(update_fields=["status"])


# ================================================
# == Notification Tasks
# ================================================


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
        created_at__lte=ten_min_ago,
        created_at__gt=one_hr_ago,
        notified_to_make_first_group_after_join_10min=False,
    )
    users_within_one_hour_not_notified = users.filter(
        created_at__lte=one_hr_ago,
        created_at__gt=one_day_ago,
        notified_to_make_first_group_after_join_1hr=False,
    )
    users_within_one_day_not_notified = users.filter(
        created_at__lte=one_day_ago,
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


@shared_task(soft_time_limit=120)
def send_notification_to_group_with_past_meetup_date():
    """그룹 만남날짜가 지난 사람에게 알림보내기"""

    # 1일, 3일, 1주일, 2주일 지난 그룹 필터링
    one_day_ago = timezone.now() - timezone.timedelta(days=1)
    three_day_ago = timezone.now() - timezone.timedelta(days=3)
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    two_weeks_ago = timezone.now() - timezone.timedelta(days=14)

    # 만남날짜가 지난 그룹을 선택한다
    one_day_groups = GroupV2.objects.filter(
        is_active=True,
        meetup_date__lte=one_day_ago,
        meetup_date__gt=three_day_ago,
        notified_to_update_meetup_date_after_one_day=False,
    )
    three_day_groups = GroupV2.objects.filter(
        is_active=True,
        meetup_date__lte=three_day_ago,
        meetup_date__gt=one_week_ago,
        notified_to_update_meetup_date_after_three_day=False,
    )
    one_week_groups = GroupV2.objects.filter(
        is_active=True,
        meetup_date__lte=one_week_ago,
        meetup_date__gt=two_weeks_ago,
        notified_to_update_meetup_date_after_one_week=False,
    )
    two_weeks_groups = GroupV2.objects.filter(
        is_active=True,
        meetup_date__lte=two_weeks_ago,
        notified_to_update_meetup_date_after_two_week=False,
    )

    # 알림1
    users_one_day = GroupMember.objects.filter(group__in=one_day_groups).values_list(
        "user_id", flat=True
    )
    if users_one_day:
        onesignal_client.send_notification_to_specific_users(
            title="만든 그룹의 만남날짜가 지났어요!",
            content="만든 그룹의 만남날짜가 [하루] 지났어요!😵 날짜가 지나면 매칭률이 떨어지니 업데이트 해봐요!🙈",
            user_ids=[str(user_id) for user_id in users_one_day],
            data={
                "route_to": "MainTabs",
            },
        )
        one_day_groups.update(notified_to_update_meetup_date_after_one_day=True)
    # 알림2
    users_three_day = GroupMember.objects.filter(
        group__in=three_day_groups
    ).values_list("user_id", flat=True)
    if users_three_day:
        onesignal_client.send_notification_to_specific_users(
            title="만든 그룹의 만남날짜가 지났어요!",
            content="만든 그룹의 만남날짜가 [3일] 지났어요!😯 아직 미팅팸 못 구했다면? 지금 당장 만남날짜 업데이트하자!😍",
            user_ids=[str(user_id) for user_id in users_three_day],
            data={
                "route_to": "MainTabs",
            },
        )
        three_day_groups.update(notified_to_update_meetup_date_after_three_day=True)
    # 알림3
    users_one_week = GroupMember.objects.filter(group__in=one_week_groups).values_list(
        "user_id", flat=True
    )
    if users_one_week:
        onesignal_client.send_notification_to_specific_users(
            title="만든 그룹의 만남날짜가 지났어요!",
            content="만든 그룹의 만남날짜가 무려 [일주일]이나 지났어요..😰 날짜 업데이트하고 매칭 많이 받아봐요!🫡",
            user_ids=[str(user_id) for user_id in users_one_week],
            data={
                "route_to": "MainTabs",
            },
        )
        one_week_groups.update(notified_to_update_meetup_date_after_one_week=True)
    # 알림4
    users_two_week = GroupMember.objects.filter(group__in=two_weeks_groups).values_list(
        "user_id", flat=True
    )
    if users_two_week:
        onesignal_client.send_notification_to_specific_users(
            title="만든 그룹의 만남날짜가 지났어요!",
            content="만드신 그룹의 만남날짜가 많이 지났어요🤧 날짜 업데이트하고 매칭 많이 받아봐요!🫡",
            user_ids=[str(user_id) for user_id in users_two_week],
            data={
                "route_to": "MainTabs",
            },
        )
        two_weeks_groups.update(notified_to_update_meetup_date_after_two_week=True)


@shared_task(soft_time_limit=120)
def send_notification_to_group_to_send_match_request():
    """그룹 만들고 매칭 안보낸 사람들에게 알림 보내기"""

    half_hour_ago = timezone.now() - timezone.timedelta(minutes=30)
    one_day_ago = timezone.now() - timezone.timedelta(days=1)
    three_day_ago = timezone.now() - timezone.timedelta(days=3)

    half_hour_group_ids = list(
        GroupV2.objects.filter(
            is_active=True,
            created_at__lte=half_hour_ago,
            created_at__gt=one_day_ago,
            notified_to_send_mr_after_half_hour=False,
        ).values_list("id", flat=True)
    )
    one_day_group_ids = list(
        GroupV2.objects.filter(
            is_active=True,
            created_at__lte=one_day_ago,
            created_at__gt=three_day_ago,
            notified_to_send_mr_after_one_day=False,
        ).values_list("id", flat=True)
    )
    three_day_group_ids = list(
        GroupV2.objects.filter(
            is_active=True,
            created_at__lte=three_day_ago,
            notified_to_send_mr_after_three_day=False,
        ).values_list("id", flat=True)
    )
    half_hour_mr_sent_group_ids = MatchRequest.objects.filter(
        sender_group__in=half_hour_group_ids
    ).values_list("sender_group_id")
    one_hour_mr_sent_group_ids = MatchRequest.objects.filter(
        sender_group__in=one_day_group_ids
    ).values_list("sender_group_id")
    three_hour_mr_sent_group_ids = MatchRequest.objects.filter(
        sender_group__in=three_day_group_ids
    ).values_list("sender_group_id")

    target_half_hour_group_ids = []
    for gid in half_hour_group_ids:
        if gid not in half_hour_mr_sent_group_ids:
            target_half_hour_group_ids.append(gid)

    target_one_day_group_ids = []
    for gid in one_day_group_ids:
        if gid not in one_hour_mr_sent_group_ids:
            target_one_day_group_ids.append(gid)

    target_three_day_group_ids = []
    for gid in three_day_group_ids:
        if gid not in three_hour_mr_sent_group_ids:
            target_three_day_group_ids.append(gid)

    # Send notification
    if target_half_hour_group_ids:
        noti_user_ids = GroupMember.objects.filter(
            group_id__in=target_half_hour_group_ids
        ).values_list("user_id", flat=True)
        onesignal_client.send_notification_to_specific_users(
            title="첫 매칭을 걸어보세요!",
            content="방금 그룹을 만드셨네요! 마음에 드는 미팅팸을 보고 매칭을 보내봐요! 🥳",
            user_ids=[str(user_id) for user_id in list(noti_user_ids)],
            data={
                "route_to": "MainTabs",
            },
        )
        GroupV2.objects.filter(id___in=target_half_hour_group_ids).update(
            notified_to_send_mr_after_half_hour=True
        )

    if target_one_day_group_ids:
        noti_user_ids = GroupMember.objects.filter(
            group_id__in=target_one_day_group_ids
        ).values_list("user_id", flat=True)
        onesignal_client.send_notification_to_specific_users(
            title="첫 매칭을 걸어보세요!",
            content="어제 그룹을 만드셨네요! 그동안 미팅팸이 더 많이 생겼어요! 어서 매칭을 보내봐요! 💚",
            user_ids=[str(user_id) for user_id in list(noti_user_ids)],
            data={
                "route_to": "MainTabs",
            },
        )
        GroupV2.objects.filter(id___in=target_one_day_group_ids).update(
            notified_to_send_mr_after_one_day=True
        )

    if target_three_day_group_ids:
        noti_user_ids = GroupMember.objects.filter(
            group_id__in=target_three_day_group_ids
        ).values_list("user_id", flat=True)
        onesignal_client.send_notification_to_specific_users(
            title="첫 그룹을 만들어 보세요!",
            content="엊그제 그룹을 만드셨네요! 그동안 미팅팸이 더 많이 생겼어요! 어서 매칭을 보내봐요! 💗💗",
            user_ids=[str(user_id) for user_id in list(noti_user_ids)],
            data={
                "route_to": "MainTabs",
            },
        )
        GroupV2.objects.filter(id___in=target_three_day_group_ids).update(
            notified_to_send_mr_after_three_day=True
        )


# ================================================
# == LEGACY (We do not use below tasks anymore)
# ================================================
@shared_task(soft_time_limit=60)
def end_of_the_day_task():
    """
    HeyMatch is meant to be used for just One-day.
    All groups created, matches made, chats sent are soft deleted (inactive).
    """
    # Unregister all users from group
    logger.debug("======================================")
    logger.debug("=== 'End of the Day' task started! ===")
    logger.debug("======================================")

    logger.debug("[1] Unregister all users from group")
    users = User.objects.exclude(joined_group__isnull=True)
    logger.debug(f"[1] Users count: {len(users)}")
    users.update(joined_group=None)

    # Make Groups inactive
    logger.debug("[2] Make Groups inactive")
    groups = Group.active_objects.all()
    logger.debug(f"[2] Groups count: {len(groups)}")
    groups.update(is_active=False)
    # TODO: for a moment, just randomly pick and make them inactive
    group_ids = Group.objects.order_by("?")[:15]
    Group.objects.filter(id__in=group_ids).update(is_active=True)

    # Make MatchRequest inactive
    logger.debug("[3] Make MatchRequest inactive")
    mrs = MatchRequest.active_objects.all()
    logger.debug(f"[3] MatchRequest count: {len(mrs)}")
    mrs.update(is_active=False)

    # Stream Chat will not be deleted. User should be able to chat with already matched user
    #  until they explicitly exit chat room
    logger.debug("============== Success! ==============")
