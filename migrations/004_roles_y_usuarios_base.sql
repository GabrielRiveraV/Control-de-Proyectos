-- Migracion 004: ampliar roles para dashboard ejecutivo

ALTER TABLE usuarios
    MODIFY COLUMN rol ENUM('admin', 'supervisor', 'jefe') DEFAULT NULL;
