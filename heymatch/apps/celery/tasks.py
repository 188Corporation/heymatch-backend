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
            onesignal_client.send_notification_to_specific_users(
                title="프로필 사진 심사 거절",
                content="프로필 사진 심사에 통과하지 못했어요. 새로운 사진을 올려주세요 😢",
                user_ids=[str(upi.user.id)],
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
