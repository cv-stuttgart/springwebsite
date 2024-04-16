from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from springeval.management.commands.evaluation import evaluate_submission_disp1, evaluate_submission_flow, evaluate_submission_sceneflow
from springeval.models import ResultEntry
import os
import traceback
from pathlib import Path

UPLOAD_DIRECTORY = os.environ["SPRING_UPLOADDIR"]

class Command(BaseCommand):
    help = 'Check if uploaded hdf files should be deleted'

    def handle(self, *args, **options):
        to_delete = []
        valid_files = []
        for f in Path(UPLOAD_DIRECTORY).iterdir():
            if not f.is_file():
                print("Strange directory found!", str(f))
            if not f.suffix == "hdf5":
                to_delete.append(f)
                continue
            parts = str(f.stem).split("__")
            if len(parts) != 4:
                to_delete.append(f)
                continue
            if parts[0] != "upload":
                to_delete.append(f)
                continue
            if parts[3] not in ["disp1", "disp2", "flow"]:
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

        print(to_delete)
        print(valid_files)
