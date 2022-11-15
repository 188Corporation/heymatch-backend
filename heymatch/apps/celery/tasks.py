import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model

from heymatch.apps.group.models import Group
from heymatch.apps.match.models import MatchRequest

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
