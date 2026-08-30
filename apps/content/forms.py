from django import forms
from django.utils import timezone

from .models import Content, Collection
from .utils import guess_content_type


INPUT_CLASS = 'field-input'


class ContentForm(forms.ModelForm):

    PUBLISH_CHOICES = [
        ('now', 'Publish immediately'),
        ('schedule', 'Schedule for later'),
    ]

    publish_when = forms.ChoiceField(
        choices=PUBLISH_CHOICES,
        widget=forms.RadioSelect,
        initial='now',
        required=False,
    )

    scheduled_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                'class': INPUT_CLASS,
                'type': 'datetime-local',
            }
        ),
    )

    class Meta:
        model = Content
        fields = [
            'title',
            'description',
            'media_file',
            'thumbnail',
            'collection',
            'minimum_tier',
        ]

        widgets = {
            'title': forms.TextInput(
                attrs={'class': INPUT_CLASS}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': INPUT_CLASS,
                    'rows': 3,
                }
            ),
            'collection': forms.Select(
                attrs={'class': INPUT_CLASS}
            ),
            'minimum_tier': forms.Select(
                attrs={'class': INPUT_CLASS}
            ),
        }

    def __init__(
        self,
        *args,
        creator=None,
        include_publish_fields=True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.creator = creator
        self.include_publish_fields = include_publish_fields

        if not include_publish_fields:
            del self.fields['publish_when']
            del self.fields['scheduled_at']

        self.fields['minimum_tier'].queryset = (
            creator.tiers.filter(is_active=True)
        )

        self.fields['minimum_tier'].required = False

        self.fields['collection'].queryset = (
            creator.collections.all()
        )

        self.fields['collection'].required = False

        # If the current content already belongs to a Collection,
        # the Collection controls its tier.
        if self.instance and self.instance.pk and self.instance.collection_id:
            self.fields['minimum_tier'].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        if (
            self.include_publish_fields
            and cleaned_data.get('publish_when') == 'schedule'
        ):
            scheduled_at = cleaned_data.get('scheduled_at')

            if not scheduled_at:
                self.add_error(
                    'scheduled_at',
                    'Pick a date and time to schedule this for.'
                )

            elif scheduled_at <= timezone.now():
                self.add_error(
                    'scheduled_at',
                    'Scheduled time must be in the future.'
                )

        collection = cleaned_data.get('collection')

        if collection:
            cleaned_data['minimum_tier'] = collection.minimum_tier

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.creator = self.creator

        media = self.cleaned_data.get('media_file')

        source_name = (
            media.name
            if media
            else (
                instance.media_file.name
                if instance.media_file
                else None
            )
        )

        instance.content_type = guess_content_type(source_name)

        # A Collection's tier always wins.
        if instance.collection_id:
            instance.minimum_tier = instance.collection.minimum_tier

        if self.include_publish_fields:
            instance.is_published = True

            if self.cleaned_data.get('publish_when') == 'schedule':
                instance.published_at = self.cleaned_data['scheduled_at']
            else:
                instance.published_at = timezone.now()

        if commit:
            instance.save()

        return instance


class CollectionForm(forms.ModelForm):

    class Meta:
        model = Collection

        fields = [
            'title',
            'description',
            'cover_image',
            'minimum_tier',
        ]

        widgets = {
            'title': forms.TextInput(
                attrs={'class': INPUT_CLASS}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': INPUT_CLASS,
                    'rows': 3,
                }
            ),
            'minimum_tier': forms.Select(
                attrs={'class': INPUT_CLASS}
            ),
        }

    def __init__(self, *args, creator=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['minimum_tier'].queryset = (
            creator.tiers.filter(is_active=True)
        )

        self.fields['minimum_tier'].required = False