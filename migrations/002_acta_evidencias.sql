-- Migracion 002: evidencias fotograficas y croquis para actas

CREATE TABLE IF NOT EXISTS acta_evidencias (
    id_evidencia INT AUTO_INCREMENT PRIMARY KEY,
    id_acta INT NOT NULL,
    tipo ENUM('foto', 'croquis') NOT NULL DEFAULT 'foto',
    titulo VARCHAR(180) NULL,
    descripcion TEXT NULL,
    nombre_original VARCHAR(255) NULL,
    ruta_archivo VARCHAR(255) NOT NULL,
    orden INT NOT NULL DEFAULT 1,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_acta_evidencias_acta FOREIGN KEY (id_acta) REFERENCES actas_visita(id_acta) ON DELETE CASCADE
);
