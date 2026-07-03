-- Migracion 003: estatus de proyecto y contrato

ALTER TABLE proyectos
    ADD COLUMN estatus_proyecto VARCHAR(40) NOT NULL DEFAULT 'Planeacion';

ALTER TABLE contratos
    ADD COLUMN estatus_contrato VARCHAR(40) NOT NULL DEFAULT 'En ejecucion';
