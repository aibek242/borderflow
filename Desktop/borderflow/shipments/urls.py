from django.urls import path
from .views import (
    landing,
    login_view,
    register_view,
    logout_view,
    home,
    driver_panel,
    create_shipment,
    edit_shipment,
    delete_shipment,
    sign_contract,
    contract_webhook,
    api_shipments,
    api_shipment_detail,
    shipment_documents,
    upload_document,
    delete_document,
    download_document,
    shipment_map,
    start_shipment,
    delay_shipment,
    complete_shipment,
    mark_notification_read,
    about,
    support_list,
    support_create,
    support_detail,
    admin_support_list,
    close_ticket,
)

urlpatterns = [
    path('', landing, name='landing'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    path('about/', about, name='about'),

    path('home/', home, name='home'),
    path('driver/', driver_panel, name='driver_panel'),

    path('create/', create_shipment, name='create_shipment'),
    path('edit/<int:pk>/', edit_shipment, name='edit_shipment'),
    path('delete/<int:pk>/', delete_shipment, name='delete_shipment'),

    path('shipment/<int:pk>/start/', start_shipment, name='start_shipment'),
    path('shipment/<int:pk>/delay/', delay_shipment, name='delay_shipment'),
    path('shipment/<int:pk>/complete/', complete_shipment, name='complete_shipment'),

    path('contract/<int:shipment_id>/', sign_contract, name='sign_contract'),
    path('webhook/contract/', contract_webhook, name='contract_webhook'),

    path('documents/<int:pk>/', shipment_documents, name='shipment_documents'),
    path('documents/<int:pk>/upload/', upload_document, name='upload_document'),
    path('documents/<int:shipment_pk>/download/<int:doc_pk>/', download_document, name='download_document'),
    path('documents/delete/<int:pk>/', delete_document, name='delete_document'),

    path('map/<int:pk>/', shipment_map, name='shipment_map'),

    path('notifications/<int:pk>/read/', mark_notification_read, name='mark_notification_read'),

    path('support/', support_list, name='support_list'),
    path('support/create/', support_create, name='support_create'),
    path('support/<int:pk>/', support_detail, name='support_detail'),
    path('support/admin/', admin_support_list, name='admin_support_list'),
    path('support/<int:pk>/close/', close_ticket, name='close_ticket'),

    path('api/shipments/', api_shipments, name='api_shipments'),
    path('api/shipments/<int:pk>/', api_shipment_detail, name='api_shipment_detail'),
]