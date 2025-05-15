import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


RESULTENTRY_NAME_MAX_LENGTH = 50

class SpringUserManager(BaseUserManager):
    def create_user(self, email, university, website=None, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            university=university,
            website=website
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, university="Superuser University", website=None, password=None):
        user = self.create_user(
            email,
            password=password,
            university=university,
            website=website
        )
        user.is_admin = True
        user.is_verified = True
        user.save(using=self._db)
        return user


class SpringUser(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address*',
        max_length=255,
        unique=True,
        help_text="Please use your university/organisation mail address."
    )

    university = models.CharField(verbose_name="University/Organization*", max_length=100)
    website = models.URLField(verbose_name="Personal website", blank=True, null=True)
    description = models.TextField(verbose_name="Description*", max_length=1000, help_text="Please provide a brief justification of why you need access to the benchmark.")

    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    objects = SpringUserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    def can_upload(self):
        return len(self.getreasons()) == 0

    def submissioncount(self, timespan):
        result = len(ResultEntry.objects.filter(creator__exact=self.pk).filter(process_status__in=["SUCCESS", "WAIT_UPL", "WAIT_PROC"]).filter(pub_date__gte=timezone.now() - timespan))
        return result

    def getreasons(self):
        reasons = []
        if not self.is_verified:
            reasons.append("Your account is not verified yet by our team. Please check again later.")
        if self.submissioncount(timezone.timedelta(hours=1)) > 0:
            reasons.append("You had a submission in the last hour. We allow at most one submission per hour.")
        if self.submissioncount(timezone.timedelta(days=30)) >= 3:
            reasons.append("You had 3 submission in the last 30 days. We allow at most 3 submissions per 30 days.")
        return reasons

    def maildomain(self):
        return self.email.split("@")[-1]


class ResultEntry(models.Model):
    name = models.CharField(max_length=RESULTENTRY_NAME_MAX_LENGTH)
    pub_date = models.DateTimeField('date published')
    VISIBILITY_CHOICES = (
        ("PUBL", "Public"),
        ("PRIV", "Private"),
        ("ANON", "Anonymous")
    )
    visibility = models.CharField(max_length=4, choices=VISIBILITY_CHOICES, blank=False, default="PRIV")
    citation = models.CharField(max_length=400, blank=True)

    METHOD_TYPE_CHOICES = (
        ("ST", "Stereo"),
        ("FL", "Optical Flow"),
        ("SF", "Scene Flow")
    )
    method_type = models.CharField(max_length=2, choices=METHOD_TYPE_CHOICES)

    creator = models.ForeignKey(SpringUser, on_delete=models.CASCADE)

    #images
    imghash = models.UUIDField(default=uuid.uuid4, unique=True)

    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("WAIT_UPL", "Waiting for upload..."),
        ("WAIT_PROC", "Waiting for evaluation..."),
        ("FAIL", "There was a problem with the submission.")
    )
    process_status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=False, null=False)

    code_url = models.URLField(verbose_name="Link to code", blank=True, null=True)
    
    evaluate_robustness = models.BooleanField(default=False)

    # Standard evaluation fields
    err_SF_total = models.FloatField("error SF total", default=-1)
    err_SF_lowdetail = models.FloatField("error SF lowdetail", default=-1)
    err_SF_highdetail = models.FloatField("error SF highdetail", default=-1)
    err_SF_rigid = models.FloatField("error SF rigid", default=-1)
    err_SF_nonrigid = models.FloatField("error SF nonrigid", default=-1)
    err_SF_matched = models.FloatField("error SF matched", default=-1)
    err_SF_unmatched = models.FloatField("error SF unmatched", default=-1)
    err_SF_notsky = models.FloatField("error SF notsky", default=-1)
    err_SF_sky = models.FloatField("error SF sky", default=-1)
    err_SF_s0_10 = models.FloatField("error SF s0-10", default=-1)
    err_SF_s10_40 = models.FloatField("error SF s10-40", default=-1)
    err_SF_s40 = models.FloatField("error SF s40+", default=-1)
    err_1px_SF_total = models.FloatField("error 1px SF total", default=-1)
    err_1px_SF_lowdetail = models.FloatField("error 1px SF lowdetail", default=-1)
    err_1px_SF_highdetail = models.FloatField("error 1px SF highdetail", default=-1)
    err_1px_SF_rigid = models.FloatField("error 1px SF rigid", default=-1)
    err_1px_SF_nonrigid = models.FloatField("error 1px SF nonrigid", default=-1)
    err_1px_SF_matched = models.FloatField("error 1px SF matched", default=-1)
    err_1px_SF_unmatched = models.FloatField("error 1px SF unmatched", default=-1)
    err_1px_SF_notsky = models.FloatField("error 1px SF notsky", default=-1)
    err_1px_SF_sky = models.FloatField("error 1px SF sky", default=-1)
    err_1px_SF_s0_10 = models.FloatField("error 1px SF s0-10", default=-1)
    err_1px_SF_s10_40 = models.FloatField("error 1px SF s10-40", default=-1)
    err_1px_SF_s40 = models.FloatField("error 1px SF s40+", default=-1)
    err_1px_D1_total = models.FloatField("error 1px D1 total", default=-1)
    err_1px_D1_lowdetail = models.FloatField("error 1px D1 lowdetail", default=-1)
    err_1px_D1_highdetail = models.FloatField("error 1px D1 highdetail", default=-1)
    err_1px_D1_notsky = models.FloatField("error 1px D1 notsky", default=-1)
    err_1px_D1_sky = models.FloatField("error 1px D1 sky", default=-1)
    err_1px_D1_s0_10 = models.FloatField("error 1px D1 s0-10", default=-1)
    err_1px_D1_s10_40 = models.FloatField("error 1px D1 s10-40", default=-1)
    err_1px_D1_s40 = models.FloatField("error 1px D1 s40+", default=-1)
    err_1px_D1_matched = models.FloatField("error 1px D1 matched", default=-1)
    err_1px_D1_unmatched = models.FloatField("error 1px D1 unmatched", default=-1)
    err_Abs_D1_total = models.FloatField("error Abs D1 total", default=-1)
    err_Abs_D1_lowdetail = models.FloatField("error Abs D1 lowdetail", default=-1)
    err_Abs_D1_highdetail = models.FloatField("error Abs D1 highdetail", default=-1)
    err_Abs_D1_notsky = models.FloatField("error Abs D1 notsky", default=-1)
    err_Abs_D1_sky = models.FloatField("error Abs D1 sky", default=-1)
    err_Abs_D1_s0_10 = models.FloatField("error Abs D1 s0-10", default=-1)
    err_Abs_D1_s10_40 = models.FloatField("error Abs D1 s10-40", default=-1)
    err_Abs_D1_s40 = models.FloatField("error Abs D1 s40+", default=-1)
    err_Abs_D1_matched = models.FloatField("error Abs D1 matched", default=-1)
    err_Abs_D1_unmatched = models.FloatField("error Abs D1 unmatched", default=-1)
    err_D1_total = models.FloatField("error D1 total", default=-1)
    err_D1_lowdetail = models.FloatField("error D1 lowdetail", default=-1)
    err_D1_highdetail = models.FloatField("error D1 highdetail", default=-1)
    err_D1_notsky = models.FloatField("error D1 notsky", default=-1)
    err_D1_sky = models.FloatField("error D1 sky", default=-1)
    err_D1_s0_10 = models.FloatField("error D1 s0-10", default=-1)
    err_D1_s10_40 = models.FloatField("error D1 s10-40", default=-1)
    err_D1_s40 = models.FloatField("error D1 s40+", default=-1)
    err_D1_matched = models.FloatField("error D1 matched", default=-1)
    err_D1_unmatched = models.FloatField("error D1 unmatched", default=-1)
    err_1px_D2_total = models.FloatField("error 1px D2 total", default=-1)
    err_1px_D2_lowdetail = models.FloatField("error 1px D2 lowdetail", default=-1)
    err_1px_D2_highdetail = models.FloatField("error 1px D2 highdetail", default=-1)
    err_1px_D2_notsky = models.FloatField("error 1px D2 notsky", default=-1)
    err_1px_D2_sky = models.FloatField("error 1px D2 sky", default=-1)
    err_1px_D2_s0_10 = models.FloatField("error 1px D2 s0-10", default=-1)
    err_1px_D2_s10_40 = models.FloatField("error 1px D2 s10-40", default=-1)
    err_1px_D2_s40 = models.FloatField("error 1px D2 s40+", default=-1)
    err_1px_D2_matched = models.FloatField("error 1px D2 matched", default=-1)
    err_1px_D2_unmatched = models.FloatField("error 1px D2 unmatched", default=-1)
    err_Abs_D2_total = models.FloatField("error Abs D2 total", default=-1)
    err_Abs_D2_lowdetail = models.FloatField("error Abs D2 lowdetail", default=-1)
    err_Abs_D2_highdetail = models.FloatField("error Abs D2 highdetail", default=-1)
    err_Abs_D2_notsky = models.FloatField("error Abs D2 notsky", default=-1)
    err_Abs_D2_sky = models.FloatField("error Abs D2 sky", default=-1)
    err_Abs_D2_s0_10 = models.FloatField("error Abs D2 s0-10", default=-1)
    err_Abs_D2_s10_40 = models.FloatField("error Abs D2 s10-40", default=-1)
    err_Abs_D2_s40 = models.FloatField("error Abs D2 s40+", default=-1)
    err_Abs_D2_matched = models.FloatField("error Abs D2 matched", default=-1)
    err_Abs_D2_unmatched = models.FloatField("error Abs D2 unmatched", default=-1)
    err_D2_total = models.FloatField("error D2 total", default=-1)
    err_D2_lowdetail = models.FloatField("error D2 lowdetail", default=-1)
    err_D2_highdetail = models.FloatField("error D2 highdetail", default=-1)
    err_D2_notsky = models.FloatField("error D2 notsky", default=-1)
    err_D2_sky = models.FloatField("error D2 sky", default=-1)
    err_D2_s0_10 = models.FloatField("error D2 s0-10", default=-1)
    err_D2_s10_40 = models.FloatField("error D2 s10-40", default=-1)
    err_D2_s40 = models.FloatField("error D2 s40+", default=-1)
    err_D2_matched = models.FloatField("error D2 matched", default=-1)
    err_D2_unmatched = models.FloatField("error D2 unmatched", default=-1)
    err_EPE_Fl_total = models.FloatField("error EPE Fl total", default=-1)
    err_EPE_Fl_lowdetail = models.FloatField("error EPE Fl lowdetail", default=-1)
    err_EPE_Fl_highdetail = models.FloatField("error EPE Fl highdetail", default=-1)
    err_EPE_Fl_rigid = models.FloatField("error EPE Fl rigid", default=-1)
    err_EPE_Fl_nonrigid = models.FloatField("error EPE Fl nonrigid", default=-1)
    err_EPE_Fl_matched = models.FloatField("error EPE Fl matched", default=-1)
    err_EPE_Fl_unmatched = models.FloatField("error EPE Fl unmatched", default=-1)
    err_EPE_Fl_notsky = models.FloatField("error EPE Fl notsky", default=-1)
    err_EPE_Fl_sky = models.FloatField("error EPE Fl sky", default=-1)
    err_EPE_Fl_s0_10 = models.FloatField("error EPE Fl s0-10", default=-1)
    err_EPE_Fl_s10_40 = models.FloatField("error EPE Fl s10-40", default=-1)
    err_EPE_Fl_s40 = models.FloatField("error EPE Fl s40+", default=-1)
    err_Fl_total = models.FloatField("error Fl total", default=-1)
    err_Fl_lowdetail = models.FloatField("error Fl lowdetail", default=-1)
    err_Fl_highdetail = models.FloatField("error Fl highdetail", default=-1)
    err_Fl_rigid = models.FloatField("error Fl rigid", default=-1)
    err_Fl_nonrigid = models.FloatField("error Fl nonrigid", default=-1)
    err_Fl_matched = models.FloatField("error Fl matched", default=-1)
    err_Fl_unmatched = models.FloatField("error Fl unmatched", default=-1)
    err_Fl_notsky = models.FloatField("error Fl notsky", default=-1)
    err_Fl_sky = models.FloatField("error Fl sky", default=-1)
    err_Fl_s0_10 = models.FloatField("error Fl s0-10", default=-1)
    err_Fl_s10_40 = models.FloatField("error Fl s10-40", default=-1)
    err_Fl_s40 = models.FloatField("error Fl s40+", default=-1)
    err_1px_Fl_total = models.FloatField("error 1px Fl total", default=-1)
    err_1px_Fl_lowdetail = models.FloatField("error 1px Fl lowdetail", default=-1)
    err_1px_Fl_highdetail = models.FloatField("error 1px Fl highdetail", default=-1)
    err_1px_Fl_rigid = models.FloatField("error 1px Fl rigid", default=-1)
    err_1px_Fl_nonrigid = models.FloatField("error 1px Fl nonrigid", default=-1)
    err_1px_Fl_matched = models.FloatField("error 1px Fl matched", default=-1)
    err_1px_Fl_unmatched = models.FloatField("error 1px Fl unmatched", default=-1)
    err_1px_Fl_notsky = models.FloatField("error 1px Fl notsky", default=-1)
    err_1px_Fl_sky = models.FloatField("error 1px Fl sky", default=-1)
    err_1px_Fl_s0_10 = models.FloatField("error 1px Fl s0-10", default=-1)
    err_1px_Fl_s10_40 = models.FloatField("error 1px Fl s10-40", default=-1)
    err_1px_Fl_s40 = models.FloatField("error 1px Fl s40+", default=-1)
    err_WAUC_Fl_total = models.FloatField("error WAUC Fl total", default=-1)
    err_WAUC_Fl_lowdetail = models.FloatField("error WAUC Fl lowdetail", default=-1)
    err_WAUC_Fl_highdetail = models.FloatField("error WAUC Fl highdetail", default=-1)
    err_WAUC_Fl_rigid = models.FloatField("error WAUC Fl rigid", default=-1)
    err_WAUC_Fl_nonrigid = models.FloatField("error WAUC Fl nonrigid", default=-1)
    err_WAUC_Fl_matched = models.FloatField("error WAUC Fl matched", default=-1)
    err_WAUC_Fl_unmatched = models.FloatField("error WAUC Fl unmatched", default=-1)
    err_WAUC_Fl_notsky = models.FloatField("error WAUC Fl notsky", default=-1)
    err_WAUC_Fl_sky = models.FloatField("error WAUC Fl sky", default=-1)
    err_WAUC_Fl_s0_10 = models.FloatField("error WAUC Fl s0-10", default=-1)
    err_WAUC_Fl_s10_40 = models.FloatField("error WAUC Fl s10-40", default=-1)
    err_WAUC_Fl_s40 = models.FloatField("error WAUC Fl s40+", default=-1)

    # Robust Evaluation Fields
    robust_1px_D1_total = models.FloatField("robust 1px D1 total", default=-1)
    robust_Abs_D1_total = models.FloatField("robust Abs D1 total", default=-1)
    robust_D1_total = models.FloatField("robust D1 total", default=-1)
    robust_EPE_Fl_total = models.FloatField("robust EPE Fl total", default=-1)
    robust_Fl_total = models.FloatField("robust Fl total", default=-1)
    robust_1px_Fl_total = models.FloatField("robust 1px Fl total", default=-1)
    robust_disp1_1px_total = models.FloatField("robust 1px D1 total (scene flow)", default=-1)
    robust_disp1_Abs_total = models.FloatField("robust Abs D1 total (scene flow)", default=-1)
    robust_disp1_D1_total = models.FloatField("robust D1 total (scene flow)", default=-1)
    robust_disp2_1px_total = models.FloatField("robust 1px D2 total (scene flow)", default=-1)
    robust_disp2_Abs_total = models.FloatField("robust Abs D2 total (scene flow)", default=-1)
    robust_disp2_D2_total = models.FloatField("robust D2 total (scene flow)", default=-1)
    robust_flow_EPE_total = models.FloatField("robust EPE Fl total (scene flow)", default=-1)
    robust_flow_Fl_total = models.FloatField("robust Fl total (scene flow)", default=-1)
    robust_flow_1px_total = models.FloatField("robust 1px Fl total (scene flow)", default=-1)

    def __str__(self):
        return self.name


class RobustCorruptionResult(models.Model):
    CORRUPTION_CHOICES = (
        ("brightness", "Brightness"),
        ("contrast", "Contrast"),
        ("saturate", "Saturate"),
        ("defocus_blur", "Defocus Blur"),
        ("gaussian_blur", "Gaussian Blur"),
        ("glass_blur", "Glass Blur"),
        ("motion_blur", "Motion Blur"),
        ("zoom_blur", "Zoom Blur"),
        ("gaussian_noise", "Gaussian Noise"),
        ("impulse_noise", "Impulse Noise"),
        ("speckle_noise", "Speckle Noise"),
        ("shot_noise", "Shot Noise"),
        ("pixelate", "Pixelate"),
        ("jpeg_compression", "JPEG Compression"),
        ("elastic_transform", "Elastic Transform"),
        ("fog", "Fog"),
        ("frost", "Frost"),
        ("rain", "Rain"),
        ("snow", "Snow"),
        ("spatter", "Spatter"),
    )
    
    result_entry = models.ForeignKey('ResultEntry', related_name='robust_corruption_results', on_delete=models.CASCADE)
    corruption_name = models.CharField(max_length=50, choices=CORRUPTION_CHOICES)
    
    # For disparity robust evaluation
    robust_1px_D1 = models.FloatField("robust 1px D1", default=-1)
    robust_Abs_D1 = models.FloatField("robust Abs D1", default=-1)
    robust_D1 = models.FloatField("robust D1", default=-1)
    
    # For optical flow robust evaluation
    robust_EPE_Fl = models.FloatField("robust EPE Fl", default=-1)
    robust_Fl = models.FloatField("robust Fl", default=-1)
    robust_1px_Fl = models.FloatField("robust 1px Fl", default=-1)

    # For scene flow robust evaluation
    # disp1
    robust_disp1_1px = models.FloatField("robust 1px D1 total (scene flow)", default=-1)
    robust_disp1_Abs = models.FloatField("robust Abs D1 total (scene flow)", default=-1)
    robust_disp1_D1 = models.FloatField("robust D1 total (scene flow)", default=-1)
    # disp2
    robust_disp2_1px = models.FloatField("robust 1px D2 total (scene flow)", default=-1)
    robust_disp2_Abs = models.FloatField("robust Abs D2 total (scene flow)", default=-1)
    robust_disp2_D2 = models.FloatField("robust D2 total (scene flow)", default=-1)
    # flow
    robust_flow_EPE = models.FloatField("robust EPE Fl total (scene flow)", default=-1)
    robust_flow_Fl = models.FloatField("robust Fl total (scene flow)", default=-1)
    robust_flow_1px = models.FloatField("robust 1px Fl total (scene flow)", default=-1)

    def __str__(self):
        return f"{self.result_entry.name} - {self.corruption_name}"
