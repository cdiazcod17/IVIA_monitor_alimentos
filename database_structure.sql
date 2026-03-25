

CREATE TABLE sensor_readings (
    id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    device_id      TINYINT UNSIGNED NOT NULL,
    report_id      TINYINT UNSIGNED NOT NULL,

    -- Control de secuencia y tiempo
    sequence       INT UNSIGNED NOT NULL,          -- contador incremental
    timeData       TIME NOT NULL,                  -- HAL_GetTick() en ms
    dateData       DATETIME NOT NULL,              -- fecha completa

    -- Sensores (almacenados con el factor de escala original del firmware)
    temperature    SMALLINT NOT NULL,              -- °C * 100  → divide /100 al leer
    humidity       SMALLINT UNSIGNED NOT NULL,     -- % * 100   → divide /100 al leer
    pressure       INT UNSIGNED NOT NULL,          -- Pa (sin escala)
    co2            SMALLINT UNSIGNED NOT NULL,     -- ppm
    weight         INT NOT NULL,                   -- gramos
    ethylene       INT NOT NULL,                   -- (int32_t ethylene)

    -- Timestamp automático para ordenación
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índices para rendimiento
CREATE INDEX idx_device_id ON sensor_readings(device_id);
CREATE INDEX idx_report_id ON sensor_readings(report_id);
CREATE INDEX idx_date_time ON sensor_readings(dateData, timeData);
CREATE INDEX idx_sequence ON sensor_readings(sequence);
CREATE INDEX idx_created_at ON sensor_readings(created_at);


INSERT INTO sensor_readings (
    report_id, device_id, sequence, timeData, dateData,
    temperature, humidity, pressure, co2, weight, ethylene
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
