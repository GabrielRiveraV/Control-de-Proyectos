-- Migracion 005: bitacora formal de observaciones
-- Si la tabla observaciones no existe, crearla con la estructura formal.
-- Si ya existia con estructura antigua, agregar las columnas faltantes manualmente.

CREATE TABLE IF NOT EXISTS observaciones (
    id_observacion INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NULL,
    id_contrato INT NULL,
    id_visita INT NULL,
    id_usuario_creador INT NULL,
    titulo VARCHAR(180) NULL,
    tipo VARCHAR(50) NULL,
    prioridad ENUM('Baja', 'Media', 'Alta', 'Critica') NOT NULL DEFAULT 'Media',
    estatus ENUM('Abierta', 'En seguimiento', 'Atendida', 'Solventada', 'Cerrada') NOT NULL DEFAULT 'Abierta',
    responsable VARCHAR(150) NULL,
    fecha_compromiso DATE NULL,
    fecha_cierre DATE NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    descripcion TEXT NULL,
    documento TEXT NULL,
    fecha DATE NULL,
    INDEX idx_observaciones_proyecto (id_proyecto),
    INDEX idx_observaciones_contrato (id_contrato),
    INDEX idx_observaciones_visita (id_visita),
    INDEX idx_observaciones_estatus (estatus),
    INDEX idx_observaciones_prioridad (prioridad)
);

-- Para bases con tabla antigua:
-- ALTER TABLE observaciones ADD COLUMN id_proyecto INT NULL AFTER id_observacion;
-- ALTER TABLE observaciones ADD COLUMN id_visita INT NULL AFTER id_contrato;
-- ALTER TABLE observaciones ADD COLUMN id_usuario_creador INT NULL AFTER id_visita;
-- ALTER TABLE observaciones ADD COLUMN titulo VARCHAR(180) NULL AFTER id_usuario_creador;
-- ALTER TABLE observaciones ADD COLUMN prioridad ENUM('Baja', 'Media', 'Alta', 'Critica') NOT NULL DEFAULT 'Media' AFTER tipo;
-- ALTER TABLE observaciones ADD COLUMN estatus ENUM('Abierta', 'En seguimiento', 'Atendida', 'Solventada', 'Cerrada') NOT NULL DEFAULT 'Abierta' AFTER prioridad;
-- ALTER TABLE observaciones ADD COLUMN responsable VARCHAR(150) NULL AFTER estatus;
-- ALTER TABLE observaciones ADD COLUMN fecha_compromiso DATE NULL AFTER responsable;
-- ALTER TABLE observaciones ADD COLUMN fecha_cierre DATE NULL AFTER fecha_compromiso;
-- ALTER TABLE observaciones ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER fecha_cierre;
-- ALTER TABLE observaciones ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;
