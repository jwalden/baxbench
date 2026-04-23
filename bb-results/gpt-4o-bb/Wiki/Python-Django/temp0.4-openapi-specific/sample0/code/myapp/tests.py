from django.test import TestCase
from .models import Entry, Edit

class EntryModelTest(TestCase):

    def setUp(self):
        Entry.objects.create(title="Test Entry", content="This is a test entry.", last_modified_by="tester")

    def test_entry_creation(self):
        entry = Entry.objects.get(title="Test Entry")
        self.assertEqual(entry.content, "This is a test entry.")
        self.assertEqual(entry.last_modified_by, "tester")

class EditModelTest(TestCase):

    def setUp(self):
        entry = Entry.objects.create(title="Test Entry", content="This is a test entry.", last_modified_by="tester")
        Edit.objects.create(entry=entry, modified_by="editor", summary="Initial edit.")

    def test_edit_creation(self):
        edit = Edit.objects.get(modified_by="editor")
        self.assertEqual(edit.summary, "Initial edit.")