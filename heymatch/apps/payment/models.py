from django.db import models


class PointItem(models.Model):
    name = models.CharField(blank=False, null=False, unique=True, max_length=32)
    price_in_krw = models.IntegerField(blank=False, null=False)
    default_point = models.IntegerField(blank=False, null=False)
    bonus_point = models.IntegerField(blank=True, null=True, default=0)
    best_deal_check = models.BooleanField(blank=True, null=True, default=False)

    @property
    def krw_per_point(self):
        return round(self.price_in_krw / (self.default_point + self.bonus_point), 2)


class FreePassItem(models.Model):
    name = models.CharField(blank=False, null=False, unique=True, max_length=32)
    price_in_krw = models.IntegerField(blank=False, null=False)
    free_pass_duration_in_hour = models.IntegerField(blank=False, null=False)
    best_deal_check = models.BooleanField(blank=True, null=True, default=False)
