from django import forms
from django.contrib.auth.models import User

from .models import (
    Shipment,
    ShipmentDocument,
    SupportTicket,
    SupportMessage,
)


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class RegisterForm(forms.Form):
    ROLE_CHOICES = [
        ('company', 'Компания'),
        ('driver', 'Водитель'),
    ]

    username = forms.CharField(
        label='Логин',
        max_length=150,
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

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        username = cleaned_data.get('username')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают.')

        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')

        return cleaned_data


class ShipmentForm(forms.ModelForm):
    estimated_arrival = forms.DateTimeField(
        label='Планируемое прибытие',
        required=False,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )

    origin_lat = forms.FloatField(
        label='Широта отправления',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )
    origin_lng = forms.FloatField(
        label='Долгота отправления',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )
    destination_lat = forms.FloatField(
        label='Широта назначения',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )
    destination_lng = forms.FloatField(
        label='Долгота назначения',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )

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
            'origin_city': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_city': forms.TextInput(attrs={'class': 'form-control'}),
            'route': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_fragile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fragile_level': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'driver' in self.fields:
            self.fields['driver'].queryset = User.objects.filter(profile__role='driver')
            self.fields['driver'].required = False

        self.fields['origin_lat'].initial = getattr(self.instance, 'origin_lat', None)
        self.fields['origin_lng'].initial = getattr(self.instance, 'origin_lng', None)
        self.fields['destination_lat'].initial = getattr(self.instance, 'destination_lat', None)
        self.fields['destination_lng'].initial = getattr(self.instance, 'destination_lng', None)


class ShipmentDelayForm(forms.Form):
    delay_minutes = forms.IntegerField(
        label='Минут задержки',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    delay_reason = forms.CharField(
        label='Причина задержки',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class ShipmentDocumentForm(forms.ModelForm):
    class Meta:
        model = ShipmentDocument
        fields = ['document_type', 'title', 'file']
        labels = {
            'document_type': 'Тип документа',
            'title': 'Название',
            'file': 'Файл',
        }
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'priority']
        labels = {
            'subject': 'Тема обращения',
            'priority': 'Приоритет',
        }
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }


class SupportMessageForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ['message']
        labels = {
            'message': 'Сообщение',
        }
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }