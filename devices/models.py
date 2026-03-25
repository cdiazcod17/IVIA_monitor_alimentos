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
