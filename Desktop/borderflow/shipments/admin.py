from django.contrib import admin
from .models import (
    Shipment,
    ShipmentContract,
    ShipmentDocument,
    UserProfile,
    ShipmentEvent,
    Notification,
    SupportTicket,
    SupportMessage,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'company_name', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'company_name')


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'company',
        'driver',
        'sender',
        'receiver',
        'origin_city',
        'destination_city',
        'status',
        'is_fragile',
        'is_delayed',
        'progress_percent',
        'created_at'
    )
    search_fields = ('title', 'sender', 'receiver', 'origin_city', 'destination_city', 'route')
    list_filter = ('status', 'is_fragile', 'is_delayed', 'fragile_level')


@admin.register(ShipmentContract)
class ShipmentContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipment', 'contract_id', 'status', 'signed_by_sender', 'signed_by_receiver', 'created_at')


@admin.register(ShipmentDocument)
class ShipmentDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipment', 'document_type', 'title', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'shipment__title')


@admin.register(ShipmentEvent)
class ShipmentEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipment', 'title', 'created_at')
    search_fields = ('shipment__title', 'title')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'user', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('subject', 'user__username')


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'author', 'is_admin_reply', 'created_at')
    list_filter = ('is_admin_reply', 'created_at')
    search_fields = ('ticket__subject', 'author__username')