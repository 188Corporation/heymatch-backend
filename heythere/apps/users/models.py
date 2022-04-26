from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, IntegerField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError
from datetime import date


def validate_birth_year(value: int):
    if value not in range(1900, date.today().year):
        raise ValidationError(
            _('%(value)s is not a valid birth year'),
            params={'value': value},
        )


def validate_height_cm(value: int):
    if value not in range(100, 300):
        raise ValidationError(
            _('%(value)s is not a valid height in centi-meter'),
            params={'value': value},
        )


GENDER_CHOICES = (
    (0, 'male'),
    (1, 'female'),
    (2, 'not specified'),
)


class User(AbstractUser):
    #: First and last name do not cover name patterns around the globe
    phone_number = PhoneNumberField(_("Phone number of User"), null=False, blank=False, unique=True)

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


class UserProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nickname = CharField(_("Nickname of User"), blank=False, null=False, max_length=32)
    birth_year = IntegerField(_("Birth Year of User"), blank=False, null=False, validators=[validate_birth_year])
    gender = models.IntegerField(_("Gender of User"), blank=False, null=False, choices=GENDER_CHOICES)
    height_cm = models.IntegerField(_("Height(cm) of User"), blank=False, null=False, validators=[validate_height_cm])
    workplace = models.CharField(_("Workplace of User"), blank=True, null=True, max_length=32)
    school = models.CharField(_("School of User"), blank=True, null=True, max_length=32)
