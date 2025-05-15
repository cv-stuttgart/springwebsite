from django import forms
from .models import RESULTENTRY_NAME_MAX_LENGTH, ResultEntry
from django.core.exceptions import ValidationError


class UploadFileForm(forms.Form):
    name = forms.CharField(
        max_length=RESULTENTRY_NAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={'id': 'id_name'})
    )
    method_type = forms.ChoiceField(
        choices=ResultEntry.METHOD_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'id': 'id_method_type'})
    )

    # Standard submission files
    disp1file = forms.FileField(
        label="Submission file for disparity 1",
        required=False,
        help_text="disp1_submission.hdf5 file. Required for disparity or scene flow submissions.",
        widget=forms.ClearableFileInput(attrs={'id': 'id_disp1file'})
    )
    disp2file = forms.FileField(
        label="Submission file for disparity 2",
        required=False,
        help_text="disp2_submission.hdf5 file. Required for scene flow submissions.",
        widget=forms.ClearableFileInput(attrs={'id': 'id_disp2file'})
    )
    flowfile = forms.FileField(
        label="Submission file for optical flow",
        required=False,
        help_text="flow_submission.hdf5 file. Required for optical flow or scene flow submissions.",
        widget=forms.ClearableFileInput(attrs={'id': 'id_flowfile'})
    )

    # Robustness evaluation toggle
    evaluate_robustness = forms.BooleanField(
        label="Evaluate robustness?",
        required=False,
        help_text="Check this box if you want to evaluate the robustness of your method.",
        widget=forms.CheckboxInput(attrs={'id': 'id_evaluate_robustness'})
    )

    # Additional robustness files
    robustness_disp1file = forms.FileField(
        label="Robustness file for disparity 1",
        required=False,
        help_text="disp1_robustness.hdf5 file. Required for robustness evaluation if disparity 1 is needed.",
        widget=forms.ClearableFileInput(attrs={'id': 'id_robustness_disp1file'})
    )
    robustness_disp2file = forms.FileField(
        label="Robustness file for disparity 2",
        required=False,
        help_text="disp2_robustness.hdf5 file. Required for robustness evaluation if disparity 2 is needed.",
        widget=forms.ClearableFileInput(attrs={'id': 'id_robustness_disp2file'})
    )
    robustness_flowfile = forms.FileField(
        label="Robustness file for optical flow",
        required=False,
        help_text="flow_robustness.hdf5 file. Required for robustness evaluation if optical flow is needed.",
        widget=forms.ClearableFileInput(attrs={'id': 'id_robustness_flowfile'})
    )

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

        for r, d, n in zip(required, [cleaned_data["disp1file"], cleaned_data["disp2file"], cleaned_data["flowfile"]], ["disparity 1", "disparity 2", "optical flow"]):
            if r and (d is None):
                raise ValidationError(f"You selected {selection} but did not provide a file for {n}!")
            if (not r) and (d is not None):
                raise ValidationError(f"You selected {selection} but provided a file for {n}!")

        if cleaned_data.get("evaluate_robustness"):
            for r, d, n in zip(
                required,
                [cleaned_data.get("robustness_disp1file"), cleaned_data.get("robustness_disp2file"), cleaned_data.get("robustness_flowfile")],
                ["robustness disparity 1", "robustness disparity 2", "robustness optical flow"]
            ):
                if r and d is None:
                    raise ValidationError(f"You selected robustness evaluation but did not provide a file for {n}!")
                if not r and d is not None:
                    raise ValidationError(f"You selected robustness evaluation but provided a file for {n} when it is not required!")


class EditResultEntryForm(forms.ModelForm):
    # --- Robustness toggle + file fields ---
    evaluate_robustness = forms.BooleanField(
        label="Evaluate robustness?",
        required=False,
        help_text="Check this box to upload robustness files.",
        widget=forms.CheckboxInput(attrs={'id': 'id_evaluate_robustness'})
    )
    robustness_disp1file = forms.FileField(
        label="Robustness file for disparity 1",
        required=False,
        widget=forms.ClearableFileInput(attrs={'id': 'id_robustness_disp1file'})
    )
    robustness_disp2file = forms.FileField(
        label="Robustness file for disparity 2",
        required=False,
        widget=forms.ClearableFileInput(attrs={'id': 'id_robustness_disp2file'})
    )
    robustness_flowfile = forms.FileField(
        label="Robustness file for optical flow",
        required=False,
        widget=forms.ClearableFileInput(attrs={'id': 'id_robustness_flowfile'})
    )

    class Meta:
        model = ResultEntry
        fields = [
            "name",
            "visibility",
            "citation",
            "code_url",
            "evaluate_robustness",
            "robustness_disp1file",
            "robustness_disp2file",
            "robustness_flowfile",
        ]

    def clean(self):
        cleaned = super().clean()
        eval_rob = cleaned.get("evaluate_robustness")
        mt = self.instance.method_type  # ST, FL, or SF

        # determine which robustness files are required
        if mt == "ST":
            required = [True, False, False]
        elif mt == "FL":
            required = [False, False, True]
        else:  # SF
            required = [True, True, True]

        fields = [
            ("robustness_disp1file", "disparity 1"),
            ("robustness_disp2file", "disparity 2"),
            ("robustness_flowfile",  "optical flow"),
        ]

        # if robustness toggled, enforce requirements; if not, forbid any upload
        for (field_name, label), req in zip(fields, required):
            uploaded = cleaned.get(field_name)
            if eval_rob:
                if req and not uploaded:
                    self.add_error(field_name,
                        f"Required for {self.instance.get_method_type_display()} robustness.")
                if not req and uploaded:
                    self.add_error(field_name,
                        f"Not required for {self.instance.get_method_type_display()}.")
            else:
                if uploaded:
                    # attach this error to the toggle box
                    self.add_error("evaluate_robustness",
                        f"You uploaded a {label} file but did not enable robustness evaluation.")
        return cleaned
