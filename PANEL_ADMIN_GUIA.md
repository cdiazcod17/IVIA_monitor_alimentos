# 📊 Panel de Administración - Guía de Uso

## 🎯 ¿Qué es el Panel de Administración?

El Panel de Administración es una interfaz web integrada en la vista de dispositivos (`/devices/`) que permite controlar la **frecuencia de lectura** de los sensores en tiempo real.

## 🚀 Acceso al Panel

1. Inicia sesión en la aplicación
2. Ve a **Dispositivos** (`/devices/`)
3. Click en el botón **"Panel Admin"** (esquina superior derecha)

```html
<button class="btn btn-secondary btn-sm" data-bs-toggle="modal" data-bs-target="#adminPanelModal">
    <i class="bi bi-gear me-1"></i>Panel Admin
</button>
```

## 📋 Secciones del Panel

### 1️⃣ Configuración Global

Permite cambiar la frecuencia de **TODOS** los dispositivos simultáneamente.

**Campos:**
- **Intervalo (segundos)**: Tiempo entre lecturas (1-3600s, recomendado: 1-10s)
- **Estado**: Encendido/Apagado

**Ejemplo:**
- Frecuencia: 2 segundos
- Estado: Encendido
- Click: "Aplicar a Todos"

**Resultado:** Se crean comandos `SET_CONFIG` para cada dispositivo activo.

### 2️⃣ Configuración Individual

Permite cambiar la frecuencia de un **dispositivo específico**.

**Campos:**
- **Dispositivo**: Dropdown con lista de dispositivos
- **Intervalo (segundos)**: Tiempo entre lecturas
- **Estado**: Encendido/Apagado

**Ejemplo:**
```
Dispositivo: [0] Analizador 0
Intervalo: 5 segundos
Estado: Encendido
Click: "Aplicar"
```

**Resultado:** Se crea un comando para ese dispositivo específico.

### 3️⃣ Comandos Pendientes

Muestra en **tiempo real** los comandos que están pendientes de ejecutar en los dispositivos.

**Información mostrada:**
- Device ID
- Tipo de comando (SET_CONFIG)
- Fecha/hora de creación

## ⚙️ Cómo Funciona el Sistema

### Flujo de Comando:

```
Panel Web
    ↓
set_global_frequency() / set_device_frequency()
    ↓
DeviceCommand.objects.create() [BD MySQL]
    ↓
HID Worker (hid_worker.py)
    ↓
_process_web_commands()
    ↓
Envía comando al dispositivo físico
    ↓
Marca como executed=True
```

### Archivos Modificados:

1. **templates/devices/list.html**
   - Botón "Panel Admin"
   - Modal con formularios
   - Script JS para cargar comandos

2. **devices/views.py**
   - `set_global_frequency()` - Aplicar a todos
   - `set_device_frequency()` - Aplicar a uno
   - `get_command_status()` - API para obtener estado

3. **devices/urls.py**
   - `api/set-global-frequency/`
   - `api/set-device-frequency/`
   - `api/command-status/`

## 🔄 Modelo de Base de Datos

```sql
DeviceCommand {
    id: Integer (PK)
    device_id: SmallInteger
    command_type: String ('SET_CONFIG')
    payload: JSON {'freq': 10, 'power': 1}
    executed: Boolean (default=False)
    created_at: DateTime (auto_now_add)
}
```

## 📱 Formato del Comando

```json
{
    "freq": 2,      // Segundos entre lecturas
    "power": 1      // 1=Encendido, 0=Apagado
}
```

## 🛠️ Implementación en HID Worker

El `hid_worker.py` ya incluye la lógica para procesar estos comandos:

```python
def _process_web_commands(self, device):
    cmd = services.get_pending_commands(device_id=1)
    if not cmd:
        return

    if cmd['type'] == 'SET_CONFIG':
        payload = cmd['payload']  # {'power': 1, 'freq': 10}
        packet = [0]*64
        packet[2] = 2  # MSG_ID_CONFIG
        packet[3] = payload.get('power', 1)
        freq = payload.get('freq', 10)
        packet[4] = (freq >> 8) & 0xFF
        packet[5] = freq & 0xFF
        
        device.write(packet)
        services.mark_command_executed(cmd['id'])
```

## 🎓 Ejemplos de Uso

### Caso 1: Cambiar frecuencia a 5 segundos globalmente

1. Panel Admin
2. Configuración Global
3. Intervalo: 5
4. Click: "Aplicar a Todos"
5. ✓ Se crean 10 comandos (uno por dispositivo)

### Caso 2: Acelerar solo el Dispositivo 0 a 1 segundo

1. Panel Admin
2. Configuración Individual
3. Dispositivo: [0] Analizador 0
4. Intervalo: 1
5. Click: "Aplicar"
6. ✓ Se crea 1 comando para dispositivo 0

### Caso 3: Apagar un dispositivo temporalmente

1. Panel Admin
2. Configuración Individual
3. Dispositivo: [5] Analizador 5
4. Estado: Apagado
5. Click: "Aplicar"
6. ✓ Dispositivo se detiene

## 📊 Monitoreo de Comandos

Abre el Panel Admin en cualquier momento para ver:

- ✅ Comandos ejecutados (historial 24h)
- ⏳ Comandos pendientes (esperando ejecución)

Los comandos se marcan como ejecutados cuando el HID Worker los procesa exitosamente.

## ⚡ Validaciones

- **Intervalo mínimo:** 1 segundo
- **Intervalo máximo:** 3600 segundos (1 hora)
- **Dispositivo requerido:** En configuración individual
- **Frecuencia requerida:** En ambas opciones

## 🔐 Seguridad

- Solo usuarios autenticados pueden acceder (decorator `@login_required`)
- CSRF Token en todos los formularios
- Los cambios se registran en la BD con timestamp

## 📝 Notas Técnicas

1. Los comandos se guardan en la BD `sensors` (MySQL)
2. El HID Worker revisa comandos cada 5 segundos
3. Los comandos se ejecutan en orden FIFO (primero en llegar, primero en salir)
4. El dispositivo confirmará la ejecución cuando lo procese
5. El estado se actualiza en tiempo real en el modal

## 🚀 Próximas Mejoras Opcionales

- [ ] Programar comandos para horas específicas
- [ ] Historial gráfico de cambios de frecuencia
- [ ] Alertas cuando un comando falla
- [ ] Estadísticas de uptime por dispositivo
- [ ] Auto-ajuste inteligente de frecuencia
