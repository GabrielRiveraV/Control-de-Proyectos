-- Migracion inicial: modulo Generacion de Actas
-- Ejecutar en la base de datos del sistema antes de usar /actas/expediente/<id_visita>.
-- Nota de roles: el modulo espera usuarios.rol = 'supervisor'. Si el ENUM actual no lo incluye,
-- ajustar manualmente el ENUM de usuarios antes de asignar supervisores.

CREATE TABLE IF NOT EXISTS actas_visita (
    id_acta INT AUTO_INCREMENT PRIMARY KEY,
    id_visita INT NOT NULL,
    id_usuario INT NOT NULL,
    fecha_acta DATE NULL,
    estado ENUM('borrador', 'finalizada') NOT NULL DEFAULT 'borrador',
    avance_programado DECIMAL(5,2) NULL,
    avance_fisico DECIMAL(5,2) NULL,
    situacion_obra VARCHAR(80) NULL,
    observacion_fisica TEXT NULL,
    notas TEXT NULL,
    elaborado_por VARCHAR(150) NULL,
    vo_bo VARCHAR(150) NULL,
    cargo_elabora VARCHAR(150) NULL,
    cargo_vo_bo VARCHAR(150) NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_acta_visita (id_visita),
    KEY idx_actas_usuario (id_usuario),
    CONSTRAINT fk_actas_visita_visita FOREIGN KEY (id_visita) REFERENCES visitas(id_visita) ON DELETE CASCADE,
    CONSTRAINT fk_actas_visita_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

CREATE TABLE IF NOT EXISTS acta_conceptos (
    id_concepto INT AUTO_INCREMENT PRIMARY KEY,
    id_acta INT NOT NULL,
    clave VARCHAR(50) NULL,
    concepto TEXT NOT NULL,
    unidad VARCHAR(30) NULL,
    importe DECIMAL(14,2) NULL,
    porcentaje_verificado DECIMAL(6,2) NULL,
    orden INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_acta_conceptos_acta FOREIGN KEY (id_acta) REFERENCES actas_visita(id_acta) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS acta_estimaciones (
    id_estimacion INT AUTO_INCREMENT PRIMARY KEY,
    id_acta INT NOT NULL,
    clave VARCHAR(50) NULL,
    concepto TEXT NOT NULL,
    unidad VARCHAR(30) NULL,
    cantidad_estimada DECIMAL(14,4) NULL,
    cantidad_verificada DECIMAL(14,4) NULL,
    precio_unitario DECIMAL(14,2) NULL,
    diferencia DECIMAL(14,4) NULL,
    importe DECIMAL(14,2) NULL,
    orden INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_acta_estimaciones_acta FOREIGN KEY (id_acta) REFERENCES actas_visita(id_acta) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS acta_tramos (
    id_tramo INT AUTO_INCREMENT PRIMARY KEY,
    id_acta INT NOT NULL,
    ubicacion VARCHAR(255) NOT NULL,
    tramo VARCHAR(255) NULL,
    volumen DECIMAL(14,2) NULL,
    unidad VARCHAR(30) NULL,
    orden INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_acta_tramos_acta FOREIGN KEY (id_acta) REFERENCES actas_visita(id_acta) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS acta_hallazgos (
    id_hallazgo INT AUTO_INCREMENT PRIMARY KEY,
    id_acta INT NOT NULL,
    descripcion TEXT NOT NULL,
    orden INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_acta_hallazgos_acta FOREIGN KEY (id_acta) REFERENCES actas_visita(id_acta) ON DELETE CASCADE
);
