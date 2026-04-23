from django.test import TestCase
from .models import Entry, Edit

class EntryModelTest(TestCase):

    def setUp(self):
        self.entry = Entry.objects.create(title="Test Entry", content="This is a test entry", last_modified_by="tester")

    def test_entry_creation(self):
        self.assertEqual(self.entry.title, "Test Entry")
        self.assertEqual(self.entry.content, "This is a test entry")
        self.assertEqual(self.entry.last_modified_by, "tester")

class EditModelTest(TestCase):

    def setUp(self):
        self.entry = Entry.objects.create(title="Test Entry", content="This is a test entry", last_modified_by="tester")
        self.edit = Edit.objects.create(entry=self.entry, content="Edited content", modified_by="editor", summary="Initial edit")

    def test_edit_creation(self):
        self.assertEqual(self.edit.entry, self.entry)
        self.assertEqual(self.edit.content, "Edited content")
        self.assertEqual(self.edit.modified_by, "editor")
        self.assertEqual(self.edit.summary, "Initial edit")