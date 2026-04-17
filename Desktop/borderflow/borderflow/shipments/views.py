import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import (
    ShipmentForm,
    ShipmentDocumentForm,
    LoginForm,
    RegisterForm,
    ShipmentDelayForm,
    SupportTicketForm,
    SupportMessageForm,
)
from .models import (
    Shipment,
    ShipmentContract,
    ShipmentDocument,
    ShipmentEvent,
    Notification,
    UserProfile,
    SupportTicket,
    SupportMessage,
)


def create_contract(shipment):
    return f"test_contract_{shipment.id}"


def create_notification(user, title, message=''):
    try:
        Notification.objects.create(user=user, title=title, message=message)
    except Exception:
        pass


def create_shipment_event(shipment, title, message=''):
    try:
        ShipmentEvent.objects.create(shipment=shipment, title=title, message=message)
    except Exception:
        pass


def ensure_user_profile(user):
    if not user or not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "company"}
    )
    if not profile.role:
        profile.role = "company"
        profile.save()
    return profile


def send_login_email(request, user):
    if not user.email:
        return

    subject = 'Вход в BorderFlow'
    message = (
        f'Здравствуйте, {user.username}!\n\n'
        f'В ваш аккаунт BorderFlow выполнен вход.\n'
        f'Время: {timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")}\n'
        f'IP: {request.META.get("REMOTE_ADDR", "неизвестно")}\n'
    )

    try:
        send_mail(subject, message, None, [user.email], fail_silently=True)
    except Exception:
        pass


def shipment_to_dict(shipment):
    return {
        'id': shipment.id,
        'title': shipment.title,
        'sender': shipment.sender,
        'receiver': shipment.receiver,
        'company': shipment.company.username if shipment.company else '',
        'driver': shipment.driver.username if shipment.driver else '',
        'origin_city': shipment.origin_city,
        'destination_city': shipment.destination_city,
        'origin_lat': shipment.origin_lat,
        'origin_lng': shipment.origin_lng,
        'destination_lat': shipment.destination_lat,
        'destination_lng': shipment.destination_lng,
        'route': shipment.route,
        'status': shipment.status,
        'weight': shipment.weight,
        'price': shipment.price,
        'is_fragile': shipment.is_fragile,
        'fragile_level': shipment.fragile_level,
        'is_delayed': shipment.is_delayed,
        'delay_reason': shipment.delay_reason,
        'delay_minutes': shipment.delay_minutes,
        'progress_percent': shipment.progress_percent,
        'estimated_arrival': shipment.estimated_arrival.isoformat() if shipment.estimated_arrival else None,
        'actual_arrival': shipment.actual_arrival.isoformat() if shipment.actual_arrival else None,
        'created_at': shipment.created_at.isoformat(),
    }


def user_role(user):
    profile = ensure_user_profile(user)
    if profile:
        return profile.role
    return None


def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)

        if user:
            ensure_user_profile(user)
            login(request, user)
            create_notification(user, 'Успешный вход', 'Вы успешно авторизовались в системе BorderFlow.')
            send_login_email(request, user)
            messages.success(request, 'Вход выполнен.')
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль.')

    return render(request, 'shipments/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
        )

        profile = ensure_user_profile(user)
        profile.role = form.cleaned_data['role']
        profile.company_name = form.cleaned_data['company_name']
        profile.phone = form.cleaned_data['phone']
        profile.save()

        create_notification(user, 'Аккаунт создан', 'Ваш аккаунт BorderFlow успешно зарегистрирован.')
        messages.success(request, 'Регистрация завершена. Теперь войдите в систему.')
        return redirect('login')

    return render(request, 'shipments/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы вышли из аккаунта.')
    return redirect('login')


@login_required
def home(request):
    ensure_user_profile(request.user)

    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    fragile = request.GET.get('fragile', '').strip()
    delayed = request.GET.get('delayed', '').strip()

    shipments = Shipment.objects.select_related('company', 'driver').all()
    role = user_role(request.user)

    if role == 'driver':
        shipments = shipments.filter(driver=request.user)
    elif role == 'company':
        shipments = shipments.filter(company=request.user)

    if query:
        shipments = shipments.filter(
            Q(title__icontains=query) |
            Q(sender__icontains=query) |
            Q(receiver__icontains=query) |
            Q(origin_city__icontains=query) |
            Q(destination_city__icontains=query) |
            Q(route__icontains=query)
        )

    if status:
        shipments = shipments.filter(status=status)

    if fragile == '1':
        shipments = shipments.filter(is_fragile=True)

    if delayed == '1':
        shipments = shipments.filter(is_delayed=True)

    try:
        notifications = request.user.notifications.filter(is_read=False)[:10]
    except Exception:
        notifications = []

    return render(request, 'shipments/index.html', {
        'shipments': shipments,
        'query': query,
        'status_filter': status,
        'statuses': Shipment.STATUS_CHOICES,
        'fragile_filter': fragile,
        'delayed_filter': delayed,
        'role': role,
        'notifications': notifications,
    })


@login_required
def driver_panel(request):
    ensure_user_profile(request.user)

    if user_role(request.user) != 'driver':
        return HttpResponseForbidden('Доступ только для водителя.')

    shipments = Shipment.objects.filter(driver=request.user).exclude(status__in=['done', 'cancelled'])
    return render(request, 'shipments/driver_panel.html', {'shipments': shipments})


@login_required
def create_shipment(request):
    ensure_user_profile(request.user)

    if user_role(request.user) != 'company':
        return HttpResponseForbidden('Создавать отправки может только компания.')

    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        if form.is_valid():
            shipment = form.save(commit=False)

            shipment.company = request.user
            shipment.origin_lat = form.cleaned_data.get('origin_lat')
            shipment.origin_lng = form.cleaned_data.get('origin_lng')
            shipment.destination_lat = form.cleaned_data.get('destination_lat')
            shipment.destination_lng = form.cleaned_data.get('destination_lng')

            shipment.save()

            contract_id = create_contract(shipment)
            ShipmentContract.objects.create(
                shipment=shipment,
                contract_id=contract_id
            )

            create_shipment_event(shipment, 'Отправка создана', 'Новая отправка была создана в системе.')

            if shipment.driver:
                create_notification(
                    shipment.driver,
                    'Вам назначен новый груз',
                    f'Груз "{shipment.title}" назначен вам для перевозки.'
                )

            messages.success(request, 'Отправка успешно добавлена.')
            return redirect('home')
    else:
        form = ShipmentForm()

    return render(request, 'shipments/form.html', {
        'form': form,
        'page_title': 'Добавить отправку',
        'button_text': 'Сохранить',
    })


@login_required
def edit_shipment(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if user_role(request.user) != 'company' or shipment.company != request.user:
        return HttpResponseForbidden('Редактировать может только владелец-компания.')

    if request.method == 'POST':
        form = ShipmentForm(request.POST, instance=shipment)
        if form.is_valid():
            shipment = form.save(commit=False)

            shipment.origin_lat = form.cleaned_data.get('origin_lat')
            shipment.origin_lng = form.cleaned_data.get('origin_lng')
            shipment.destination_lat = form.cleaned_data.get('destination_lat')
            shipment.destination_lng = form.cleaned_data.get('destination_lng')

            shipment.save()

            create_shipment_event(shipment, 'Отправка обновлена', 'Данные отправки были изменены.')
            messages.success(request, 'Отправка обновлена.')
            return redirect('home')
    else:
        initial = {
            'origin_lat': shipment.origin_lat,
            'origin_lng': shipment.origin_lng,
            'destination_lat': shipment.destination_lat,
            'destination_lng': shipment.destination_lng,
            'estimated_arrival': shipment.estimated_arrival.strftime('%Y-%m-%dT%H:%M') if shipment.estimated_arrival else '',
        }
        form = ShipmentForm(instance=shipment, initial=initial)

    return render(request, 'shipments/form.html', {
        'form': form,
        'page_title': 'Редактировать отправку',
        'button_text': 'Обновить',
    })


@login_required
def delete_shipment(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if user_role(request.user) != 'company' or shipment.company != request.user:
        return HttpResponseForbidden('Удалять может только владелец-компания.')

    if request.method == 'POST':
        shipment.delete()
        messages.success(request, 'Удалено.')
        return redirect('home')

    return render(request, 'shipments/delete.html', {
        'shipment': shipment,
    })


@login_required
@require_POST
def start_shipment(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if request.user != shipment.driver and request.user != shipment.company:
        return HttpResponseForbidden('Нет доступа.')

    if shipment.status in ['created', 'docs', 'ready', 'delayed']:
        shipment.status = 'in_transit'
        shipment.is_delayed = False

        if not shipment.started_at:
            shipment.started_at = timezone.now()

        if not shipment.estimated_arrival:
            shipment.estimated_arrival = timezone.now() + timedelta(hours=8)

        shipment.save()

        create_shipment_event(shipment, 'Рейс начат', 'Груз начал движение.')

        if shipment.company:
            create_notification(shipment.company, 'Груз отправлен', f'Груз "{shipment.title}" начал движение.')

        if shipment.driver:
            create_notification(shipment.driver, 'Рейс начат', f'Вы начали перевозку груза "{shipment.title}".')

    return redirect('shipment_map', pk=pk)


@login_required
@require_POST
def delay_shipment(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if request.user != shipment.driver and request.user != shipment.company:
        return HttpResponseForbidden('Нет доступа.')

    form = ShipmentDelayForm(request.POST)

    if form.is_valid():
        shipment.is_delayed = True
        shipment.status = 'delayed'
        shipment.delay_minutes += form.cleaned_data['delay_minutes']
        shipment.delay_reason = form.cleaned_data['delay_reason']

        if shipment.estimated_arrival:
            shipment.estimated_arrival += timedelta(minutes=form.cleaned_data['delay_minutes'])
        else:
            shipment.estimated_arrival = timezone.now() + timedelta(minutes=form.cleaned_data['delay_minutes'])

        shipment.save()

        msg = f'Причина: {shipment.delay_reason}. Задержка: {shipment.delay_minutes} мин.'
        create_shipment_event(shipment, 'Груз задерживается', msg)

        if shipment.company:
            create_notification(
                shipment.company,
                'Есть задержка груза',
                f'Груз "{shipment.title}" задерживается. {msg}'
            )

        if shipment.driver:
            create_notification(
                shipment.driver,
                'Задержка сохранена',
                f'Для груза "{shipment.title}" записана задержка.'
            )

        messages.warning(request, 'Задержка сохранена.')

    return redirect('shipment_map', pk=pk)


@login_required
@require_POST
def complete_shipment(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if request.user != shipment.driver and request.user != shipment.company:
        return HttpResponseForbidden('Нет доступа.')

    shipment.status = 'done'
    shipment.actual_arrival = timezone.now()
    shipment.progress_percent = 100
    shipment.is_delayed = False
    shipment.save()

    create_shipment_event(shipment, 'Груз доставлен', 'Отправка успешно завершена.')

    if shipment.company:
        create_notification(shipment.company, 'Груз доставлен', f'Груз "{shipment.title}" доставлен.')

    if shipment.driver:
        create_notification(shipment.driver, 'Рейс завершён', f'Груз "{shipment.title}" отмечен как доставленный.')

    messages.success(request, 'Груз доставлен.')
    return redirect('shipment_map', pk=pk)


@login_required
def sign_contract(request, shipment_id):
    contract = ShipmentContract.objects.get(shipment_id=shipment_id)
    return JsonResponse({
        'shipment_id': shipment_id,
        'contract_id': contract.contract_id,
        'status': contract.status,
        'signed_by_sender': contract.signed_by_sender,
        'signed_by_receiver': contract.signed_by_receiver,
    })


@csrf_exempt
def contract_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        contract_id = data.get('contract_id')
        status = data.get('status')

        contract = ShipmentContract.objects.get(contract_id=contract_id)
        contract.status = status
        contract.save()

        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Only POST allowed'}, status=400)


@login_required
def api_shipments(request):
    ensure_user_profile(request.user)
    shipments = Shipment.objects.all()

    role = user_role(request.user)
    if role == 'driver':
        shipments = shipments.filter(driver=request.user)
    elif role == 'company':
        shipments = shipments.filter(company=request.user)

    if request.method == 'GET':
        shipments = shipments.order_by('-created_at')
        data = [shipment_to_dict(shipment) for shipment in shipments]
        return JsonResponse({'shipments': data})

    if request.method == 'POST':
        if role != 'company':
            return JsonResponse({'error': 'Only company can create shipment'}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Неверный JSON')

        driver = None
        driver_id = data.get('driver_id')
        if driver_id:
            driver = User.objects.filter(id=driver_id, profile__role='driver').first()

        shipment = Shipment.objects.create(
            title=data.get('title', ''),
            sender=data.get('sender', ''),
            receiver=data.get('receiver', ''),
            company=request.user,
            driver=driver,
            origin_city=data.get('origin_city', ''),
            destination_city=data.get('destination_city', ''),
            origin_lat=data.get('origin_lat'),
            origin_lng=data.get('origin_lng'),
            destination_lat=data.get('destination_lat'),
            destination_lng=data.get('destination_lng'),
            route=data.get('route', ''),
            status=data.get('status', 'created'),
            weight=float(data.get('weight', 0)),
            price=float(data.get('price', 0)),
            is_fragile=bool(data.get('is_fragile', False)),
            fragile_level=data.get('fragile_level', 'low'),
        )

        contract_id = create_contract(shipment)
        ShipmentContract.objects.create(
            shipment=shipment,
            contract_id=contract_id
        )

        create_shipment_event(shipment, 'Отправка создана через API', 'Новая отправка создана через API.')

        return JsonResponse({
            'message': 'Shipment created',
            'shipment': shipment_to_dict(shipment)
        }, status=201)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def api_shipment_detail(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if request.user != shipment.company and request.user != shipment.driver:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    return JsonResponse({'shipment': shipment_to_dict(shipment)})


@login_required
def shipment_documents(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if request.user != shipment.company and request.user != shipment.driver:
        return HttpResponseForbidden('Нет доступа.')

    documents = shipment.documents.all().order_by('-uploaded_at')

    return render(request, 'shipments/documents.html', {
        'shipment': shipment,
        'documents': documents,
    })


@login_required
def upload_document(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if request.user != shipment.company and request.user != shipment.driver:
        return HttpResponseForbidden('Нет доступа.')

    if request.method == 'POST':
        form = ShipmentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.shipment = shipment
            document.save()

            create_shipment_event(
                shipment,
                'Документ загружен',
                f'Загружен документ "{document.title}".'
            )

            messages.success(request, 'Документ успешно загружен.')
            return redirect('shipment_documents', pk=shipment.pk)
        else:
            messages.error(request, 'Проверь форму. Все обязательные поля должны быть заполнены.')
    else:
        form = ShipmentDocumentForm()

    return render(request, 'shipments/upload_document.html', {
        'shipment': shipment,
        'form': form,
    })


@login_required
def delete_document(request, pk):
    ensure_user_profile(request.user)
    document = get_object_or_404(ShipmentDocument, pk=pk)
    shipment_id = document.shipment.id

    if request.user != document.shipment.company and request.user != document.shipment.driver:
        return HttpResponseForbidden('Нет доступа.')

    if request.method == 'POST':
        document.file.delete(save=False)

        create_shipment_event(
            document.shipment,
            'Документ удалён',
            f'Удалён документ "{document.title}".'
        )

        document.delete()
        messages.success(request, 'Документ удалён.')
        return redirect('shipment_documents', pk=shipment_id)

    return render(request, 'shipments/delete_document.html', {
        'document': document,
    })


@login_required
def shipment_map(request, pk):
    ensure_user_profile(request.user)
    shipment = get_object_or_404(Shipment, pk=pk)

    if request.user != shipment.company and request.user != shipment.driver:
        return HttpResponseForbidden('Нет доступа.')

    delay_form = ShipmentDelayForm()

    return render(request, 'shipments/map.html', {
        'shipment': shipment,
        'delay_form': delay_form,
        'events': shipment.events.all()[:10],
    })


@login_required
@require_POST
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('home')


@login_required
def support_list(request):
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shipments/support_list.html', {'tickets': tickets})


@login_required
def support_create(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        message_form = SupportMessageForm(request.POST)

        if form.is_valid() and message_form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()

            msg = message_form.save(commit=False)
            msg.ticket = ticket
            msg.author = request.user
            msg.is_admin_reply = request.user.is_staff
            msg.save()

            messages.success(request, 'Обращение в поддержку создано.')
            return redirect('support_detail', pk=ticket.pk)
    else:
        form = SupportTicketForm()
        message_form = SupportMessageForm()

    return render(request, 'shipments/support_create.html', {
        'form': form,
        'message_form': message_form,
    })


@login_required
def support_detail(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk)

    if request.user != ticket.user and not request.user.is_staff:
        return HttpResponseForbidden('Нет доступа.')

    if request.method == 'POST':
        form = SupportMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.author = request.user
            msg.is_admin_reply = request.user.is_staff
            msg.save()

            if request.user.is_staff and ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save()

            messages.success(request, 'Сообщение отправлено.')
            return redirect('support_detail', pk=ticket.pk)
    else:
        form = SupportMessageForm()

    return render(request, 'shipments/support_detail.html', {
        'ticket': ticket,
        'form': form,
    })


@login_required
def admin_support_list(request):
    if not request.user.is_staff:
        return HttpResponseForbidden('Доступ только для администратора.')

    tickets = SupportTicket.objects.all().order_by('-created_at')
    return render(request, 'shipments/admin_support_list.html', {'tickets': tickets})


@login_required
@require_POST
def close_ticket(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden('Доступ только для администратора.')

    ticket = get_object_or_404(SupportTicket, pk=pk)
    ticket.status = 'closed'
    ticket.save()

    messages.success(request, 'Обращение закрыто.')
    return redirect('support_detail', pk=pk)


def about(request):
    return render(request, 'shipments/about.html')