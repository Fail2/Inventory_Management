from django import forms
from .models import Buyer


class BuyerForm(forms.ModelForm):
    password = forms.CharField(widget= forms.PasswordInput())
    confirm_password = forms.CharField(widget = forms.PasswordInput())
    class Meta:
        model = Buyer
        fields = ['full_name','address','email','username','password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password do not match!")  