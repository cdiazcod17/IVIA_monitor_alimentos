from django.db import connections, OperationalError, ProgrammingError, transaction, DatabaseError, models
from datetime import timedelta
from django.utils import timezone
from .models import SensorReading, DeviceCommand, Device

class DatabaseConnectionError(Exception):
    """Excepción personalizada para errores de conexión a la base de datos de sensores."""
    pass

def check_connection():
    """Verifica si la base de datos está disponible mediante el ORM."""
    try:
        SensorReading.objects.exists()
    except (OperationalError, DatabaseError):
        raise DatabaseConnectionError("No se pudo establecer conexión con el dispositivo (Base de datos de sensores).")

def get_sensor_data(device_id: int, limit: int = 50) -> list[dict]:
    try:
        readings = SensorReading.objects.filter(device_id=device_id).order_by('-dateData', '-timeData')[:limit]
        return [
            {
                'device_id': r.device_id,
                'temperature': r.temperature / 100.0,
                'humidity': r.humidity / 100.0,
                'pressure': r.pressure,
                'co2': r.co2,
                'weight': r.weight,
                'ethylene': r.ethylene,
                'dateData': r.dateData,
                'timeData': r.timeData,
            } for r in readings
        ]
    except (OperationalError, DatabaseError) as e:
        raise DatabaseConnectionError(f"Error al obtener datos: {e}")

def save_sensor_readings_batch(readings: list):
    """Inserta múltiples lecturas en una sola transacción para mejorar rendimiento."""
    if not readings:
        return
    try:
        objs = [
            SensorReading(
                report_id=r['report_id'],
                device_id=r['device_id'],
                sequence=r['sequence'],
                timeData=r['timeData_str'],
                dateData=r['dateData_str'],
                temperature=r['temperature_raw'],
                humidity=r['humidity_raw'],
                pressure=r['pressure'],
                co2=r['co2'],
                weight=r['weight'],
                ethylene=r['ethylene']
            ) for r in readings
        ]
        SensorReading.objects.bulk_create(objs)
    except Exception as e:
        print(f"Error en inserción masiva: {e}")

def get_pending_commands(device_id: int):
    """Obtiene comandos pendientes de la base de datos para enviar al dispositivo."""
    try:
        cmd = DeviceCommand.objects.filter(device_id=device_id, executed=False).first()
        if cmd:
            return {'id': cmd.id, 'type': cmd.command_type, 'payload': cmd.payload}
    except:
        return None

def mark_command_executed(command_id: int):
    DeviceCommand.objects.filter(id=command_id).update(executed=True)

def save_sensor_reading(reading_data: dict):
    """Inserta una lectura proveniente del sensor HID en la base de datos de sensores."""
    try:
        SensorReading.objects.create(
            report_id=reading_data['report_id'],
            device_id=reading_data['device_id'],
            sequence=reading_data['sequence'],
            timeData=reading_data['timeData_str'],
            dateData=reading_data['dateData_str'],
            temperature=reading_data['temperature_raw'],
            humidity=reading_data['humidity_raw'],
            pressure=reading_data['pressure'],
            co2=reading_data['co2'],
            weight=reading_data['weight'],
            ethylene=reading_data['ethylene']
        )
    except (OperationalError, DatabaseError):
        raise DatabaseConnectionError("No se pudo guardar la lectura en la base de datos de sensores.")


def get_latest_reading(device_id: int) -> dict | None:
    try:
        data = get_sensor_data(device_id, limit=1)
        return data[0] if data else None
    except DatabaseConnectionError:
        raise


def build_filter(range_preset, date_from=None, date_to=None):
    if range_preset == 'custom' and date_from and date_to:
        date_from = date_from.replace('T', ' ')
        date_to   = date_to.replace('T', ' ')
        return "AND dateData BETWEEN %s AND %s", [date_from, date_to]

    hours = {'1h': 1, '6h': 6, '24h': 24, '7d': 168}.get(range_preset, 24)
    return "AND dateData >= DATE_SUB(NOW(), INTERVAL %s HOUR)", [hours]


def get_device_stats(device_id, range_preset='24h', date_from=None, date_to=None):
    """Estadísticas agregadas (avg, max, min, count) del dispositivo."""
    try:
        where, extra_params = build_filter(range_preset, date_from, date_to)

        with connections['sensors'].cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    AVG(temperature) / 100.0, AVG(humidity) / 100.0,
                    MAX(temperature) / 100.0, MIN(temperature) / 100.0,
                    MAX(humidity) / 100.0,    MIN(humidity) / 100.0,
                    COUNT(*),
                    MAX(dateData)
                FROM sensor_readings
                WHERE device_id = %s {where}
            """, [device_id] + extra_params)

            row = cursor.fetchone()

        if not row or row[6] == 0:
            return None

        return {
            'avg_temp':  round(row[0], 1) if row[0] else None,
            'avg_hum':   round(row[1], 1) if row[1] else None,
            'max_temp':  row[2],
            'min_temp':  row[3],
            'max_hum':   row[4],
            'min_hum':   row[5],
            'count':     row[6],
            'last_seen': row[7],
        }
    except OperationalError as e:
        print("Error de conexión con la base de datos de sensores:", e)
        raise DatabaseConnectionError("No se pudo establecer conexión con el dispositivo (Base de datos de sensores).")


def get_filtered_readings(device_id, range_preset='24h', date_from=None, date_to=None, limit=200):
    """Lecturas filtradas por rango para tabla y descarga."""
    try:
        where, extra_params = build_filter(range_preset, date_from, date_to)

        with connections['sensors'].cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    dateData, 
                    temperature / 100.0 as temperature, 
                    humidity / 100.0 as humidity, 
                    pressure, co2, weight, ethylene
                FROM sensor_readings
                WHERE device_id = %s {where}
                ORDER BY dateData DESC
                LIMIT %s
            """, [device_id] + extra_params + [limit])
            columns = ['dateData', 'temperature', 'humidity', 'pressure', 'co2', 'weight', 'ethylene']  
            rows = cursor.fetchall()
            data = []
            for row in rows:
                r = dict(zip(columns, row))
                # formatea dateData a string con segundos
                if r['dateData']:
                    r['dateData_str'] = r['dateData'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    r['dateData_str'] = ''
                data.append(r)
            return data
    except OperationalError as e:
        print("Error de conexión con la base de datos de sensores:", e)
        raise DatabaseConnectionError("No se pudo establecer conexión con el dispositivo (Base de datos de sensores).")