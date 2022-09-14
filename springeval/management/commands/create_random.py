from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from springeval.models import ResultEntry, SpringUser
import random
import string


SFERRORS = ["err_SF_total", "err_SF_lowdetail", "err_SF_highdetail", "err_SF_rigid", "err_SF_nonrigid", "err_SF_matched", "err_SF_unmatched", "err_SF_notsky", "err_SF_sky", "err_1px_SF_total", "err_1px_SF_lowdetail", "err_1px_SF_highdetail", "err_1px_SF_rigid", "err_1px_SF_nonrigid", "err_1px_SF_matched", "err_1px_SF_unmatched", "err_1px_SF_notsky", "err_1px_SF_sky"]
D1ERRORS = ["err_1px_D1_total", "err_1px_D1_lowdetail", "err_1px_D1_highdetail", "err_1px_D1_notsky", "err_1px_D1_sky", "err_1px_D1_matched", "err_1px_D1_unmatched", "err_Abs_D1_total", "err_Abs_D1_lowdetail", "err_Abs_D1_highdetail", "err_Abs_D1_notsky", "err_Abs_D1_sky", "err_Abs_D1_matched", "err_Abs_D1_unmatched", "err_D1_total", "err_D1_lowdetail", "err_D1_highdetail", "err_D1_notsky", "err_D1_sky", "err_D1_matched", "err_D1_unmatched"]
D2ERRORS = ["err_1px_D2_total", "err_1px_D2_lowdetail", "err_1px_D2_highdetail", "err_1px_D2_notsky", "err_1px_D2_sky", "err_1px_D2_matched", "err_1px_D2_unmatched", "err_Abs_D2_total", "err_Abs_D2_lowdetail", "err_Abs_D2_highdetail", "err_Abs_D2_notsky", "err_Abs_D2_sky", "err_Abs_D2_matched", "err_Abs_D2_unmatched", "err_D2_total", "err_D2_lowdetail", "err_D2_highdetail", "err_D2_notsky", "err_D2_sky", "err_D2_matched", "err_D2_unmatched"]
FLERRORS = ["err_EPE_Fl_total", "err_EPE_Fl_lowdetail", "err_EPE_Fl_highdetail", "err_EPE_Fl_rigid", "err_EPE_Fl_nonrigid", "err_EPE_Fl_matched", "err_EPE_Fl_unmatched", "err_EPE_Fl_notsky", "err_EPE_Fl_sky", "err_Fl_total", "err_Fl_lowdetail", "err_Fl_highdetail", "err_Fl_rigid", "err_Fl_nonrigid", "err_Fl_matched", "err_Fl_unmatched", "err_Fl_notsky", "err_Fl_sky", "err_1px_Fl_total", "err_1px_Fl_lowdetail", "err_1px_Fl_highdetail", "err_1px_Fl_rigid", "err_1px_Fl_nonrigid", "err_1px_Fl_matched", "err_1px_Fl_unmatched", "err_1px_Fl_notsky", "err_1px_Fl_sky", "err_WAUC_Fl_total", "err_WAUC_Fl_lowdetail", "err_WAUC_Fl_highdetail", "err_WAUC_Fl_rigid", "err_WAUC_Fl_nonrigid", "err_WAUC_Fl_matched", "err_WAUC_Fl_unmatched", "err_WAUC_Fl_notsky", "err_WAUC_Fl_sky"]


class Command(BaseCommand):
    help = 'Creates Users and Random Entries'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int)

    def handle(self, *args, **options):
        # create 3 random users:
        mails = ["user1@test.test", "user2@test.test", "user3@test.test"]
        for usermail in mails:
            try:
                SpringUser.objects.get(email=usermail)
            except ObjectDoesNotExist as e:
                SpringUser.objects.create_user(email=usermail, university="University of Testing", password="opticalflow")
                self.stdout.write(f"Created user {usermail}")
        users = SpringUser.objects.filter(email__in=mails)

        for i in range(options["count"]):
            methodname = ""
            while True:
                methodname = "".join(random.choices(string.ascii_uppercase, k=4))
                try:
                    ResultEntry.objects.get(name=methodname)
                except ObjectDoesNotExist as e:
                    break
            visibility = random.choice(ResultEntry.VISIBILITY_CHOICES)[0]
            creator = random.choice(users)
            method_type = random.choice(ResultEntry.METHOD_TYPE_CHOICES)[0]

            errors = dict(zip(D1ERRORS+D2ERRORS+FLERRORS+SFERRORS, [-1]*96))
            if method_type == "ST":
                for e in D1ERRORS:
                    errors[e] = random.uniform(1,60)
            elif method_type == "FL":
                for e in FLERRORS:
                    errors[e] = random.uniform(1,60)
            else:
                for e in D1ERRORS+D2ERRORS+FLERRORS+SFERRORS:
                    errors[e] = random.uniform(1,60)
            ResultEntry.objects.create(pub_date=timezone.now(), name=methodname, visibility=visibility, process_status="SUCCESS", creator=creator, method_type=method_type, **errors)
