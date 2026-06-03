class SensorsRouter:
    """
    Router para dirigir el modelo SensorReading a la base de datos 'sensors'
    y mantener el resto (Device, DeviceCommand, Users) en 'default'.
    """
    def db_for_read(self, model, **hints):
        if model._meta.model_name == 'sensorreading':
            return 'sensors'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.model_name == 'sensorreading':
            return 'sensors'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Permite relaciones lógicas aunque no haya integridad referencial física
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name == 'sensorreading':
            return db == 'sensors'
        return db == 'default'