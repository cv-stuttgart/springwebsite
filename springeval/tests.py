from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from springeval.models import ResultEntry, SpringUser


class RobustnessLimitTests(TestCase):
    def setUp(self):
        self.user = SpringUser.objects.create_user(
            email="user@test.edu",
            university="Test University",
            password="testpass",
        )
        self.user.is_active = True
        self.user.is_verified = True
        self.user.save()

        self.admin = SpringUser.objects.create_superuser(
            email="admin@test.edu",
            password="adminpass",
        )

    def _make_entry(
        self,
        name="method",
        evaluate_robustness=False,
        robustness_pub_date=None,
        pub_date=None,
    ):
        return ResultEntry.objects.create(
            name=name,
            pub_date=pub_date or timezone.now() - timedelta(days=5),
            creator=self.user,
            method_type="ST",
            process_status="SUCCESS",
            evaluate_robustness=evaluate_robustness,
            robustness_pub_date=robustness_pub_date,
        )

    def test_first_late_addition_allowed(self):
        entry = self._make_entry()
        self.assertTrue(self.user.can_add_robustness(entry))
        self.assertEqual(self.user.get_robustness_reasons(entry), [])

    def test_first_late_addition_allowed_despite_regular_limits(self):
        self._make_entry(name="recent1", pub_date=timezone.now())
        entry = self._make_entry(name="target")
        self.assertFalse(self.user.can_upload())
        self.assertTrue(self.user.can_add_robustness(entry))

    def test_second_addition_within_hour_blocked(self):
        self._make_entry(
            name="first-robust",
            evaluate_robustness=True,
            robustness_pub_date=timezone.now() - timedelta(minutes=10),
        )
        entry = self._make_entry(name="second-target")
        reasons = self.user.get_robustness_reasons(entry)
        self.assertFalse(self.user.can_add_robustness(entry))
        self.assertTrue(any("last hour" in r for r in reasons))

    def test_third_addition_within_30_days_blocked(self):
        for i in range(3):
            self._make_entry(
                name=f"robust-{i}",
                evaluate_robustness=True,
                robustness_pub_date=timezone.now() - timedelta(days=i + 1),
            )
        entry = self._make_entry(name="fourth-target")
        reasons = self.user.get_robustness_reasons(entry)
        self.assertFalse(self.user.can_add_robustness(entry))
        self.assertTrue(any("30 days" in r for r in reasons))

    def test_entry_with_existing_robustness_blocked(self):
        entry = self._make_entry(evaluate_robustness=True)
        reasons = self.user.get_robustness_reasons(entry)
        self.assertFalse(self.user.can_add_robustness(entry))
        self.assertTrue(any("already has a robustness evaluation" in r for r in reasons))

    def test_admin_exempt(self):
        self._make_entry(
            name="first-robust",
            evaluate_robustness=True,
            robustness_pub_date=timezone.now(),
        )
        entry = self._make_entry(name="second-target")
        self.assertTrue(self.admin.can_add_robustness(entry))

    def test_unverified_user_blocked(self):
        self.user.is_verified = False
        self.user.save()
        entry = self._make_entry()
        reasons = self.user.get_robustness_reasons(entry)
        self.assertFalse(self.user.can_add_robustness(entry))
        self.assertTrue(any("not verified" in r for r in reasons))
