from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import User

INPUT_CLASS = 'field-input'


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        min_length=8,
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
    )

    class Meta:
        model = User
        fields = ['email', 'display_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'display_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Passwords do not match.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False  # stays inactive until the email link is clicked
        if commit:
            user.save()
        return user


class ResendActivationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'autofocus': True}),
    )


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'autofocus': True}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
    )

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['display_name', 'avatar', 'avatar_position_x', 'avatar_position_y', 'bio']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'bio': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
            # Plain FileInput (not Django's default ClearableFileInput) skips
            # the "Currently: / Clear / Change:" boilerplate — we build our
            # own click-to-change UI instead.
            'avatar': forms.FileInput(attrs={'id': 'avatarFileInput', 'hidden': True}),
            'avatar_position_x': forms.HiddenInput(attrs={'id': 'avatarPosX'}),
            'avatar_position_y': forms.HiddenInput(attrs={'id': 'avatarPosY'}),
        }

class StyledPasswordChangeForm(PasswordChangeForm):
    """Same validation as Django's built-in form — just restyled to match our fields."""

    old_password = forms.CharField(
        label='Current password',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'autofocus': True}),
    )
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
    )
