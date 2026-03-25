from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Device, UserDevice
from .services import get_sensor_data, get_latest_reading

@login_required
def device_list(request):
    devices = Device.objects.filter(is_active=True).order_by('device_id')

    user_links = {
        link.device_id: link
        for link in UserDevice.objects.filter(user=request.user).select_related('device')
    }

    devices_with_data = []
    for device in devices:
        devices_with_data.append({
            'device': device,
            'user_device': user_links.get(device.id),
            'latest': get_latest_reading(device.device_id),
        })

    return render(request, 'devices/list.html', {
        'devices': devices_with_data
    })
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
