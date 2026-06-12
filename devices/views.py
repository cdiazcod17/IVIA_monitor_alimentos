import csv
import logging
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Device, UserDevice, DeviceCommand
from . import services
from django.http import HttpResponse, JsonResponse
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)


@login_required
def device_list_latest_json(request):
    status_filter = request.GET.get('status', 'active')
    try:
        devices = Device.objects.all()

        if status_filter == 'inactive':
            devices = devices.filter(is_active=False)
        elif status_filter == 'active':
            devices = devices.filter(is_active=True)
        
        data = {}
        for device in devices:
            data[device.device_id] = services.get_latest_reading(device.device_id)
            
        return JsonResponse(data, encoder=DjangoJSONEncoder)
    except services.DatabaseConnectionError as e:
        return JsonResponse({'error': str(e)}, status=503)


@login_required
def device_readings_json(request, device_id):
    range_preset = request.GET.get('range', '24h')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    try:
        latest = services.get_latest_reading(device_id)
        
        all_sensor_data = services.get_filtered_readings(
            device_id=device_id,
            range_preset=range_preset,
            date_from=date_from or None,
            date_to=date_to or None,
            limit=20 # Limitamos a los últimos 20 registros, simulando la 1ra página del Paginator
        )

        return JsonResponse({
            'latest': latest,
            'sensor_data': all_sensor_data,
        }, encoder=DjangoJSONEncoder)
    except services.DatabaseConnectionError as e:
        return JsonResponse({'error': str(e)}, status=503)


@login_required
def device_list(request):
    # Filtro por GET
    status_filter = request.GET.get('status', 'active')
    try:
        # Verificamos conexión antes de proceder
        services.check_connection()

        devices = Device.objects.all().order_by('id')

        if status_filter == 'inactive':
            devices = devices.filter(is_active=False)
        elif status_filter == 'active':
            devices = devices.filter(is_active=True)

        user_links = {
            link.device_id: link
            for link in UserDevice.objects.filter(user=request.user)
        }

        devices_with_data = []
        for device in devices:
            devices_with_data.append({
                'device': device,
                'user_device': user_links.get(device.id),
                'latest': None, # Se cargará asíncronamente vía JavaScript
            })

        context = {
            'devices': devices_with_data,
            'status_filter': status_filter,
            'total_active': Device.objects.filter(is_active=True).count(),
            'total_inactive': Device.objects.filter(is_active=False).count(),
        }
        return render(request, 'devices/list.html', context)
    except services.DatabaseConnectionError as e:
        context = {
            'error_message': str(e),
            'status_filter': status_filter,
            'devices': [],
        }
        return render(request, 'devices/list.html', context)
    except Exception as e:
        messages.warning(request, f'Ocurrió un error inesperado: {str(e)}')
        return render(request, 'devices/list.html', {'devices': [], 'status_filter': status_filter})
    


@login_required
def device_add(request):
    devices = Device.objects.filter(is_active=True).order_by('id')
    user_devices_qs = UserDevice.objects.filter(user=request.user, device__is_active=True).select_related('device')
    user_devices_map = {ud.device.device_id: ud for ud in user_devices_qs}

    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        alias = request.POST.get('alias', '').strip()
        food_name = request.POST.get('food_name', '').strip()
        notes = request.POST.get('notes', '').strip()

        device = get_object_or_404(Device, device_id=device_id, is_active=True)

        user_device, created = UserDevice.objects.get_or_create(
            user=request.user,
            device=device,
            defaults={
                'alias': alias,
                'food_name': food_name,
                'notes': notes,
            }
        )

        if not created:
            user_device.alias = alias
            user_device.food_name = food_name
            user_device.notes = notes
            user_device.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'alias': alias, 'food_name': food_name, 'notes': notes})

        messages.success(request, 'Configuración del dispositivo guardada correctamente.')
        return redirect('devices:add')

    selected_device_id = request.GET.get('device_id') or next(iter(user_devices_map.keys()), '')

    devices_with_user_data = []
    selected_user_device = None

    for device in devices:
        ud = user_devices_map.get(device.device_id)
        devices_with_user_data.append({
            'device': device,
            'user_device': ud,
        })
        if device.device_id == selected_device_id:
            selected_user_device = ud

    context = {
        'devices_with_user_data': devices_with_user_data,
        'selected_device_id': selected_device_id,
        'selected_user_device': selected_user_device,
    }
    return render(request, 'devices/add.html', context)


@login_required
def device_detail(request, device_id):
    range_preset = request.GET.get('range', '24h')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    page_number = request.GET.get('page')

    try:
        latest = services.get_latest_reading(device_id)
        stats = services.get_device_stats(device_id, range_preset, date_from, date_to)

        user_device = UserDevice.objects.filter(
            user=request.user,
            device__device_id=device_id
        ).select_related('device').first()

        device_alias = ''
        if user_device and user_device.alias:
            device_alias = user_device.alias.strip()

        # Si el usuario envió un cambio de configuración (ej: frecuencia)
        if request.method == 'POST' and 'set_frequency' in request.POST:
            new_freq = request.POST.get('frequency')
            # Aquí guardaríamos en una tabla de comandos que el worker revise
            # O simplemente actualizamos el modelo Device si el worker lo consulta
            messages.info(request, f"Comando de frecuencia ({new_freq}s) enviado al dispositivo.")

        all_sensor_data = services.get_filtered_readings(
            device_id=device_id,
            range_preset=range_preset,
            date_from=date_from or None,
            date_to=date_to or None,
        )

        paginator = Paginator(all_sensor_data, 20)
        page_obj = paginator.get_page(page_number)
        sensor_data = page_obj.object_list

        context = {
            'device_id': device_id,
            'device_alias': device_alias,
            'user_device': user_device,
            'latest': latest,
            'stats': stats,
            'sensor_data': sensor_data,
            'page_obj': page_obj,
            'range_preset': range_preset,
            'date_from': date_from,
            'date_to': date_to,
            'preset_ranges': [('1h', '1h'), ('6h', '6h'), ('24h', '24h'), ('7d', '7 días')],
        }
        return render(request, 'devices/detail.html', context)
    except services.DatabaseConnectionError as e:
        messages.error(request, str(e))
        return redirect('devices:list')


@login_required
def device_download_csv(request, device_id):
    range_preset = request.GET.get('range', '24h')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    try:
        readings = services.get_filtered_readings(
            device_id, range_preset, date_from, date_to, limit=99999
        )

        response = HttpResponse(content_type='text/csv')
        safe_device_id = re.sub(r'[^\w-]', '', str(device_id))
        safe_range = re.sub(r'[^\w-]', '', range_preset)
        response['Content-Disposition'] = f'attachment; filename="{safe_device_id}_{safe_range}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Temperatura', 'Humedad', 'Presion', 'CO2', 'Peso', 'Etileno'])

        for r in readings:
            writer.writerow([
                r['dateData'],
                r['temperature'],
                r['humidity'],
                r['pressure'],
                r['co2'],
                r['weight'],
                r['ethylene']
            ])

        return response
    except services.DatabaseConnectionError as e:
        messages.error(request, str(e))
        return redirect('devices:detail', device_id=device_id)


@login_required
def device_disable(request):
    if request.method != 'POST':
        return redirect('devices:list')

    device_id = request.POST.get('device_id')
    device = get_object_or_404(Device, device_id=device_id)
    
    # Crear comando para apagar el dispositivo
    DeviceCommand.objects.create(
        device_id=device.device_id,
        command_type='SET_CONFIG',
        payload={'power': 0}  # 0 = apagado
    )
    
    # Marcar como inactivo en la UI
    device.is_active = False
    device.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
        return JsonResponse({'status': 'success', 'is_active': False, 'message': f'{device.default_name} se apagará pronto.'})

    messages.success(request, f'✋ Comando enviado: {device.default_name} se apagará cuando reciba la orden.')
    return redirect('devices:list')


@login_required
def device_enable(request):
    if request.method != 'POST':
        return redirect('devices:list')

    device_id = request.POST.get('device_id')
    device = get_object_or_404(Device, device_id=device_id)
    
    # Crear comando para encender el dispositivo
    DeviceCommand.objects.create(
        device_id=device.device_id,
        command_type='SET_CONFIG',
        payload={'power': 1}  # 1 = encendido
    )
    
    # Marcar como activo en la UI
    device.is_active = True
    device.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
        return JsonResponse({'status': 'success', 'is_active': True, 'message': f'{device.default_name} se encenderá pronto.'})

    messages.success(request, f'✅ Comando enviado: {device.default_name} se encenderá cuando reciba la orden.')
    return redirect('devices:list')


@login_required
def set_global_frequency(request):
    if request.method != 'POST':
        return redirect('devices:list')
    
    try:
        frequency = max(1, min(3600, int(request.POST.get('frequency', 2))))
        power = max(0, min(1, int(request.POST.get('power', 1))))
    except (ValueError, TypeError):
        messages.error(request, 'Valores de configuración inválidos.')
        return redirect('devices:list')

    # Crear comando para cada dispositivo
    from .models import DeviceCommand
    for device in Device.objects.filter(is_active=True):
        DeviceCommand.objects.create(
            device_id=device.device_id,
            command_type='SET_CONFIG',
            payload={'freq': frequency, 'power': power},
            executed=False
        )
    
    messages.success(request, f'✓ Comandos de frecuencia enviados a todos los dispositivos ({frequency}s)')
    return redirect('devices:list')


@login_required
def set_device_frequency(request):
    if request.method != 'POST':
        return redirect('devices:list')
    
    try:
        device_id = int(request.POST.get('device_id'))
        frequency = max(1, min(3600, int(request.POST.get('frequency', 2))))
        power = max(0, min(1, int(request.POST.get('power', 1))))
    except (ValueError, TypeError):
        messages.error(request, 'Valores de configuración inválidos.')
        return redirect('devices:list')

    from .models import DeviceCommand
    DeviceCommand.objects.create(
        device_id=device_id,
        command_type='SET_CONFIG',
        payload={'freq': frequency, 'power': power},
        executed=False
    )
    
    device = Device.objects.get(device_id=device_id)
    messages.success(request, f'✓ Comando enviado a {device.default_name} (frecuencia: {frequency}s)')
    return redirect('devices:list')


@login_required
def get_command_status(request):
    from .models import DeviceCommand
    import json
    from django.utils import timezone
    from datetime import timedelta
    
    # Comandos pendientes
    pending = DeviceCommand.objects.filter(executed=False).values(
        'id', 'device_id', 'command_type', 'created_at', 'payload'
    )
    
    # Comandos ejecutados recientes (últimas 24 horas)
    recent_date = timezone.now() - timedelta(hours=24)
    recent = DeviceCommand.objects.filter(
        executed=True, 
        created_at__gte=recent_date
    ).values('id', 'device_id', 'command_type', 'created_at', 'payload').order_by('-created_at')[:10]
    
    pending_list = list(pending)
    recent_list = list(recent)
    
    # Serializar con formato de string para el payload
    for item in pending_list + recent_list:
        item['created_at'] = item['created_at'].isoformat()
        item['payload'] = json.dumps(item['payload']) if isinstance(item['payload'], dict) else str(item['payload'])
    
    return JsonResponse({
        'pending_commands': pending_list,
        'command_history': recent_list
    })


@login_required
def get_device_config(request):
    """API que devuelve la configuración actual de cada dispositivo"""
    from .models import DeviceCommand
    import json
    
    device_id = request.GET.get('device_id')
    
    # Obtener el último comando ejecutado (configuración actual)
    last_command = DeviceCommand.objects.filter(
        device_id=device_id,
        executed=True,
        command_type='SET_CONFIG'
    ).order_by('-created_at').first()
    
    # Verificar si hay comandos pendientes
    pending_command = DeviceCommand.objects.filter(
        device_id=device_id,
        executed=False,
        command_type='SET_CONFIG'
    ).order_by('-created_at').first()
    
    if last_command:
        payload = last_command.payload
        return JsonResponse({
            'device_id': device_id,
            'frequency': payload.get('freq', 2),
            'power': payload.get('power', 1),
            'last_config': last_command.created_at.isoformat(),
            'has_config': True,
            'has_pending': pending_command is not None,
            'pending_command_type': pending_command.payload.get('power') if pending_command else None
        })
    else:
        # Configuración por defecto si no hay comandos ejecutados
        return JsonResponse({
            'device_id': device_id,
            'frequency': 2,  # Por defecto
            'power': 1,      # Por defecto
            'has_config': False,
            'has_pending': pending_command is not None,
            'pending_command_type': pending_command.payload.get('power') if pending_command else None
        })