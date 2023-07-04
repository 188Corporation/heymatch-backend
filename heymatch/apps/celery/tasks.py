import datetime
import json
from collections import Counter

import pandas as pd
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
    GroupV2,
    Recent24HrTopGroupAddress,
)
from heymatch.apps.match.models import MatchRequest
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
    date_from = timezone.now() - datetime.timedelta(days=1)
    last_24_group_addresses = list(
        GroupV2.objects.filter(created_at__gte=date_from, is_active=True).values_list(
            "gps_address", flat=True
        )
    )
    if len(last_24_group_addresses) > 5:
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


@shared_task(soft_time_limit=120)
def update_school_company_database():
    company_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuyG7ft8IsuRzGqWYqDC963W2-nG_fKkKDn_Xp7cGwoFpFgYPKx46jhIobyEn3cpIoi62PNJx-V7oT/pub?gid=0&single=true&output=csv"  # noqa: E501
    school_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuyG7ft8IsuRzGqWYqDC963W2-nG_fKkKDn_Xp7cGwoFpFgYPKx46jhIobyEn3cpIoi62PNJx-V7oT/pub?gid=903166839&single=true&output=csv"  # noqa: E501

    ################
    # Update Company
    ################
    df = pd.read_csv(company_url, on_bad_lines="skip")
    db = {}
    for idx, line in df.iterrows():
        company_name = line["회사명 출력"]
        company_name_alt = line["회사명"]
        email = line["이메일"]

        if not email or type(email) is float:
            continue

        if not company_name and not company_name_alt:
            continue

        company_emails = email.replace(" ", "").split(",")
        company_name_final = company_name_alt if not company_name else company_name
        for email in company_emails:
            if email in db:
                if company_name_final not in db[email]:
                    db[email].append(company_name_final)
            else:
                db[email] = [company_name_final]

    # save to json
    with open(
        f"{settings.APPS_DIR}/data/domains/company.json", "w", encoding="utf-8"
    ) as f:
        json.dump(db, f, indent="\t", ensure_ascii=False)

    ################
    # Update School
    ################
    df = pd.read_csv(school_url)
    db = {}
    for idx, line in df.iterrows():
        school_name = line["학교명"]
        email = line["이메일"]
        if not email or type(email) is float:
            continue
        db[email] = school_name

    # save to json
    with open("../heymatch/data/domains/school.json", "w", encoding="utf-8") as f:
        json.dump(db, f, indent="\t", ensure_ascii=False)


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
