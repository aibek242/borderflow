from django.contrib import admin
from django.utils.html import format_html

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
    search_fields = ('user__username', 'user__email', 'company_name', 'phone')
    list_per_page = 25


class ShipmentDocumentInline(admin.TabularInline):
    model = ShipmentDocument
    extra = 0
    readonly_fields = ('uploaded_at',)
    fields = ('document_type', 'title', 'file', 'uploaded_at')


class ShipmentEventInline(admin.TabularInline):
    model = ShipmentEvent
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('title', 'message', 'created_at')


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'company',
        'driver',
        'route_display',
        'status_badge',
        'fragile_badge',
        'delay_badge',
        'progress_percent',
        'created_at',
    )
    list_filter = (
        'status',
        'is_fragile',
        'is_delayed',
        'fragile_level',
        'created_at',
    )
    search_fields = (
        'title',
        'sender',
        'receiver',
        'origin_city',
        'destination_city',
        'route',
        'company__username',
        'driver__username',
    )
    readonly_fields = ('created_at',)
    autocomplete_fields = ('company', 'driver')
    list_per_page = 20
    inlines = [ShipmentDocumentInline, ShipmentEventInline]

    fieldsets = (
        ('Основное', {
            'fields': (
                'title', 'sender', 'receiver',
                'company', 'driver',
            )
        }),
        ('Маршрут', {
            'fields': (
                'origin_city', 'destination_city', 'route',
                ('origin_lat', 'origin_lng'),
                ('destination_lat', 'destination_lng'),
            )
        }),
        ('Статус и груз', {
            'fields': (
                'status',
                ('weight', 'price'),
                'progress_percent',
                'estimated_arrival',
                'actual_arrival',
            )
        }),
        ('Особые условия', {
            'fields': (
                'is_fragile',
                'fragile_level',
                'is_delayed',
                'delay_reason',
                'delay_minutes',
            )
        }),
        ('Служебное', {
            'fields': ('created_at',),
        }),
    )

    @admin.display(description='Маршрут')
    def route_display(self, obj):
        return f'{obj.origin_city or "—"} → {obj.destination_city or "—"}'

    @admin.display(description='Статус')
    def status_badge(self, obj):
        colors = {
            'created': '#64748b',
            'docs': '#0ea5e9',
            'ready': '#f59e0b',
            'in_transit': '#22c55e',
            'delayed': '#ef4444',
            'border': '#8b5cf6',
            'done': '#16a34a',
            'cancelled': '#991b1b',
        }
        color = colors.get(obj.status, '#334155')
        label = obj.get_status_display()
        return format_html(
            '<span style="background:{};color:white;padding:4px 10px;border-radius:999px;font-weight:600;">{}</span>',
            color,
            label,
        )

    @admin.display(description='Хрупкий')
    def fragile_badge(self, obj):
        if not obj.is_fragile:
            return '—'
        return format_html(
            '<span style="background:#facc15;color:#111;padding:4px 10px;border-radius:999px;font-weight:600;">{}</span>',
            obj.get_fragile_level_display()
        )

    @admin.display(description='Задержка')
    def delay_badge(self, obj):
        if not obj.is_delayed:
            return '—'
        return format_html(
            '<span style="background:#ef4444;color:white;padding:4px 10px;border-radius:999px;font-weight:600;">{} мин</span>',
            obj.delay_minutes
        )


@admin.register(ShipmentContract)
class ShipmentContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipment', 'contract_id', 'status', 'signed_by_sender', 'signed_by_receiver', 'created_at')
    list_filter = ('status', 'signed_by_sender', 'signed_by_receiver', 'created_at')
    search_fields = ('contract_id', 'shipment__title')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('shipment',)
    list_per_page = 25


@admin.register(ShipmentDocument)
class ShipmentDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipment', 'document_type', 'title', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'shipment__title')
    readonly_fields = ('uploaded_at',)
    autocomplete_fields = ('shipment',)
    list_per_page = 25


@admin.register(ShipmentEvent)
class ShipmentEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipment', 'title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('shipment__title', 'title', 'message')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('shipment',)
    list_per_page = 25


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user',)
    list_per_page = 25


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ('author', 'created_at', 'is_admin_reply')
    fields = ('author', 'message', 'is_admin_reply', 'created_at')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'user', 'status_badge', 'priority_badge', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('subject', 'user__username')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user',)
    inlines = [SupportMessageInline]
    list_per_page = 25

    @admin.display(description='Статус')
    def status_badge(self, obj):
        colors = {
            'open': '#ef4444',
            'in_progress': '#f59e0b',
            'closed': '#16a34a',
        }
        return format_html(
            '<span style="background:{};color:white;padding:4px 10px;border-radius:999px;font-weight:600;">{}</span>',
            colors.get(obj.status, '#334155'),
            obj.get_status_display()
        )

    @admin.display(description='Приоритет')
    def priority_badge(self, obj):
        colors = {
            'low': '#64748b',
            'medium': '#0ea5e9',
            'high': '#dc2626',
        }
        return format_html(
            '<span style="background:{};color:white;padding:4px 10px;border-radius:999px;font-weight:600;">{}</span>',
            colors.get(obj.priority, '#334155'),
            obj.get_priority_display()
        )


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'author', 'short_message', 'is_admin_reply', 'created_at')
    list_filter = ('is_admin_reply', 'created_at')
    search_fields = ('ticket__subject', 'author__username', 'message')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('ticket', 'author')
    list_per_page = 25

    @admin.display(description='Сообщение')
    def short_message(self, obj):
        return obj.message[:60] + ('...' if len(obj.message) > 60 else '')