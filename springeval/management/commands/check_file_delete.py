from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from springeval.models import ResultEntry
import os
from pathlib import Path
from django.utils import timezone
import random


UPLOAD_DIRECTORY = os.environ["SPRING_UPLOADDIR"]

class Command(BaseCommand):
    help = 'Check if uploaded hdf files should be deleted'

    def handle(self, *args, **options):
        to_delete = []
        valid_files = []
        for f in Path(UPLOAD_DIRECTORY).iterdir():
            if not f.is_file():
                print("Strange directory found!", str(f))
                continue
            if f.suffix != ".hdf5":
                to_delete.append(f)
                continue
            parts = str(f.stem).split("__")
            if len(parts) != 4:
                to_delete.append(f)
                continue
            if parts[0] != "upload":
                to_delete.append(f)
                continue
            if parts[3] not in ["disp1", "disp2", "flow", "robust_disp1", "robust_disp2", "robust_flow"]:
                to_delete.append(f)
                continue
            if len(parts[2]) != 32:
                to_delete.append(f)
                continue
            try:
                parts[1] = int(parts[1])
            except:
                to_delete.append(f)
                continue
            valid_files.append(parts[1:] + [f])

        for entryid, imghash, submtype, fullpath in valid_files:
            try:
                entry = ResultEntry.objects.get(id=entryid)
            except ObjectDoesNotExist as e:
                to_delete.append(fullpath)
                continue
            if entry.imghash.hex != imghash:
                print("Wrong imghash!", fullpath)
                to_delete.append(fullpath)
                continue
            age = timezone.now()-entry.pub_date
            if entry.process_status == "SUCCESS":
                threshold1 = timezone.timedelta(days=360)
                if age > threshold1:
                    to_delete.append(fullpath)
                    continue
            else:
                threshold2 = timezone.timedelta(days=360*2)
                if age > threshold2:
                    to_delete.append(fullpath)
                    continue

        for d in to_delete:
            print("marked for deletion:", str(d))
        if len(to_delete) > 0:
            # only delete one entry at a time:
            delete_file = random.choice(to_delete)
            print("deleting file", delete_file)
            try:
                os.remove(to_delete[0])
                print("succesfully deleted", delete_file)
            except Exception as e:
                print(e)
                print("error while deleting file", delete_file)
