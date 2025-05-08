from django import forms
from .models import Buyer

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Password",
        required= False #Make password optional in Admin edit mode
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password",
        required= False #Make confirm password optional in Admin edit mode
    )

    class Meta:
        model = Buyer  # Default, but we will override dynamically!
        fields = ['full_name', 'address', 'email', 'username', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        model_class = kwargs.pop('model_class', None)
        super(UserForm, self).__init__(*args, **kwargs)
        if model_class:
            self._meta.model = model_class  # dynamically set model (Buyer/Supplier)
    

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data
