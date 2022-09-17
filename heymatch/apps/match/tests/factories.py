from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from heymatch.apps.group.tests.factories import ActiveGroupFactory
from heymatch.apps.match.models import MatchRequest


class MatchRequestFactory(DjangoModelFactory):
    class Meta:
        model = MatchRequest

    uuid = Faker("uuid4")
    sender = SubFactory(ActiveGroupFactory)
    receiver = SubFactory(ActiveGroupFactory)
    unread = True
    accepted = False
    denied = False
