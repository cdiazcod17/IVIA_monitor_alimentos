from django.contrib import admin
from .models import Device, UserDevice

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    # Columnas visibles en la lista
    list_display = ('device_id', 'default_name', 'location', 'is_active')
    # Filtros laterales
    list_filter = ('is_active',)
    # Buscador
    search_fields = ('device_id', 'default_name', 'location')
    # Ordenación por ID de dispositivo
    ordering = ('device_id',)

@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    # Columnas visibles en la lista
    list_display = ('user', 'device', 'alias', 'food_name', 'linked_at')
    # Filtros por fecha de vinculación
    list_filter = ('linked_at',)
    # Buscador (incluyendo campos de modelos relacionados mediante __)
    search_fields = ('user__email', 'user__username', 'device__default_name', 'alias', 'food_name')
    # Fecha de vinculación como campo de solo lectura
    readonly_fields = ('linked_at',)
