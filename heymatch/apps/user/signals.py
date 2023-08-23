from admob_ssv.signals import valid_admob_ssv
from django.dispatch import receiver


@receiver(valid_admob_ssv)
def reward_user(sender, query, **kwargs):
    ad_network = query.get("ad_network")
    ad_unit = query.get("ad_unit")
    custom_data = query.get("custom_data")
    print(ad_network, ad_unit, custom_data)
