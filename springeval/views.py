import glob
import logging
import os

from django.http import HttpResponseRedirect
from .models import ResultEntry
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from springeval.admin import UserCreationForm
from .forms import UploadFileForm, EditResultEntryForm
from django.utils import timezone
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from springeval.token import TokenGenerator
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Case, When, Value, IntegerField, F

logger = logging.getLogger(__name__)

UPLOAD_DIRECTORY = os.environ["SPRING_UPLOADDIR"]

class DetailView(UserPassesTestMixin, generic.DetailView):
    model = ResultEntry
    template_name = 'springeval/detail.html'

    def test_func(self):
        obj = self.get_object()
        if obj.visibility in ["PUBL", "ANON"]:
            return True
        else:
            if not self.request.user.is_authenticated:
                return False
            return self.request.user.pk == obj.creator.pk

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['range'] = [f"{i:02d}" for i in range(10)]
        return context


def stereo(request):
    valid_keys = [
        "err_1px_D1_total", "err_1px_D1_lowdetail", "err_1px_D1_highdetail", 
        "err_1px_D1_matched", "err_1px_D1_unmatched", "err_1px_D1_notsky", 
        "err_1px_D1_sky", "err_Abs_D1_total", "err_D1_total", 
        "err_1px_D1_s0_10", "err_1px_D1_s10_40", "err_1px_D1_s40",
        "robust_1px_D1_total", "robust_Abs_D1_total", "robust_D1_total"
    ]
    qs = ResultEntry.objects.exclude(method_type__exact="FL").exclude(visibility__exact="PRIV")
    # For stereo, default to accuracy if not robustness:
    entries_list, sortby, display = get_sorted_entries(request, qs, valid_keys, "err_1px_D1_total", "robust_1px_D1_total")
    context = {'entries_list': entries_list, 'sortby': sortby, 'display': display}
    return render(request, "springeval/stereo.html", context)


def opticalflow(request):
    valid_keys = [
        "err_1px_Fl_total", "err_1px_Fl_lowdetail", "err_1px_Fl_highdetail", 
        "err_1px_Fl_matched", "err_1px_Fl_unmatched", "err_1px_Fl_rigid", 
        "err_1px_Fl_nonrigid", "err_1px_Fl_notsky", "err_1px_Fl_sky", 
        "err_EPE_Fl_total", "err_Fl_total", "err_WAUC_Fl_total", 
        "err_1px_Fl_s0_10", "err_1px_Fl_s10_40", "err_1px_Fl_s40",
        "robust_EPE_Fl_total", "robust_Fl_total", "robust_1px_Fl_total"
    ]
    qs = ResultEntry.objects.exclude(method_type__exact="ST").exclude(visibility__exact="PRIV")
    entries_list, sortby, display = get_sorted_entries(request, qs, valid_keys, "err_1px_Fl_total", "robust_EPE_Fl_total")
    context = {
        'entries_list': entries_list,
        'sortby': sortby,
        'display': display
    }
    return render(request, "springeval/opticalflow.html", context)


def sceneflow(request):
    valid_keys = [
        "err_1px_SF_total", "err_1px_SF_lowdetail", "err_1px_SF_highdetail", 
        "err_1px_SF_matched", "err_1px_SF_unmatched", "err_1px_SF_rigid", 
        "err_1px_SF_nonrigid", "err_1px_SF_notsky", "err_1px_SF_sky", 
        "err_SF_total", "err_1px_D1_total", "err_1px_D2_total", "err_1px_Fl_total", 
        "err_1px_SF_s0_10", "err_1px_SF_s10_40", "err_1px_SF_s40",
        "robust_disp1_1px_total", "robust_disp1_Abs_total", "robust_disp1_D1_total",
        "robust_disp2_1px_total", "robust_disp2_Abs_total", "robust_disp2_D2_total",
        "robust_flow_EPE_total", "robust_flow_Fl_total", "robust_flow_1px_total"
    ]
    qs = ResultEntry.objects.filter(method_type__exact="SF").exclude(visibility__exact="PRIV")
    # For scene flow, default to accuracy if not robustness:
    entries_list, sortby, display = get_sorted_entries(request, qs, valid_keys, "err_1px_SF_total", "robust_disp1_1px_total")
    context = {'entries_list': entries_list, "sortby": sortby, "display": display}
    return render(request, "springeval/sceneflow.html", context)


def get_sorted_entries(request, qs, valid_keys, default_accuracy, default_robustness):
    """
    Returns a tuple of (sorted queryset, sortby, display) based on the request GET parameters.
    
    qs: initial queryset
    valid_keys: list of valid sort keys (e.g. for optical flow, stereo, etc.)
    default_accuracy: default sort key to use if display is not "robustness"
    default_robustness: default sort key to use if display is "robustness"
    """
    display = request.GET.get("display", "both")
    sortby = request.GET.get("s", "")
    if sortby not in valid_keys:
        if display == "robustness":
            sortby = default_robustness
        else:
            sortby = default_accuracy

    if sortby == "err_WAUC_Fl_total":
        sortby = "-err_WAUC_Fl_total"

    descending = sortby.startswith("-")
    sort_field = sortby[1:] if descending else sortby

    # sort key to push missing entries to the bottom
    qs = qs.annotate(
        sort_key=Case(
            When(**{sort_field: -1}, then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )
    )
    if descending:
        entries_list = qs.order_by('sort_key', F(sort_field).desc())
    else:
        entries_list = qs.order_by('sort_key', sort_field)

    return entries_list, sortby, display


@login_required
def userindex(request):
    entries_list = ResultEntry.objects.filter(creator__exact=request.user.pk).order_by("pub_date")
    context = {'entries_list': entries_list}
    return render(request, "springeval/userindex.html", context)


def can_user_upload(user):
    return user.can_upload()


def _upload_file_path(entry, suffix):
    return os.path.join(
        UPLOAD_DIRECTORY,
        f"upload__{entry.id}__{entry.imghash.hex}__{suffix}.hdf5",
    )


def _write_upload(request_files, field_name, entry, suffix):
    """Write an uploaded file to disk. Returns the path written."""
    f = request_files[field_name]
    path = _upload_file_path(entry, suffix)
    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return path


def _cleanup_upload_files(entry):
    """Remove any partial upload files left on disk for *entry*."""
    pattern = os.path.join(
        UPLOAD_DIRECTORY,
        f"upload__{entry.id}__{entry.imghash.hex}__*.hdf5",
    )
    for path in glob.glob(pattern):
        try:
            os.remove(path)
        except OSError:
            pass


def handle_results(form, request):
    name = form.cleaned_data["name"]
    method_type = form.cleaned_data["method_type"]
    creator = request.user
    evaluate_robustness = form.cleaned_data["evaluate_robustness"]
    entry = ResultEntry.objects.create(
        pub_date=timezone.now(),
        name=name,
        creator=creator,
        method_type=method_type,
        process_status="WAIT_UPL",
        evaluate_robustness=evaluate_robustness,
    )

    try:
        # Process standard submission files
        if method_type in ["ST", "SF"]:
            _write_upload(request.FILES, "disp1file", entry, "disp1")

        if method_type in ["FL", "SF"]:
            _write_upload(request.FILES, "flowfile", entry, "flow")

        if method_type == "SF":
            _write_upload(request.FILES, "disp2file", entry, "disp2")

        # Process robustness files if the user selected robustness evaluation
        if evaluate_robustness:
            if method_type in ["ST", "SF"] and request.FILES.get("robustness_disp1file"):
                _write_upload(request.FILES, "robustness_disp1file", entry, "robust_disp1")

            if method_type in ["FL", "SF"] and request.FILES.get("robustness_flowfile"):
                _write_upload(request.FILES, "robustness_flowfile", entry, "robust_flow")

            if method_type == "SF" and request.FILES.get("robustness_disp2file"):
                _write_upload(request.FILES, "robustness_disp2file", entry, "robust_disp2")

        # Mark the entry for later processing
        entry.process_status = "WAIT_PROC"
        entry.save()

    except OSError as exc:
        logger.error("Upload failed for entry %s: %s", entry.id, exc)
        _cleanup_upload_files(entry)
        entry.delete()
        raise

    return entry


@login_required
@user_passes_test(can_user_upload)
def submit(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                handle_results(form, request)
            except OSError:
                form.add_error(
                    None,
                    "Upload failed \u2014 the server may be low on disk space. "
                    "Please try again later or contact the administrators.",
                )
                return render(request, "springeval/submit.html", {'form': form})
            return HttpResponseRedirect(reverse_lazy('springeval:user'))
    else:
        form = UploadFileForm()
    return render(request, "springeval/submit.html", {'form': form})


class EditView(UserPassesTestMixin, generic.UpdateView):
    model = ResultEntry
    form_class = EditResultEntryForm
    template_name = "springeval/resultentry_form.html"

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_authenticated and (self.request.user == obj.creator)

    def get_success_url(self):
        return reverse_lazy('springeval:detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        # First, let Django save the model fields (name, visibility, etc.)
        response = super().form_valid(form)
        entry = self.object
        mt = entry.method_type
        files = self.request.FILES

        # Only proceed if user checked the toggle
        if form.cleaned_data["evaluate_robustness"]:
            try:
                if mt in ["ST", "SF"] and files.get("robustness_disp1file"):
                    _write_upload(files, "robustness_disp1file", entry, "robust_disp1")

                if mt in ["FL", "SF"] and files.get("robustness_flowfile"):
                    _write_upload(files, "robustness_flowfile", entry, "robust_flow")

                if mt == "SF" and files.get("robustness_disp2file"):
                    _write_upload(files, "robustness_disp2file", entry, "robust_disp2")

                # After adding robustness files, re-queue for processing
                entry.process_status = "WAIT_PROC"
                entry.save()

            except OSError as exc:
                logger.error("Robustness upload failed for entry %s: %s", entry.id, exc)
                form.add_error(
                    None,
                    "Upload failed \u2014 the server may be low on disk space. "
                    "Please try again later or contact the administrators.",
                )
                return self.form_invalid(form)

        return response


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # save form in the memory not in database
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            # to get the domain of the current site
            current_site = get_current_site(request)
            mail_subject = 'Please confirm your Spring benchmark account'
            message = render_to_string('registration/confirm_email.html', {
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': TokenGenerator().make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            return render(request, "registration/confirm_request.html")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {'form': form})


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and TokenGenerator().check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, "registration/confirm_successful.html")
    else:
        return HttpResponse('Activation link is invalid!')
