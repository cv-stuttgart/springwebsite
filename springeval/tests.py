from datetime import timedelta

import numpy as np
from django.test import TestCase
from django.utils import timezone

from springeval.management.commands.evaluation import compute_disp2_robust_errors
from springeval.management.robustness_eval_utils import apply_robust_sceneflow_totals
from springeval.models import ResultEntry, SpringUser


class ComputeDisp2RobustErrorsTests(TestCase):
    def test_basic_metrics(self):
        clean = np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32)
        corrupted = np.array([11.5, 20.0, 36.0, 40.0], dtype=np.float32)

        onepx, abs_total, d2 = compute_disp2_robust_errors(clean, corrupted)

        self.assertAlmostEqual(onepx, 50.0)
        self.assertAlmostEqual(abs_total, 1.875)
        self.assertAlmostEqual(d2, 25.0)

    def test_clipping_limits_extreme_values(self):
        clean = np.array([0.0, 1e7], dtype=np.float32)
        corrupted = np.array([0.0, 0.0], dtype=np.float32)

        onepx, abs_total, d2 = compute_disp2_robust_errors(clean, corrupted)

        self.assertAlmostEqual(abs_total, 5e5)
        self.assertAlmostEqual(onepx, 50.0)
        self.assertAlmostEqual(d2, 50.0)

    def test_fixed_disp_len_threshold(self):
        clean = np.array([100.0, 100.0], dtype=np.float32)
        corrupted = np.array([94.0, 95.0], dtype=np.float32)

        onepx, abs_total, d2 = compute_disp2_robust_errors(clean, corrupted)

        self.assertAlmostEqual(onepx, 100.0)
        self.assertAlmostEqual(abs_total, 5.5)
        # D2 requires epe > 3 and epe > 0.05 * 100 (= 5); only the 6px error qualifies.
        self.assertAlmostEqual(d2, 50.0)

    def test_raises_on_nan(self):
        clean = np.array([1.0, np.nan], dtype=np.float32)
        corrupted = np.array([1.0, 2.0], dtype=np.float32)

        with self.assertRaises(ValueError):
            compute_disp2_robust_errors(clean, corrupted)


class RobustSceneflowTotalsTests(TestCase):
    def setUp(self):
        self.user = SpringUser.objects.create_user(
            email="sf@test.edu",
            university="Test University",
            password="testpass",
        )

    def test_apply_robust_sceneflow_totals_maps_nested_dict(self):
        entry = ResultEntry.objects.create(
            name="sf-method",
            pub_date=timezone.now(),
            creator=self.user,
            method_type="SF",
            process_status="SUCCESS",
            evaluate_robustness=True,
        )
        total = {
            "disp1": {
                "disp1_1px_total": 10.5,
                "disp1_Abs_total": 11.5,
                "disp1_D1_total": 12.5,
            },
            "disp2": {
                "disp2_1px_total": 20.5,
                "disp2_Abs_total": 21.5,
                "disp2_D2_total": 22.5,
            },
            "flow": {
                "flow_EPE_total": 30.5,
                "flow_Fl_total": 31.5,
                "flow_1px_total": 32.5,
            },
        }
        apply_robust_sceneflow_totals(entry, total)
        entry.save()

        entry.refresh_from_db()
        self.assertEqual(entry.robust_disp1_1px_total, 10.5)
        self.assertEqual(entry.robust_disp1_Abs_total, 11.5)
        self.assertEqual(entry.robust_disp1_D1_total, 12.5)
        self.assertEqual(entry.robust_disp2_1px_total, 20.5)
        self.assertEqual(entry.robust_disp2_Abs_total, 21.5)
        self.assertEqual(entry.robust_disp2_D2_total, 22.5)
        self.assertEqual(entry.robust_flow_EPE_total, 30.5)
        self.assertEqual(entry.robust_flow_Fl_total, 31.5)
        self.assertEqual(entry.robust_flow_1px_total, 32.5)


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
