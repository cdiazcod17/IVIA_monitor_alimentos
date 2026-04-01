# Pot Monitor — Sistema de Monitoreo Agrícola IVIA

Aplicación full-stack Django para monitoreo en tiempo real de sensores agrícolas en el Instituto Valenciano de Investigación Agrícola (IVIA). Permite a investigadores gestionar dispositivos, visualizar datos y controlar la frecuencia de muestreo.

**Estado**: Producción activa, version BETA V1.0.0  
**Usuarios**: Investigadores IVIA  
**Ubicación**: Valencia, España

---

## Servicios

### Dashboard Web (Django + Bootstrap 5)

- Gestión de dispositivos (activar/desactivar)
- Filtros activos/inactivos/todos
- Control de periodicidad de muestreo (2s, 5s, 10s, 30s)
- Visualización de datos temperatura/humedad en tiempo real
- Cards responsive con última lectura
- Empty states y diseño mobile-first

### Script de placa (Raspberry Pi + HID)

- Lectura HID de sensores (VID:0x06DC PID:0x5750)
- Buffer inteligente (30 lecturas → MySQL)
- Configuración dinámica por usuario/dispositivo
- API de uso de disco (`/api/disk`)
- Soporte multi-dispositivo/usuario
- Sleep dinámico por configuración de usuario


## Interfaz de usuario

| Pantalla | Funcionalidades |
|----------|----------------|
| Lista | Filtros, cards responsive, ON/OFF, última lectura |
| Detalle | Historial filtrable, descarga CSV, control de periodicidad |
| Dashboard | Uso de disco, alertas de espacio, estado de dispositivos |

---

## Instalación

```bash
# Backend Django
git clone <repo>
cd pot_monitor
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
---

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| Frontend | Django Templates + Bootstrap 5 |
| Backend | Django 6 + MySQL 8 |
| Placa | Python 3.11 + hidapi + MySQL Connector |
| Infraestructura | Raspberry Pi 4 + USB 3.0 SSD + Nginx |

---

## Métricas de referencia

- 1–10 dispositivos activos simultáneos
- Intervalo de muestreo configurable: 2–30 segundos
- Almacenamiento aproximado: 1.2 MB/día/dispositivo (con intervalos de 30s)
- Arquitectura escalable para múltiples investigadores

---

## Próximas funcionalidades

- Alertas por WhatsApp
- Estadisticas por periodos
- Soporte multi-placa

---

## Autor

**Carlos Díaz** — Full-stack intern (DAW) @ IVIA  
Django, Vue.js, DevOps, base de datos

---

## Licencia

Propiedad del Instituto Valenciano de Investigación Agrícola (IVIA).  
Uso interno — no distribuir sin autorización.