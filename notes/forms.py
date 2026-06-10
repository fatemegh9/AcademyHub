from django import forms
from .models import Note


class NoteUploadForm(forms.ModelForm):
    tags_input = forms.CharField(
    max_length=500, 
    required=False,
    widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'هر تگ را در یک خط بنویسید:\nریاضی\nفیزیک\nبرنامه نویسی'}),
    help_text="هر تگ را در یک خط جداگانه وارد کنید"
)
    class Meta:
        model = Note
        fields = ['title', 'description','lesson_name', 'professor_name', 'file', 'tags_input' ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }