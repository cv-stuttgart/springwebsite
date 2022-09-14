from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import ResultEntry, SpringUser



class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password*', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation*', widget=forms.PasswordInput)

    class Meta:
        model = SpringUser
        fields = ('email', 'university', 'website', 'description')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = SpringUser
        fields = ('email', 'password', 'is_active', 'is_admin')


class SpringUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'maildomain', 'university', 'is_verified', 'is_admin')
    list_filter = ('university', 'is_verified', 'is_admin')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (None, {'fields': ('university', 'website', 'description')}),
        (None, {'fields': ('is_verified',)}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'university', 'website'),
        }),
    )
    search_fields = ('email','university')
    ordering = ('email',)
    filter_horizontal = ()



class ResultEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'pub_date', 'visibility', 'method_type', 'process_status']
    ordering = ('pub_date',)



admin.site.register(SpringUser, SpringUserAdmin)
admin.site.register(ResultEntry, ResultEntryAdmin)

admin.site.unregister(Group)