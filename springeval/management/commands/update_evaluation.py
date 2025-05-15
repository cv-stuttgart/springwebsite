from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from springeval.management.commands.evaluation import (
    evaluate_submission_disp1,
    evaluate_submission_flow,
    evaluate_submission_sceneflow,
    evaluate_robust_submission_disp1,
    evaluate_robust_submission_flow,
    evaluate_robust_submission_sceneflow
)
from springeval.models import ResultEntry, RobustCorruptionResult
import os
import traceback

UPLOAD_DIRECTORY = os.environ["SPRING_UPLOADDIR"]
IMG_DIR = os.path.join(os.environ["SPRING_IMGDIR"], "media")

class Command(BaseCommand):
    help = 'Check for new evaluation files (including robustness files)'

    def handle(self, *args, **options):
        data_standard = []
        data_robust = []
        for f in os.listdir(UPLOAD_DIRECTORY):
            full_path = os.path.join(UPLOAD_DIRECTORY, f)
            if not os.path.isfile(full_path):
                continue
            if not f.endswith(".hdf5"):
                continue
            parts = f[:-5].split("__")
            if len(parts) != 4:
                continue
            if parts[0] != "upload":
                continue
            # Separate standard from robustness files
            if parts[3] in ["disp1", "disp2", "flow"]:
                try:
                    parts[1] = int(parts[1])
                except:
                    continue
                data_standard.append(parts[1:] + [full_path])
            elif parts[3] in ["robust_disp1", "robust_disp2", "robust_flow"]:
                try:
                    parts[1] = int(parts[1])
                except:
                    continue
                data_robust.append(parts[1:] + [full_path])
            else:
                continue

        # Group standard submission files by method type
        stereo = []
        flow = []
        sceneflow = []

        for entryid, imghash, submtype, full_path in data_standard:
            try:
                entry = ResultEntry.objects.get(id=entryid)
            except ObjectDoesNotExist:
                continue
            if entry.imghash.hex != imghash:
                continue
            if entry.process_status != "WAIT_PROC":
                continue
            if entry.method_type == "ST":
                if submtype != "disp1":
                    continue
                stereo.append((entryid, imghash, full_path))
            elif entry.method_type == "FL":
                if submtype != "flow":
                    continue
                flow.append((entryid, imghash, full_path))
            elif entry.method_type == "SF":
                if submtype != "disp1":
                    continue
                if not any([(e == entryid) and (i == imghash) and (s == "disp2") for e, i, s, _ in data_standard]):
                    continue
                if not any([(e == entryid) and (i == imghash) and (s == "flow") for e, i, s, _ in data_standard]):
                    continue
                sceneflow.append((entryid, imghash, full_path))

        # Group robustness files similarly
        robust_stereo = []
        robust_flow = []
        robust_sceneflow = []

        for entryid, imghash, submtype, full_path in data_robust:
            try:
                entry = ResultEntry.objects.get(id=entryid)
            except ObjectDoesNotExist:
                continue
            if entry.imghash.hex != imghash:
                continue
            if entry.process_status != "WAIT_PROC":
                continue
            if entry.method_type == "ST":
                if submtype != "robust_disp1":
                    continue
                robust_stereo.append((entryid, imghash, full_path))
            elif entry.method_type == "FL":
                if submtype != "robust_flow":
                    continue
                robust_flow.append((entryid, imghash, full_path))
            elif entry.method_type == "SF":
                if submtype != "robust_disp1":
                    continue
                if not any([(e == entryid) and (i == imghash) and (s == "robust_disp2") for e, i, s, _ in data_robust]):
                    continue
                if not any([(e == entryid) and (i == imghash) and (s == "robust_flow") for e, i, s, _ in data_robust]):
                    continue
                robust_sceneflow.append((entryid, imghash, full_path))

        print("Stereo:", stereo)
        print("Flow:", flow)
        print("Scene flow:", sceneflow)
        print("Robust - Stereo:", robust_stereo)
        print("Robust - Flow:", robust_flow)
        print("Robust - Scene flow:", robust_sceneflow)

        # Evaluate standard submissions
        for entryid, imghash, full_path in stereo:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            entry = ResultEntry.objects.get(id=entryid)
            try:
                results = evaluate_submission_disp1(full_path, outputimgdir)
            except Exception:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            for k, v in results.items():
                setattr(entry, k, v)
            entry.process_status = "SUCCESS"
            entry.save()

        for entryid, imghash, full_path in flow:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            entry = ResultEntry.objects.get(id=entryid)
            try:
                results = evaluate_submission_flow(full_path, outputimgdir)
            except Exception:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            for k, v in results.items():
                setattr(entry, k, v)
            entry.process_status = "SUCCESS"
            entry.save()

        for entryid, imghash, full_path in sceneflow:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            file_d1 = full_path
            file_d2 = full_path[:-10] + "disp2.hdf5"
            file_fl = full_path[:-10] + "flow.hdf5"
            entry = ResultEntry.objects.get(id=entryid)
            try:
                results = evaluate_submission_sceneflow(file_d1, file_d2, file_fl, outputimgdir)
            except Exception:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            for k, v in results.items():
                setattr(entry, k, v)
            entry.process_status = "SUCCESS"
            entry.save()

        # Evaluate robust submissions
        for entryid, imghash, full_path in robust_stereo:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            entry = ResultEntry.objects.get(id=entryid)
            try:
                robust_results = evaluate_robust_submission_disp1(full_path)
            except Exception:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            
            total_errors = robust_results.get("total", {})
            for k, v in total_errors.items():
                setattr(entry, "robust_" + k, v)
                
            by_corr = robust_results.get("by_corruption", {})
            for corruption, metrics in by_corr.items():
                RobustCorruptionResult.objects.update_or_create(
                    result_entry=entry,
                    corruption_name=corruption,
                    defaults={
                        "robust_1px_D1": metrics.get("onepx_total", -1),
                        "robust_Abs_D1": metrics.get("abs_total", -1),
                        "robust_D1": metrics.get("d1_total", -1),
                    }
                )
            entry.process_status = "SUCCESS"
            entry.save()

        for entryid, imghash, full_path in robust_flow:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            entry = ResultEntry.objects.get(id=entryid)
            try:
                robust_results = evaluate_robust_submission_flow(full_path)
            except Exception:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            
            total_errors = robust_results.get("total", {})
            for k, v in total_errors.items():
                setattr(entry, "robust_" + k, v)
            
            by_corr = robust_results.get("by_corruption", {})
            for corruption, metrics in by_corr.items():
                RobustCorruptionResult.objects.update_or_create(
                    result_entry=entry,
                    corruption_name=corruption,
                    defaults={
                        "robust_EPE_Fl": metrics.get("epe_total", -1),
                        "robust_Fl": metrics.get("fl_total", -1),
                        "robust_1px_Fl": metrics.get("onepx_total", -1),
                    }
                )
            entry.process_status = "SUCCESS"
            entry.save()

        for entryid, imghash, full_path in robust_sceneflow:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            file_d1 = full_path
            file_d2 = full_path[:17] + "robust_disp2.hdf5"
            file_fl = full_path[:17] + "robust_flow.hdf5"
            entry = ResultEntry.objects.get(id=entryid)
            try:
                robust_results = evaluate_robust_submission_sceneflow(file_d1, file_d2, file_fl)
            except Exception:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            
            total_errors = robust_results.get("total", {})
            for k, v in total_errors.items():
                setattr(entry, "robust_" + k, v)
                
            by_corr = robust_results.get("by_corruption", {})
            for corruption, metrics in by_corr.items():
                defaults = {
                    "robust_disp1_1px": metrics.get("disp1", {}).get("onepx_total", -1),
                    "robust_disp1_Abs": metrics.get("disp1", {}).get("abs_total", -1),
                    "robust_disp1_D1": metrics.get("disp1", {}).get("d1_total", -1),
                    "robust_disp2_1px": metrics.get("disp2", {}).get("onepx_total", -1),
                    "robust_disp2_Abs": metrics.get("disp2", {}).get("abs_total", -1),
                    "robust_disp2_D2": metrics.get("disp2", {}).get("d1_total", -1),
                    "robust_flow_EPE": metrics.get("flow", {}).get("epe_total", -1),
                    "robust_flow_Fl": metrics.get("flow", {}).get("fl_total", -1),
                    "robust_flow_1px": metrics.get("flow", {}).get("onepx_total", -1),
                }
                RobustCorruptionResult.objects.update_or_create(
                    result_entry=entry,
                    corruption_name=corruption,
                    defaults=defaults
                )
            entry.process_status = "SUCCESS"
            entry.save()
