from django.test import TestCase
from .models import Entry

class EntryModelTest(TestCase):
    def setUp(self):
        Entry.objects.create(title="Test Entry", content="This is a test entry.", last_modified_by="tester")

    def test_entry_creation(self):
        entry = Entry.objects.get(title="Test Entry")
        self.assertEqual(entry.content, "This is a test entry.")