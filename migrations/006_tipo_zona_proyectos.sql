-- Migracion 006: clasificacion urbana/rural de proyectos

ALTER TABLE proyectos
    ADD COLUMN tipo_zona ENUM('Urbana', 'Rural') NOT NULL DEFAULT 'Urbana';
