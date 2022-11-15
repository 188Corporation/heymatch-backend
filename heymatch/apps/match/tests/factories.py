from factory import SubFactory
from factory.django import DjangoModelFactory

from heymatch.apps.group.tests.factories import ActiveGroupFactory
from heymatch.apps.match.models import MatchRequest


class MatchRequestFactory(DjangoModelFactory):
    class Meta:
        model = MatchRequest

    sender_group = SubFactory(ActiveGroupFactory)
    receiver_group = SubFactory(ActiveGroupFactory)
