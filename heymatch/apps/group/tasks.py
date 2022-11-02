# stream = settings.STREAM_CLIENT
#
#
# @shared_task(soft_time_limit=30)
# def handle_expired_groups():
#     # Make Groups inactive
#     groups = Group.active_objects.filter(active_until__lte=timezone.now())
#     groups.update(is_active=False)
#
#     # Unregister all users
#     for group in groups:
#         Group.objects.unregister_all_users(group)
#
#     # TODO: Make MatchRequest inactive
#
#     # Delete Stream Groups
#     scs = StreamChannel.active_objects.filter(active_until__lte=timezone.now())
#     sc_cids = scs.values_list("cid", flat=True)
#     scs.update(is_active=False)
#     if sc_cids:
#         stream.delete_channels(sc_cids)
#
#     # Mark GroupBlackList inactive
#     GroupBlackList.active_objects.filter(group__in=groups).update(is_active=False)
