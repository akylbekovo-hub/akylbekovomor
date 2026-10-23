from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("omor", "omor@example.com", "pass12345")
        self.other = User.objects.create_user("other", "other@example.com", "pass12345")

    def test_profile_created_by_signal(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_anonymous_redirected_to_login(self):
        for name in ("accounts:profile", "accounts:profile_edit"):
            url = reverse(name)
            resp = self.client.get(url)
            self.assertRedirects(resp, f"{reverse('accounts:login')}?next={url}")

    def test_profile_view(self):
        self.client.login(username="omor", password="pass12345")
        resp = self.client.get(reverse("accounts:profile"))
        self.assertContains(resp, "omor@example.com")
        self.assertContains(resp, "Редактировать профиль")

    def test_old_user_without_profile(self):
        Profile.objects.filter(user=self.user).delete()
        self.client.login(username="omor", password="pass12345")
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:profile_edit")).status_code, 200)

    def test_edit_saves_only_own_profile(self):
        self.client.login(username="omor", password="pass12345")
        resp = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "Омор", "last_name": "Акылбеков", "email": "new@example.com",
            "city": "Бишкек", "bio": "Студент", "birth_date": "2005-01-02",
            "is_staff": "on", "username": "hacked",
        }, follow=True)
        self.assertContains(resp, "Профиль обновлён")
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(self.user.first_name, "Омор")
        self.assertEqual(self.user.profile.city, "Бишкек")
        self.assertFalse(self.user.is_staff)
        self.assertEqual(self.user.username, "omor")
        self.assertEqual(self.other.profile.city, "")

    def test_duplicate_email_rejected(self):
        self.client.login(username="omor", password="pass12345")
        resp = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "", "last_name": "", "email": "other@example.com",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "уже существует")

    def test_own_email_allowed(self):
        self.client.login(username="omor", password="pass12345")
        resp = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "", "last_name": "", "email": "omor@example.com",
        })
        self.assertRedirects(resp, reverse("accounts:profile"))
