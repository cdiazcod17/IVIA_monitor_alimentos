from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Campos que se muestran en la lista de usuarios
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_verified', 'is_staff')
    # Filtros laterales
    list_filter = ('is_verified', 'is_staff', 'is_superuser', 'is_active')
    # Campos de búsqueda
    search_fields = ('email', 'username', 'first_name', 'last_name')
    # Orden predeterminado
    ordering = ('email',)

    # Configuración de los formularios de edición
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('is_verified',)}),
    )
    # Configuración para el formulario de creación
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'is_verified'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
