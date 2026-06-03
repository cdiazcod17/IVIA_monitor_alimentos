from django.db import models
from django.conf import settings


class Device(models.Model):
    device_id = models.PositiveSmallIntegerField(unique=True)  # 1-10
    default_name = models.CharField(max_length=100)
    location = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='UserDevice',
        related_name='devices'
    )

    class Meta:
        db_table = 'devices'
        ordering = ['device_id']

    def __str__(self):
        return f'[{self.device_id}] {self.default_name}'


class UserDevice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_devices'
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='user_devices'
    )
    alias = models.CharField(max_length=100, blank=True)
    food_name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_devices'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'device'],
                name='unique_user_device'
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.device}'


class SensorReading(models.Model):
    device_id = models.PositiveSmallIntegerField()
    report_id = models.PositiveSmallIntegerField()
    sequence = models.PositiveIntegerField()
    timeData = models.TimeField()
    dateData = models.DateTimeField()
    temperature = models.IntegerField()  # Valor raw (ej: 2550 para 25.50°C)
    humidity = models.IntegerField()     # Valor raw
    pressure = models.IntegerField()
    co2 = models.IntegerField()
    weight = models.IntegerField()
    ethylene = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'sensor_readings'
        managed = True

    def __str__(self):
        return f'Lectura {self.device_id} - {self.dateData}'


class DeviceCommand(models.Model):
    device_id = models.PositiveSmallIntegerField()
    command_type = models.CharField(max_length=50)  # Ej: 'SET_CONFIG'
    payload = models.JSONField()                  # Ej: {"freq": 10, "power": 1}
    executed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_commands'
