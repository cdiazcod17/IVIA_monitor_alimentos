# Pot Monitor - Sistema de Monitoreo Agrícola IVIA 📱🌱

## Descripción
Aplicación **full-stack** Django + Raspberry Pi para monitoreo en tiempo real de **sensores agrícolas** en el Instituto Valenciano de Investigación Agrícola (IVIA). Permite a investigadores gestionar dispositivos, visualizar datos y controlar la frecuencia de muestreo.

**Estado**: Producción activa | **Usuarios**: Investigadores IVIA | **Ubicación**: Valencia, España

## 🚀 Servicios Actuales

### **Dashboard Web (Django + Bootstrap 5)**

✅ Gestión dispositivos (activar/desactivar)
✅ Filtros activos/inactivos/todos
✅ Control granular periodicidad muestreo (2s,5s,10s,30s)
✅ Visualización datos temperatura/humedad en tiempo real
✅ Cards responsive con última lectura
✅ Empty states y UX móvil-first

text

### **Script Placa (Raspberry Pi + HID)**

✅ Lectura HID sensores (VID:0x06DC PID:0x5750)
✅ Buffer inteligente (30 lecturas → MySQL)
✅ Configuración dinámica por usuario/dispositivo
✅ API disco espacio (/api/disk → % uso)
✅ Multi-dispositivo/usuario
✅ Sleep dinámico por config usuario

text

### **Base de Datos (MySQL → Disco Externo)**

✅ sensor_readings (temp, hum, pres, co2, peso, etileno)
✅ UserDevice (alias, intervalos, user FK)
✅ Almacenamiento externo montado /mnt/external_data
✅ Backup automático SD→USB

text

### **Control Periodicidad (Feature Nuevo)**

👥 Usuario1 → Device001 → 2s (Alta precisión)
👥 Usuario2 → Device001 → 10s (Económico)
👥 Usuario3 → Device002 → 5s (Normal)

Flujo: Web → Django API → HID CMD → MCU → Sleep dinámico

text

## 🏗️ Arquitectura

Raspberry Pi + Sensores HID
↓ (datos cada X seg)
MySQL (disco externo USB)
↓ (API REST)
Django Dashboard (Web)
↓ (HID write)
MCU config (sampling rate)

text

## 📱 Interfaz Usuario

| Pantalla | Funcionalidades |
|----------|----------------|
| **Lista** | Filtros, cards responsive, ON/OFF, última lectura |
| **Detalle** | Gráficos tiempo real, control periodicidad |
| **Dashboard** | % Disco, alertas espacio, estado dispositivos |

## 🔧 Instalación

```bash
# Backend Django
git clone <repo>
cd pot_monitor
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Placa (Raspberry Pi)
sudo apt install python3-hid python3-mysql.connector python3-requests
python3 sensor_script.py

🛠️ Stack Técnico

text
Frontend: Django Templates + Bootstrap 5 + htmx
Backend: Django 4.x + MySQL 8
Placa: Python 3.11 + hidapi + MySQL Connector
Infra: Raspberry Pi 4 + USB 3.0 SSD + Nginx
DevOps: GitHub Actions + Docker-ready

📊 Métricas Esperadas

text
-  1-10 dispositivos activos simultáneos
-  2-30 segundos intervalo muestreo configurable
-  ~1.2MB/día/dispositivo (30s intervalos)
-  Escalable multi-investigador IVIA

🤝 Colaboradores

Carlos Díaz - Full-stack DAW Intern @ IVIA
Desarrollo: Django/Vue.js, DevOps, Base de datos
Enfocado: Infra producción, UX agrícola
📄 Licencia

Propiedad Instituto Valenciano de Investigación Agrícola (IVIA)
Uso interno - No distribuir sin autorización

¡Sistema listo para producción agrícola! 🌾💾🚀

Próximos: Alertas WhatsApp, ML predicción estrés vegetal, Multi-placa