from django import forms
from django.contrib.auth.models import User

from .models import Shipment, ShipmentDocument, UserProfile


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class RegisterForm(forms.Form):
    ROLE_CHOICES = [
        ('driver', 'Водитель'),
        ('company', 'Компания'),
    ]

    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        label='Роль',
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    company_name = forms.CharField(
        label='Название компании',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='Телефон',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Такой логин уже существует.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Такая почта уже зарегистрирована.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password1') != cleaned_data.get('password2'):
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned_data


class ShipmentForm(forms.ModelForm):
    origin_lat = forms.FloatField(widget=forms.HiddenInput(), required=False)
    origin_lng = forms.FloatField(widget=forms.HiddenInput(), required=False)
    destination_lat = forms.FloatField(widget=forms.HiddenInput(), required=False)
    destination_lng = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Shipment
        fields = [
            'title',
            'sender',
            'receiver',
            'driver',
            'origin_city',
            'destination_city',
            'route',
            'status',
            'weight',
            'price',
            'is_fragile',
            'fragile_level',
            'estimated_arrival',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'sender': forms.TextInput(attrs={'class': 'form-control'}),
            'receiver': forms.TextInput(attrs={'class': 'form-control'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'origin_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Магнитогорск'}),
            'destination_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Астана'}),
            'route': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_fragile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fragile_level': forms.Select(attrs={'class': 'form-select'}),
            'estimated_arrival': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = User.objects.filter(profile__role='driver').order_by('username')
        self.fields['driver'].required = False


class ShipmentDelayForm(forms.Form):
    delay_minutes = forms.IntegerField(
        label='Задержка в минутах',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    delay_reason = forms.CharField(
        label='Причина задержки',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class ShipmentDocumentForm(forms.ModelForm):
    class Meta:
        model = ShipmentDocument
        fields = ['document_type', 'title', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }