from django import forms
from .models import Buyer


class BuyerForm(forms.ModelForm):
    password = forms.CharField(widget= forms.PasswordInput())
    confirm_passsword = forms.CharField(widget = forms.PasswordInput())
    class Meta:
        model = Buyer
        fields = ['full_name','address','email','username','password']