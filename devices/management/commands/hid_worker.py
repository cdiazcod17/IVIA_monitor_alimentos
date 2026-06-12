import time
import struct
import datetime
import hid
from django.core.management.base import BaseCommand
from devices import services

class Command(BaseCommand):
    help = 'Monitor de dispositivos HID para captura de datos de sensores en tiempo real'

    def handle(self, *args, **options):
        VID = 0x06DC
        PID = 0x5750
        # Formato basado en el firmware: report_id, dev_id, msg_id, seq, time, date, temp, hum, press, co2, weight, eth
        FORMAT = "<BBBIIIhHIHii31s"
        buffer_readings = []
        last_command_check = 0

        self.stdout.write(self.style.SUCCESS(f"Iniciando monitor HID (VID:{VID:04x} PID:{PID:04x})..."))

        while True:
            try:
                h = hid.device()
                h.open(VID, PID)
                h.set_nonblocking(True)
                
                # Al conectar, sincronizar hora automáticamente (Función de la GUI)
                self._send_time_packet(h)
                self.stdout.write(self.style.SUCCESS("Dispositivo sincronizado y listo."))

                while True:
                    # 1. Verificar comandos desde la WEB (cada 5 segundos)
                    if time.time() - last_command_check > 5:
                        self._process_web_commands(h)
                        last_command_check = time.time()

                    data = h.read(64)
                    if not data:                        
                        time.sleep(0.5)  # Evitar consumo excesivo de CPU
                        continue

                    unpacked = struct.unpack(FORMAT, bytes(data[:64]))
                    
                    msg_id = unpacked[2]
                    if msg_id != 1:  # Solo procesamos lecturas de sensores (tipo 1)
                        continue

                    # Extracción de metadatos
                    report_id = unpacked[0]
                    device_id = unpacked[1]
                    sequence  = unpacked[3]
                    time_raw  = unpacked[4]
                    date_raw  = unpacked[5]

                    # Reconstrucción de tiempo/fecha (Lógica del firmware original)
                    h_ = (time_raw >> 16) & 0xFF
                    m_ = (time_raw >> 8) & 0xFF
                    s_ = time_raw & 0xFF
                    
                    y  = (date_raw >> 16) & 0xFF
                    mo = (date_raw >> 8) & 0xFF
                    d  = date_raw & 0xFF

                    time_str = f"{h_:02d}:{m_:02d}:{s_:02d}"
                    date_str = f"20{y:02d}-{mo:02d}-{d:02d} {time_str}"

                    # Preparar payload para el servicio
                    reading_data = {
                        'report_id': report_id,
                        'device_id': device_id,
                        'sequence': sequence,
                        'timeData_str': time_str,
                        'dateData_str': date_str,
                        'temperature_raw': unpacked[6],
                        'humidity_raw': unpacked[7],
                        'pressure': unpacked[8],
                        'co2': unpacked[9],
                        'weight': unpacked[10],
                        'ethylene': unpacked[11]
                    }

                    buffer_readings.append(reading_data)
                    
                    # Buffer inteligente: Guardar cada 30 lecturas
                    if len(buffer_readings) >= 30:
                        try:
                            services.save_sensor_readings_batch(buffer_readings)
                            self.stdout.write(self.style.SUCCESS(f"Batch de 30 lecturas guardado."))
                            buffer_readings = []
                        except Exception as e:
                            self.stderr.write(f"Error al guardar batch: {e}")

                    # Imprimir log similar a la consola de la GUI
                    self.stdout.write(f"[{date_str}] ID:{device_id} SEQ:{sequence} T:{unpacked[6]/100.0}")

            except Exception as e:
                # Si hay error y el buffer tiene algo, intentar salvarlo antes de morir
                if buffer_readings:
                    try: services.save_sensor_readings_batch(buffer_readings)
                    except: pass
                    buffer_readings = []
                
                self.stderr.write(self.style.WARNING(f"Error de conexión o base de datos: {e}"))
                self.stderr.write("Reintentando en 5 segundos...")
                time.sleep(5)
            finally:
                try: h.close()
                except: pass

    def _send_time_packet(self, device):
        """Reclica la lógica de 'Enviar Hora' de tu script original."""
        now = datetime.datetime.now()
        packet = [0]*64
        packet[2] = 1 # MSG_ID para hora
        packet[3] = now.year % 100
        packet[4] = now.month
        packet[5] = now.day
        packet[6] = now.hour
        packet[7] = now.minute
        packet[8] = now.second
        device.write(packet)

    def _process_web_commands(self, device):
        """Revisa si hay cambios de frecuencia o configuración en la DB."""
        from devices.models import DeviceCommand

        # Obtener todos los comandos pendientes
        pending_commands = DeviceCommand.objects.filter(executed=False)

        if pending_commands.exists():
            self.stdout.write(f"🔍 Encontrados {pending_commands.count()} comandos pendientes...")

        for cmd in pending_commands:
            self.stdout.write(f"  -> Procesando CMD ID:{cmd.id} Tipo:{cmd.command_type}")

            if cmd.command_type == 'SET_CONFIG':
                payload = cmd.payload
                packet = [0]*64
                packet[1] = int(cmd.device_id or 0) # ID del dispositivo
                packet[2] = 2  # MSG_ID_CONFIG

                power = max(0, min(1, int(payload.get('power', 1))))
                freq = max(1, min(3600, int(payload.get('freq', 2))))
                cant = max(1, min(255, int(payload.get('cant', 1))))

                packet[3] = power
                packet[4] = (freq >> 8) & 0xFF
                packet[5] = freq & 0xFF
                packet[6] = (cant >> 8) & 0xFF
                packet[7] = cant & 0xFF

                try:
                    self.stdout.write(f"     Enviando paquete HID: Power={power}, Freq={freq}, Cant={cant}")
                    device.write(packet)
                    cmd.executed = True
                    cmd.save()
                    self.stdout.write(self.style.SUCCESS(f"     ✅ Device#{cmd.device_id}: Freq={freq}s, Power={power}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"     ❌ Error enviando comando a Device#{cmd.device_id}: {e}"))
            else:
                self.stdout.write(f"     ⚠️ Tipo de comando desconocido o no manejado: {cmd.command_type}")