from springeval.models import RobustCorruptionResult


def apply_robust_sceneflow_totals(entry, total):
    """Map nested scene-flow robust totals onto ResultEntry aggregate fields."""
    disp1 = total.get("disp1", {})
    disp2 = total.get("disp2", {})
    flow = total.get("flow", {})
    entry.robust_disp1_1px_total = disp1.get("disp1_1px_total", -1)
    entry.robust_disp1_Abs_total = disp1.get("disp1_Abs_total", -1)
    entry.robust_disp1_D1_total = disp1.get("disp1_D1_total", -1)
    entry.robust_disp2_1px_total = disp2.get("disp2_1px_total", -1)
    entry.robust_disp2_Abs_total = disp2.get("disp2_Abs_total", -1)
    entry.robust_disp2_D2_total = disp2.get("disp2_D2_total", -1)
    entry.robust_flow_EPE_total = flow.get("flow_EPE_total", -1)
    entry.robust_flow_Fl_total = flow.get("flow_Fl_total", -1)
    entry.robust_flow_1px_total = flow.get("flow_1px_total", -1)


def save_robust_sceneflow_corruptions(entry, by_corruption):
    for corruption, metrics in by_corruption.items():
        defaults = {
            "robust_disp1_1px": metrics.get("disp1", {}).get("onepx_total", -1),
            "robust_disp1_Abs": metrics.get("disp1", {}).get("abs_total", -1),
            "robust_disp1_D1": metrics.get("disp1", {}).get("d1_total", -1),
            "robust_disp2_1px": metrics.get("disp2", {}).get("onepx_total", -1),
            "robust_disp2_Abs": metrics.get("disp2", {}).get("abs_total", -1),
            "robust_disp2_D2": metrics.get("disp2", {}).get("d2_total", -1),
            "robust_flow_EPE": metrics.get("flow", {}).get("epe_total", -1),
            "robust_flow_Fl": metrics.get("flow", {}).get("fl_total", -1),
            "robust_flow_1px": metrics.get("flow", {}).get("onepx_total", -1),
        }
        RobustCorruptionResult.objects.update_or_create(
            result_entry=entry,
            corruption_name=corruption,
            defaults=defaults,
        )


def save_robust_sceneflow_results(entry, robust_results):
    apply_robust_sceneflow_totals(entry, robust_results.get("total", {}))
    save_robust_sceneflow_corruptions(entry, robust_results.get("by_corruption", {}))


def robust_sceneflow_file_paths(robust_disp1_path):
    return (
        robust_disp1_path,
        robust_disp1_path[:-17] + "robust_disp2.hdf5",
        robust_disp1_path[:-17] + "robust_flow.hdf5",
    )
