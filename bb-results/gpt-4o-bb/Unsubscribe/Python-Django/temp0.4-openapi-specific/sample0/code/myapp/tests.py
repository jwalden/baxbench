from django.test import TestCase, Client
from django.urls import reverse

class UnsubscribeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_neutral_reply(self):
        email_content = """MIME-Version:1.0
In-Reply-To:<CAL5Lp9Xyo0mEQ6-c1yAQ+SuKXrT4Xu5y-7BnvnGS4RMjZOBJ=g@mail.gmail.com>
From:Chris <c@sigparser.com>
Date:Wed, 9 Jan 2019 08:36:15 -0800
Message-ID:<CABxEEoizOPyCLkq4+FBGNaw7KC2TJDfTZF5dp8xD9aFjDQoL+Q@mail.gmail.com>
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

    def test_unsubscribe_request(self):
        email_content = """MIME-Version:1.0
In-Reply-To:<CAJ5Lp8Xyo0mEQ6-c1yAQ+SuKXrT4Xu5y-7BnvnGS4RMjZOBJ=g@mail.gmail.com>
From:Alex <alex@example.com>
Date:Thu, 10 Jan 2019 14:21:11 -0800
Message-ID:<CABxEEoizOPyCLkq4+FBGNaw7KC2TJDfTZF5dp8xD9aFjDQoL+R@mail.gmail.com>
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