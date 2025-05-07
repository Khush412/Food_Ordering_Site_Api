from django import forms
from .models import Rider
from django.contrib.auth.models import User
from .models import ContactMessage

class RiderRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, max_length=128)

    class Meta:
        model = Rider
        fields = ['name', 'email', 'aadhaar_card', 'driving_license', 'password']

    def save(self, commit=True):
        user = User.objects.create_user(username=self.cleaned_data['email'], password=self.cleaned_data['password'])
        rider = super().save(commit=False)
        rider.user = user
        if commit:
            rider.save()
        return rider

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'placeholder': 'Your Message', 'rows': 4}),
        }
