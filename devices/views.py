from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Device, UserDevice
from . import services
import csv
from django.http import HttpResponse


@login_required
def device_list(request):
    # Filtro por GET
    status_filter = request.GET.get('status', 'all')    
    devices = Device.objects.all().order_by('device_id')    
    if status_filter == 'inactive':
        devices = devices.filter(is_active=False)
    elif status_filter == 'active':
        devices = devices.filter(is_active=True)
    
    user_links = {link.device_id: link for link in UserDevice.objects.filter(user=request.user)}
    
    devices_with_data = []
    for device in devices:
        devices_with_data.append({
            'device': device,
            'user_device': user_links.get(device.id),
            'latest': services.get_latest_reading(device.device_id),
        })
    
    context = {
        'devices': devices_with_data,
        'status_filter': status_filter,  # Para mantener activo el botón
        'total_active': Device.objects.filter(is_active=True).count(),
        'total_inactive': Device.objects.filter(is_active=False).count(),
    }
    return render(request, 'devices/list.html', context)


@login_required
def device_add(request):
    devices = Device.objects.filter(is_active=True).order_by('device_id')

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

        return redirect('devices:list')

    return render(request, 'devices/add.html', {
        'devices': devices
    })
@login_required
def device_detail(request, device_id):
    # Filtros
    range_preset = request.GET.get('range', '24h')
    date_from    = request.GET.get('date_from', '')
    date_to      = request.GET.get('date_to', '')

    latest   = services.get_latest_reading(device_id)
    stats    = services.get_device_stats(device_id, range_preset, date_from, date_to)
    sensor_data = services.get_filtered_readings(
        device_id=device_id,
        range_preset=range_preset,
        date_from=date_from or None,
        date_to=date_to or None,
    )

    context = {
        'device_id':    device_id,
        'latest':       latest,
        'stats':        stats,
        'sensor_data':  sensor_data,        
        'range_preset': range_preset,
        'date_from':    date_from,
        'date_to':      date_to,
        'preset_ranges': [('1h','1h'), ('6h','6h'), ('24h','24h'), ('7d','7 días')],
    }
    return render(request, 'devices/detail.html', context)


@login_required
def device_download_csv(request, device_id):
    range_preset = request.GET.get('range', '24h')
    date_from    = request.GET.get('date_from', '')
    date_to      = request.GET.get('date_to', '')

    # Sin límite para la descarga (None = todos)
    readings = services.get_filtered_readings(
        device_id, range_preset, date_from, date_to, limit=99999
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{device_id}_{range_preset}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Temperatura', 'Humedad', 'Presion', 'CO2', 'Peso', 'Etileno'])
    for r in readings:
        writer.writerow([
            r['dateData'], r['temperature'], r['humidity'],
            r['pressure'], r['co2'], r['weight'], r['ethylene']
        ])

    return response


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