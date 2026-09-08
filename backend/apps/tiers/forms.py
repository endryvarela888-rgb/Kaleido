from django import forms

from .models import Tier

INPUT_CLASS = 'field-input'
LEVEL_CHOICES = [(1, 'Level 1 (lowest)'), (2, 'Level 2'), (3, 'Level 3 (highest)')]


class TierForm(forms.ModelForm):
    level = forms.ChoiceField(choices=LEVEL_CHOICES, widget=forms.Select(attrs={'class': INPUT_CLASS}))

    class Meta:
        model = Tier
        fields = ['name', 'description', 'price', 'level']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01', 'min': '1'}),
        }

    def __init__(self, *args, creator=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.creator = creator

    def clean_level(self):
        level = int(self.cleaned_data['level'])
        conflict = self.creator.tiers.filter(level=level, is_active=True)
        if self.instance.pk:
            conflict = conflict.exclude(pk=self.instance.pk)
        if conflict.exists():
            raise forms.ValidationError(f'Level {level} is already used by another active tier.')
        return level