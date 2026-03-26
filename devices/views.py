from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Device, UserDevice
from .services import get_sensor_data, get_latest_reading

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
            'latest': get_latest_reading(device.device_id),
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
    device = get_object_or_404(Device, device_id=device_id, is_active=True)

    user_device = UserDevice.objects.filter(
        user=request.user,
        device=device
    ).first()
    
    sensor_data = get_sensor_data(device.device_id)

    return render(request, 'devices/detail.html', {
        'device': device,
        'user_device': user_device,
        'sensor_data': sensor_data,
    })
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