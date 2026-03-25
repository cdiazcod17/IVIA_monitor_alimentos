from django.db import connections, OperationalError, ProgrammingError


def get_sensor_data(device_id: int, limit: int = 50) -> list[dict]:
    try:
        with connections['sensors'].cursor() as cursor:
            cursor.execute("""
            SELECT
                device_id,
                temperature as temperature,
                humidity as humidity,
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

    except Exception as e:
        print("Error en la consulta",e)
        return []


def get_latest_reading(device_id: int) -> dict | None:
    data = get_sensor_data(device_id, limit=1)
    return data[0] if data else None
