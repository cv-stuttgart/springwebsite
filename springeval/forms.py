from django import forms
from .models import RESULTENTRY_NAME_MAX_LENGTH, ResultEntry
from django.core.exceptions import ValidationError



class UploadFileForm(forms.Form):
    name = forms.CharField(max_length=RESULTENTRY_NAME_MAX_LENGTH)
    method_type = forms.ChoiceField(choices=ResultEntry.METHOD_TYPE_CHOICES, widget=forms.RadioSelect)
    disp1file = forms.FileField(label="Submission file for disparity 1", required=False, help_text="disp1_submission.hdf5 file. Required for disparity or scene flow submissions.")
    disp2file = forms.FileField(label="Submission file for disparity 2", required=False, help_text="disp2_submission.hdf5 file. Required for scene flow submissions.")
    flowfile = forms.FileField(label="Submission file for optical flow", required=False, help_text="flow_submission.hdf5 file. Required for optical flow or scene flow submissions.")

    def clean(self):
        cleaned_data = super().clean()
        selection = ""
        if cleaned_data["method_type"] == "ST":
            required = [True, False, False]
            selection = "Stereo"
        if cleaned_data["method_type"] == "FL":
            required = [False, False, True]
            selection = "Optical Flow"
        if cleaned_data["method_type"] == "SF":
            selection = "Scene Flow"
            required = [True, True, True]
        for r, d, n in zip(required,[cleaned_data["disp1file"], cleaned_data["disp2file"], cleaned_data["flowfile"]], ["disparity 1", "disparity 2", "optical flow"]):
            if r and (d is None):
                raise ValidationError(f"You selected {selection} but did not provide a file for {n}!")
            if (not r) and (d is not None):
                raise ValidationError(f"You selected {selection} but provided a file for {n}!")
