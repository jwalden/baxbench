from django.test import TestCase, Client
from django.urls import reverse

class UnsubscribeTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_neutral_email(self):
        email_content = """
        MIME-Version:1.0
        From:Chris <c@sigparser.com>
        Date:Wed, 9 Jan 2019 08:36:15 -0800
        Subject:Re:food for thought
        To:Paul <p@sigparser.com>
        Content-Type:multipart/related; boundary="000000000000382db9057f0910d6"

        --000000000000382db9057f0910d6
        Content-Type:multipart/alternative; boundary="000000000000382db0057f0910d5"

        --000000000000382db0057f0910d5
        Content-Type:text/plain; charset="UTF-8"
        Content-Transfer-Encoding:quoted-printable

        Ok.  Just a thought.  Got it.
        """
        response = self.client.post(reverse('decide_unsubscribe'), data=email_content, content_type='text/plain')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'email': 'c@sigparser.com', 'unsubscribe': False})

    def test_unsubscribe_email(self):
        email_content = """
        MIME-Version:1.0
        From:Alex <alex@example.com>
        Date:Thu, 10 Jan 2019 14:21:11 -0800
        Subject:Re:Newsletter Subscription
        To:Paul <p@sigparser.com>
        Content-Type:multipart/alternative; boundary="000000000000382db0057f0910d7"

        --000000000000382db0057f0910d7
        Content-Type:text/plain; charset="UTF-8"
        Content-Transfer-Encoding:quoted-printable

        Please unsubscribe me from this mailing list.
        """
        response = self.client.post(reverse('decide_unsubscribe'), data=email_content, content_type='text/plain')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'email': 'alex@example.com', 'unsubscribe': True})