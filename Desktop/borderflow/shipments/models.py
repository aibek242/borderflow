from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('company', 'Компания'),
        ('driver', 'Водитель'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='company')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} - {self.role}'


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('docs', 'Документы'),
        ('ready', 'Готов к отправке'),
        ('in_transit', 'В пути'),
        ('delayed', 'Задерживается'),
        ('border', 'На границе'),
        ('done', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]

    FRAGILE_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]

    title = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    receiver = models.CharField(max_length=255)

    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_shipments')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_shipments')

    origin_city = models.CharField(max_length=255, blank=True, null=True)
    destination_city = models.CharField(max_length=255, blank=True, null=True)

    origin_lat = models.FloatField(blank=True, null=True)
    origin_lng = models.FloatField(blank=True, null=True)
    destination_lat = models.FloatField(blank=True, null=True)
    destination_lng = models.FloatField(blank=True, null=True)

    route = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')

    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    is_fragile = models.BooleanField(default=False)
    fragile_level = models.CharField(max_length=20, choices=FRAGILE_CHOICES, default='low')

    is_delayed = models.BooleanField(default=False)
    delay_reason = models.TextField(blank=True, null=True)
    delay_minutes = models.PositiveIntegerField(default=0)

    progress_percent = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(blank=True, null=True)
    estimated_arrival = models.DateTimeField(blank=True, null=True)
    actual_arrival = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ShipmentContract(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('signed', 'Подписан'),
        ('cancelled', 'Отменён'),
    ]

    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name='contract')
    contract_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    signed_by_sender = models.BooleanField(default=False)
    signed_by_receiver = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Контракт {self.contract_id}'


class ShipmentDocument(models.Model):
    DOCUMENT_TYPES = [
        ('cmr', 'CMR'),
        ('invoice', 'Инвойс'),
        ('packing_list', 'Упаковочный лист'),
        ('certificate', 'Сертификат'),
        ('customs', 'Таможенный документ'),
        ('passport', 'Паспорт водителя'),
        ('vehicle_passport', 'Техпаспорт'),
        ('insurance', 'Страховка'),
        ('other', 'Другое'),
    ]

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='other')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='shipment_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} - {self.shipment.title}'


class ShipmentEvent(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.shipment.title} - {self.title}'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.title}'


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('in_progress', 'В работе'),
        ('closed', 'Закрыт'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} ({self.user.username})'


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin_reply = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username}: {self.message[:30]}'