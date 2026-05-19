from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Device, UserDevice
from . import services
import csv
from django.http import HttpResponse, JsonResponse
from django.core.serializers.json import DjangoJSONEncoder


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
        response['Content-Disposition'] = f'attachment; filename="{device_id}_{range_preset}.csv"'

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
    device.is_active = False
    device.save()
    messages.success(request, f'Dispositivo {device.default_name} desactivado')
    return redirect('devices:list')


@login_required
def device_enable(request):
    if request.method != 'POST':
        return redirect('devices:list')

    device_id = request.POST.get('device_id')
    device = get_object_or_404(Device, device_id=device_id)
    device.is_active = True
    device.save()
    messages.success(request, f'Dispositivo {device.default_name} Activado')
    return redirect('devices:list')