from django import forms
from .models import Buyer,Supplier,Product,Category,Season,Order

#using model method (Model Form) for buyer/supplier form
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

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'season', 'price', 'quantity', 'picture', 'supplier']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'season': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Make optional fields not required in the form
        self.fields['category'].required = False
        self.fields['season'].required = False
        self.fields['picture'].required = False
        self.fields['supplier'].required = False    
        
    def clean_price(self):
         price = self.cleaned_data.get('price')
         if price is not None and price < 0:
           raise forms.ValidationError("Price cannot be negative.")
         return price

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class SeasonForm(forms.ModelForm):
    class Meta:
        model = Season
        fields = ['name']    


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

#Order form
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product', 'quantity', 'delivery_address']

        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity
    
    def clean_delivery_address(self):
        address = self.cleaned_data.get('delivery_address')
        if not address.strip():
            raise forms.ValidationError("Delivery address cannot be empty.")
        return address
