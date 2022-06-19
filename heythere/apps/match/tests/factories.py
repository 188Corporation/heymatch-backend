from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from heythere.apps.group.tests.factories import ActiveGroupFactory
from heythere.apps.match.models import MatchRequest


class MatchRequestFactory(DjangoModelFactory):
    class Meta:
        model = MatchRequest

    uuid = Faker("uuid4")
    sender = SubFactory(ActiveGroupFactory)
    receiver = SubFactory(ActiveGroupFactory)
    unread = True
    accepted = False
    denied = False
