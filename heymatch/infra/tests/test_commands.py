from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class CustomCommandsTest(TestCase):
    def test_datasetup_command_output(self):
        out = StringIO()
        call_command("datasetup", stdout=out)
        output = out.getvalue()
        self.assertIn("Successfully set up all mocking data!", output)
