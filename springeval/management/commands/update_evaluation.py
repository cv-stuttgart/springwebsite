from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from springeval.management.commands.evaluation import evaluate_submission_disp1, evaluate_submission_flow, evaluate_submission_sceneflow
from springeval.models import ResultEntry
import os
import traceback

UPLOAD_DIRECTORY = os.environ["SPRING_UPLOADDIR"]
IMG_DIR = os.path.join(os.environ["SPRING_IMGDIR"], "media")

class Command(BaseCommand):
    help = 'Check for new evaluation files'

    def handle(self, *args, **options):
        
        data = []
        for f in os.listdir(UPLOAD_DIRECTORY):
            if not os.path.isfile(os.path.join(UPLOAD_DIRECTORY, f)):
                continue
            if not f.endswith(".hdf5"):
                continue
            parts = f[:-5].split("__")
            if len(parts) != 4:
                continue
            if parts[0] != "upload":
                continue
            if parts[3] not in ["disp1", "disp2", "flow"]:
                continue
            if len(parts[2]) != 32:
                continue
            try:
                parts[1] = int(parts[1])
            except:
                continue
            data.append(parts[1:] + [os.path.join(UPLOAD_DIRECTORY, f)])

        stereo = []
        flow = []
        sceneflow = []

        for entryid, imghash, submtype, fullpath in data:
            try:
                entry = ResultEntry.objects.get(id=entryid)
            except ObjectDoesNotExist as e:
                continue
            if entry.imghash.hex != imghash:
                continue
            if entry.process_status != "WAIT_PROC":
                continue
            if entry.method_type == "ST":
                if submtype != "disp1":
                    continue
                stereo.append((entryid, imghash, fullpath))
            elif entry.method_type == "FL":
                if submtype != "flow":
                    continue
                flow.append((entryid, imghash, fullpath))
            elif entry.method_type == "SF":
                if submtype != "disp1":
                    continue
                if not any([(e==entryid) and (i==imghash) and (s=="disp2") for e,i,s,_ in data]):
                    continue
                if not any([(e==entryid) and (i==imghash) and (s=="flow") for e,i,s,_ in data]):
                    continue
                sceneflow.append((entryid, imghash, fullpath))

        print("Stereo:", stereo)
        print("Flow:", flow)
        print("Scene flow:", sceneflow)

        for entryid, imghash, fullpath in stereo:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            entry = ResultEntry.objects.get(id=entryid)
            try:
                results = evaluate_submission_disp1(fullpath, outputimgdir)
            except Exception as e:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            for k,v in results.items():
                setattr(entry, k, v)
            entry.process_status = "SUCCESS"
            entry.save()

        for entryid, imghash, fullpath in flow:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            entry = ResultEntry.objects.get(id=entryid)
            try:
                results = evaluate_submission_flow(fullpath, outputimgdir)
            except Exception as e:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            for k,v in results.items():
                setattr(entry, k, v)
            entry.process_status = "SUCCESS"
            entry.save()

        for entryid, imghash, fullpath in sceneflow:
            outputimgdir = os.path.join(IMG_DIR, imghash)
            file_d1 = fullpath
            file_d2 = fullpath[:-10] + "disp2.hdf5"
            file_fl = fullpath[:-10] + "flow.hdf5"
            entry = ResultEntry.objects.get(id=entryid)
            try:
                results = evaluate_submission_sceneflow(file_d1, file_d2, file_fl, outputimgdir)
            except Exception as e:
                print(traceback.format_exc())
                entry.process_status = "FAIL"
                entry.save()
                continue
            for k,v in results.items():
                setattr(entry, k, v)
            entry.process_status = "SUCCESS"
            entry.save()
