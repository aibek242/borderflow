from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('driver', 'Водитель'),
        ('company', 'Компания'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='company')
    company_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'


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

    FRAGILE_LEVELS = [
        ('low', 'Низкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая'),
    ]

    title = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    receiver = models.CharField(max_length=255)

    company = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='company_shipments',
        verbose_name='Компания'
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver_shipments',
        verbose_name='Водитель'
    )

    origin_city = models.CharField(max_length=255, blank=True, verbose_name='Город отправления')
    destination_city = models.CharField(max_length=255, blank=True, verbose_name='Город назначения')

    origin_lat = models.FloatField(null=True, blank=True)
    origin_lng = models.FloatField(null=True, blank=True)
    destination_lat = models.FloatField(null=True, blank=True)
    destination_lng = models.FloatField(null=True, blank=True)

    route = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='created')
    weight = models.FloatField(default=0)
    price = models.FloatField(default=0)

    is_fragile = models.BooleanField(default=False, verbose_name='Хрупкий груз')
    fragile_level = models.CharField(
        max_length=20,
        choices=FRAGILE_LEVELS,
        default='low',
        verbose_name='Уровень хрупкости'
    )

    is_delayed = models.BooleanField(default=False, verbose_name='Есть задержка')
    delay_reason = models.CharField(max_length=255, blank=True, verbose_name='Причина задержки')
    delay_minutes = models.PositiveIntegerField(default=0, verbose_name='Задержка в минутах')

    started_at = models.DateTimeField(null=True, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True, verbose_name='Ожидаемое прибытие')
    actual_arrival = models.DateTimeField(null=True, blank=True, verbose_name='Фактическое прибытие')

    progress_percent = models.PositiveIntegerField(default=0, verbose_name='Прогресс маршрута')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Отправка'
        verbose_name_plural = 'Отправки'

    def __str__(self):
        return self.title

    @property
    def last_location(self):
        return self.locations.order_by('-recorded_at').first()


class ShipmentContract(models.Model):
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE)
    contract_id = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='draft')
    signed_by_sender = models.BooleanField(default=False)
    signed_by_receiver = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Contract for {self.shipment.title}'


class ShipmentLocation(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f'{self.shipment.title} ({self.latitude}, {self.longitude})'


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
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.shipment.title} - {self.title}'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title