import datetime
import logging
from collections import Counter

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from heymatch.apps.group.models import Group, GroupV2, Recent24HrTopGroupAddress
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.user.models import DeleteScheduledUser, UserProfileImage
from heymatch.utils.util import detect_face_with_haar_cascade_ml

User = get_user_model()
stream = settings.STREAM_CLIENT
onesignal_client = settings.ONE_SIGNAL_CLIENT

logger = logging.getLogger(__name__)


@shared_task(soft_time_limit=60)
def verify_main_profile_images():
    logger.debug("==================================================")
    logger.debug("=== 'verify_main_profile_images' task started! ===")
    logger.debug("==================================================")

    logger.debug("[1] Get target profile images to be verified")
    target_upi_qs = UserProfileImage.active_objects.filter(
        Q(is_main=True) & Q(status=UserProfileImage.StatusChoices.NOT_VERIFIED)
    )
    logger.debug(f"[1] Target images to be verified: {target_upi_qs}")

    # Create the haar cascade
    for upi in target_upi_qs:  # type: UserProfileImage
        faces_num = detect_face_with_haar_cascade_ml(upi.image.url)
        if faces_num == 1:
            upi.status = UserProfileImage.StatusChoices.ACCEPTED
            upi.user.is_first_signup = False
            upi.user.save(update_fields=["is_first_signup"])
            logger.debug(f"UserProfile(id={upi.id}) ACCEPTED!")

            # Send notification
            onesignal_client.send_notification_to_specific_users(
                title="프로필 사진 통과!",
                content="메인 프로필 사진 심사 통과 하셨습니다! 이제 헤이매치를 이용해봐요 😀",
                user_ids=[str(upi.user.id)],
            )
        else:
            upi.status = UserProfileImage.StatusChoices.REJECTED
            logger.debug(
                f"UserProfile(id={upi.id}) REJECTED! (faces num = {faces_num})"
            )
            onesignal_client.send_notification_to_specific_users(
                title="프로필 사진 심사 거절",
                content="새로운 메인 프로필 사진을 올려주세요",
                user_ids=[str(upi.user.id)],
            )
        upi.save(update_fields=["status", "is_active"])


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
    date_from = timezone.now() - datetime.timedelta(days=1)
    last_24_group_addresses = list(
        GroupV2.objects.filter(created_at__gte=date_from).values_list(
            "gps_address", flat=True
        )
    )
    if len(last_24_group_addresses) > 0:
        top_10_counter = dict(Counter(last_24_group_addresses).most_common(10))
        Recent24HrTopGroupAddress.objects.create(result=top_10_counter)


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
        # joined_group = user.joined_group
        # if joined_group:
        #     joined_group.is_active = False
        #     joined_group.save(update_fields=["is_active"])

        # Deactivate MatchRequest
        logger.debug("[2.2] Deactivate all MatchRequests")
        # MatchRequest.active_objects.filter(sender_group=joined_group).update(
        #     is_active=False
        # )
        # MatchRequest.active_objects.filter(receiver_group=joined_group).update(
        #     is_active=False
        # )

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
