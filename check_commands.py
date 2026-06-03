import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitor_alimentos.settings')
django.setup()

from devices.models import DeviceCommand

# Ver comandos pendientes
pendientes = DeviceCommand.objects.filter(executed=False).order_by('-created_at')
print("=== COMANDOS PENDIENTES ===")
if pendientes.exists():
    for cmd in pendientes:
        print(f"ID:{cmd.id} | Device:{cmd.device_id} | Type:{cmd.command_type} | Payload:{cmd.payload} | Created:{cmd.created_at}")
else:
    print("❌ No hay comandos pendientes")

print("\n=== ÚLTIMOS 5 COMANDOS (todos) ===")
todos = DeviceCommand.objects.all().order_by('-created_at')[:5]
for cmd in todos:
    status = "⏳ PENDIENTE" if not cmd.executed else "✅ EJECUTADO"
    print(f"{status} | ID:{cmd.id} | Device:{cmd.device_id} | {cmd.payload}")
