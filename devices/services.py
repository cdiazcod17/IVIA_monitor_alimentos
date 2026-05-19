from django.db import connections, OperationalError, ProgrammingError
from datetime import timedelta
from django.utils import timezone

class DatabaseConnectionError(Exception):
    """Excepción personalizada para errores de conexión a la base de datos de sensores."""
    pass

def check_connection():
    """Verifica si la base de datos de sensores está disponible."""
    try:
        with connections['sensors'].cursor() as cursor:
            cursor.execute("SELECT 1")
    except OperationalError:
        raise DatabaseConnectionError("No se pudo establecer conexión con el dispositivo (Base de datos de sensores).")

def get_sensor_data(device_id: int, limit: int = 50) -> list[dict]:
    try:
        with connections['sensors'].cursor() as cursor:
            cursor.execute("""
            SELECT
                device_id,
                temperature / 100.0 as temperature,
                humidity / 100.0 as humidity,
                pressure,
                co2,
                weight,
                ethylene,
                dateData,
                timeData
            FROM sensor_readings
            WHERE device_id = %s
            ORDER BY dateData DESC, timeData DESC
            LIMIT %s
        """, [device_id, limit])


            if not cursor.description:
                return []

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    except OperationalError as e:
        print("Error de conexión con la base de datos de sensores:", e)
        raise DatabaseConnectionError("No se pudo establecer conexión con el dispositivo (Base de datos de sensores).")
    except Exception as e:
        print("Error en la consulta", e)
        return []


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