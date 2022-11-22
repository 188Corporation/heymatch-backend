import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from heymatch.apps.group.models import Group
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.user.models import DeleteScheduledUser

User = get_user_model()
stream = settings.STREAM_CLIENT
logger = logging.getLogger(__name__)


@shared_task(soft_time_limit=60)
def end_of_the_day_task():
    """
    HeyMatch is meant to be used for just One-day.
    All groups created, matches made, chats sent are soft deleted (inactive).
    """
    # Unregister all users from group
    logger.info("======================================")
    logger.info("=== 'End of the Day' task started! ===")
    logger.info("======================================")

    logger.info("[1] Unregister all users from group")
    users = User.objects.exclude(joined_group__isnull=True)
    logger.info(f"[1] Users count: {len(users)}")
    users.update(joined_group=None)

    # Make Groups inactive
    logger.info("[2] Make Groups inactive")
    groups = Group.active_objects.all()
    logger.info(f"[2] Groups count: {len(groups)}")
    groups.update(is_active=False)

    # Make MatchRequest inactive
    logger.info("[3] Make MatchRequest inactive")
    mrs = MatchRequest.active_objects.all()
    logger.info(f"[3] MatchRequest count: {len(mrs)}")
    mrs.update(is_active=False)

    # Make Stream Chat inactive
    logger.info("[4] Make Stream Channel disabled")
    channels = stream.query_channels({"disabled": False})
    logger.info(f"[4] StreamChannel count: {len(channels['channels'])}")
    for channel in channels["channels"]:
        ch = stream.channel(
            channel_type=channel["channel"]["type"], channel_id=channel["channel"]["id"]
        )
        ch.update_partial(to_set={"disabled": True})

    logger.info("============== Success! ==============")


@shared_task(soft_time_limit=60)
def delete_scheduled_users():
    logger.info("======================================")
    logger.info("=== 'Delete Scheduled User' task started! ===")
    logger.info("======================================")

    logger.info("[1] Get users that are scheduled for deletion")
    ds_users = DeleteScheduledUser.objects.filter(
        Q(delete_processed=False) & Q(delete_schedule_at__lt=timezone.now())
    )
    logger.info(f"[1] Target users to be deleted: {ds_users}")

    # process deletion for each user
    for dsu in ds_users:
        user = dsu.user
        logger.info(f"=== Target user: {user.id} ===")
        logger.info("[2.1] Deactivate joined_group if any")
        # Disable group
        joined_group = user.joined_group
        if joined_group:
            joined_group.is_active = False
            joined_group.save(update_fields=["is_active"])

        # Deactivate MatchRequest
        logger.info("[2.2] Deactivate all MatchRequests")
        MatchRequest.active_objects.filter(sender_group=joined_group).update(
            is_active=False
        )
        MatchRequest.active_objects.filter(receiver_group=joined_group).update(
            is_active=False
        )

        # Deactivate Stream Chat
        logger.info("[2.3] Deactivate all Stream Chats")
        channels = stream.query_channels(
            filter_conditions={
                "members": {"$in": [str(user.id)]},
                "disabled": False,
            }
        )
        for channel in channels["channels"]:
            ch = stream.channel(
                channel_type=channel["channel"]["type"],
                channel_id=channel["channel"]["id"],
            )
            ch.update_partial(to_set={"disabled": True})

        # Mark user as deleted
        logger.info("[2.4] Mark user as `deleted`")
        user.joined_group = None
        user.is_deleted = True
        user.save(update_fields=["joined_group", "is_deleted"])

        # Mark DeleteScheduledUser as processed
        logger.info("[2.5] Mark DeleteScheduledUser as `processed`")
        dsu.delete_processed = True
        dsu.save(update_fields=["delete_processed"])
