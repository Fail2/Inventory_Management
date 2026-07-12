from django import forms
from .models import Buyer,Supplier,Product,Category,Season

#buyer passwordless login/registration
class EmailOTPRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com', 'autofocus': True}),
        label="Email",
    )

class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit code', 'autofocus': True, 'inputmode': 'numeric'}),
        label="Verification Code",
    )

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isdigit():
            raise forms.ValidationError("Enter the 6-digit code we emailed you.")
        return code

#shown to a brand-new buyer/supplier right after their email is verified
class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ['full_name', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'autofocus': True}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SupplierProfileForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['full_name', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'autofocus': True}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

#admin forms for managing buyer/supplier records directly (no password - everyone logs in via email OTP)
class BuyerAdminForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ['full_name', 'address', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class SupplierAdminForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['full_name', 'address', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'season', 'price', 'quantity', 'picture']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'season': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)

        self.fields['category'].empty_label = 'None'
        self.fields['season'].empty_label = 'None'
        # Make optional fields not required in the form
        self.fields['category'].required = False
        self.fields['season'].required = False
        self.fields['picture'].required = False
        
    def clean_price(self):
         price = self.cleaned_data.get('price')
         if price is not None and price < 0:
           raise forms.ValidationError("Price cannot be negative.")
         return price

#using function method(Regular Form) for category/season form
#Form Type: This is a regular form, not a ModelForm. It’s used for scenarios where you want to create or handle data that doesn't directly map to a Django model.
class DynamicGroupForm(forms.Form):
    name = forms.CharField(max_length=100, label='Name')

    def __init__(self, *args, **kwargs):
        self.group_by = kwargs.pop('group_by', None)
        super().__init__(*args, **kwargs)

    def save(self):
        if self.group_by == 'category':
            return Category.objects.create(name=self.cleaned_data['name'])
        elif self.group_by == 'season':
            return Season.objects.create(name=self.cleaned_data['name'])
        else:
            raise ValueError('Invalid group type')
