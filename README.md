# Sistema de Control de Proyectos de Obra

Aplicacion web Flask para el control interno de proyectos, contratos, visitas, actas, observaciones y seguimiento ejecutivo de obras publicas municipales.

El proyecto esta orientado a uso gubernamental municipal, especificamente para el seguimiento de obras del Municipio de Centro, Tabasco, desde una perspectiva operativa y de supervision.

## Objetivo General

Centralizar la informacion de proyectos de obra, contratos, visitas de supervision, actas de visita, observaciones formales y tableros ejecutivos para facilitar el control, consulta, seguimiento y toma de decisiones del area.

## Funcionalidades Principales

- Registro y administracion de proyectos de obra.
- Clasificacion de proyectos por zona: `Urbana` o `Rural`.
- Registro y administracion de contratos.
- Expediente del contrato con informacion contractual ampliada.
- Carga y reemplazo de PDF de contrato.
- Registro de visitas de supervision.
- Carga de actas firmadas por visita.
- Modulo de generacion de actas de visita.
- Expediente del acta con conceptos, estimaciones, tramos, hallazgos, croquis y evidencias fotograficas.
- Bitacora formal de observaciones.
- Dashboard ejecutivo para jefatura y administracion.
- Auditoria de acciones.
- Control de acceso por roles.

## Roles Del Sistema

Actualmente el sistema maneja estos roles:

| Rol | Descripcion |
|---|---|
| `admin` | Control total del sistema. Puede crear, editar, eliminar, administrar contratos, ver auditoria y acceder al dashboard ejecutivo. |
| `jefe` | Perfil directivo o de jefatura. Puede consultar informacion ejecutiva, observaciones y seguimiento general. |
| `supervisor` | Perfil operativo. Puede registrar visitas, generar actas, subir actas firmadas y crear observaciones desde visitas. |

> Nota: En una fase futura se contempla limitar la visibilidad de supervisores por zona, por ejemplo supervisores rurales y supervisores urbanos.

## Estructura Del Proyecto

```text
C:\sistema_control
|-- app.py
|-- config.py
|-- database.py
|-- requirements.txt
|-- routes/
|   |-- auth.py
|   |-- proyectos.py
|   |-- contratos.py
|   |-- visitas.py
|   |-- actas.py
|   |-- observaciones.py
|   |-- dashboard.py
|   `-- permisos.py
|-- templates/
|   |-- index.html
|   |-- login.html
|   |-- dashboard_ejecutivo.html
|   |-- expediente_contrato.html
|   |-- expediente_acta.html
|   |-- acta_imprimir.html
|   |-- observaciones.html
|   |-- observacion_form.html
|   |-- observacion_detalle.html
|   |-- visitas.html
|   `-- visitas_proyecto.html
|-- static/
|   |-- img/
|   `-- uploads/
|-- migrations/
|   |-- 001_generacion_actas.sql
|   |-- 002_acta_evidencias.sql
|   |-- 003_estatus_proyecto_contrato.sql
|   |-- 004_roles_y_usuarios_base.sql
|   |-- 005_bitacora_observaciones.sql
|   `-- 006_tipo_zona_proyectos.sql
`-- utils/
    `-- auditoria.py
```

## Tecnologias

- Python
- Flask
- Flask-Login
- Flask-WTF / CSRFProtect
- MySQL
- mysql-connector-python
- Jinja2
- Bootstrap
- Chart.js

## Instalacion Local

1. Clonar o abrir la carpeta del proyecto:

```powershell
cd C:\sistema_control
```

2. Crear entorno virtual, si no existe:

```powershell
python -m venv venv
```

3. Activar entorno virtual:

```powershell
venv\Scripts\Activate.ps1
```

4. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

5. Crear archivo `.env` en la raiz del proyecto:

```env
SECRET_KEY=coloca_una_clave_segura
DB_HOST=localhost
DB_USER=usuario_mysql
DB_PASSWORD=password_mysql
DB_NAME=control_proyectos
```

> El archivo `.env` no debe subirse a Git. Ya esta incluido en `.gitignore`.

## Base De Datos

El sistema usa MySQL. La conexion se configura desde:

- [config.py](config.py)
- [database.py](database.py)

Las migraciones historicas estan en:

- [migrations/](migrations/)

### Migraciones Disponibles

| Archivo | Proposito |
|---|---|
| `001_generacion_actas.sql` | Crea tablas del modulo de generacion de actas. |
| `002_acta_evidencias.sql` | Agrega evidencias y croquis al expediente del acta. |
| `003_estatus_proyecto_contrato.sql` | Agrega estatus de proyecto y contrato. |
| `004_roles_y_usuarios_base.sql` | Amplia roles para incluir `jefe`. |
| `005_bitacora_observaciones.sql` | Define/amplia la bitacora formal de observaciones. |
| `006_tipo_zona_proyectos.sql` | Agrega clasificacion `Urbana` / `Rural` a proyectos. |

Las migraciones no usan actualmente un gestor automatico como Alembic o Flask-Migrate; se aplican manualmente sobre la base MySQL.

## Ejecucion

Con el entorno virtual activo:

```powershell
python app.py
```

La aplicacion se ejecuta en:

```text
http://0.0.0.0:5000
```

En red local, normalmente se accede mediante la IP del equipo servidor, por ejemplo:

```text
http://192.168.1.130:5000
```

## Rutas Principales

| Ruta | Descripcion |
|---|---|
| `/login` | Inicio de sesion. |
| `/` | Dashboard operativo principal y listado de proyectos. |
| `/nuevo_proyecto` | Alta de proyecto. |
| `/editar_proyecto/<id>` | Edicion de proyecto. |
| `/nuevo_contrato/<id_proyecto>` | Alta de contrato para un proyecto. |
| `/expediente_contrato/<id_contrato>` | Expediente ampliado del contrato. |
| `/visitas` | Historial general de visitas. |
| `/visitas_proyecto/<id_proyecto>` | Historial de visitas por proyecto. |
| `/nueva_visita/<id_proyecto>` | Registro de nueva visita. |
| `/actas/expediente/<id_visita>` | Expediente del acta de visita. |
| `/actas/imprimir/<id_visita>` | Vista imprimible del acta de visita. |
| `/observaciones/` | Bitacora formal de observaciones. |
| `/observaciones/nueva` | Nueva observacion manual o contextual. |
| `/dashboard/ejecutivo` | Dashboard ejecutivo para `admin` y `jefe`. |
| `/auditoria` | Auditoria de acciones del sistema. |

## Modulos Del Sistema

### Proyectos

El proyecto es la entidad base del sistema. Incluye:

- Nombre del proyecto.
- Programa/fuente.
- Unidad administrativa.
- Localidad.
- Zona: `Urbana` o `Rural`.
- Inversion autorizada.
- Ejercicio fiscal.
- Estatus del proyecto.

### Contratos

Cada proyecto puede tener un contrato asociado. El contrato incluye:

- Numero de contrato.
- Contratista.
- Fecha.
- Monto contratado.
- PDF del contrato.
- Estatus del contrato.
- Datos ampliados en expediente contractual.

### Visitas

Los supervisores pueden registrar visitas vinculadas a contratos/proyectos.

Cada visita puede incluir:

- Fecha.
- Supervisor.
- Residente de obra.
- Observaciones.
- Acta firmada cargada como archivo.

### Actas De Visita

El sistema cuenta con un modulo de generacion de actas a partir de una visita.

El expediente del acta puede contener:

- Datos generales.
- Conceptos de obra.
- Estimaciones.
- Tramos.
- Hallazgos.
- Croquis de ubicacion.
- Evidencias fotograficas.
- Firmas y cargos.

### Observaciones

La bitacora formal de observaciones usa una logica mixta:

- Siempre se relaciona con un proyecto.
- Puede relacionarse con un contrato.
- Puede nacer desde una visita.

Campos principales:

- Titulo.
- Descripcion.
- Tipo: fisica, documental, financiera, administrativa u otra.
- Prioridad: baja, media, alta o critica.
- Estatus: abierta, en seguimiento, atendida, solventada o cerrada.
- Responsable.
- Fecha compromiso.
- Fecha cierre.

### Dashboard Ejecutivo

Vista de consulta para `admin` y `jefe`.

Incluye:

- KPIs generales.
- Semaforo de contratos.
- Proyectos que requieren atencion.
- Observaciones abiertas, de alta prioridad, vencidas y solventadas.
- Graficas por estatus, programa y visitas.

## Archivos Subidos

Las rutas principales de carga son:

```text
static/uploads/actas
static/uploads/contratos
```

El limite de carga esta configurado en `config.py`:

```python
MAX_CONTENT_LENGTH = 10 * 1024 * 1024
```

Extensiones permitidas actualmente:

```python
pdf, xlsx, xls
```

## Seguridad Y Consideraciones

- El sistema usa `Flask-Login` para autenticacion.
- Las contrasenas se validan con hash de Werkzeug.
- Formularios protegidos con CSRF mediante `Flask-WTF`.
- `.env` esta excluido de Git.
- No subir credenciales reales al repositorio.
- Las rutas sensibles dependen del rol del usuario.

## Comandos Utiles Para Desarrollo

Validar sintaxis Python:

```powershell
venv\Scripts\python.exe -m compileall app.py routes utils
```

Listar rutas Flask:

```powershell
venv\Scripts\flask.exe --app app:app routes
```

Ver estado Git:

```powershell
git status --short
```

Revisar diferencias:

```powershell
git diff
```

## Notas Para Futuros Agentes

- Leer primero `app.py`, `routes/proyectos.py`, `routes/observaciones.py`, `routes/dashboard.py` y `config.py`.
- No asumir que todas las migraciones estan aplicadas; verificar columnas en MySQL antes de modificar rutas.
- El proyecto ya tiene historial de cambios no necesariamente comprometidos en Git.
- No revertir archivos sin confirmacion del usuario.
- Mantener los roles existentes: `admin`, `jefe`, `supervisor`.
- Para nuevas funcionalidades de permisos, usar decoradores en `routes/permisos.py`.
- La clasificacion urbana/rural vive en `proyectos.tipo_zona`.
- La bitacora formal vive en `observaciones`.
- El dashboard ejecutivo debe mantenerse sobrio, formal y de solo lectura.

## Pendientes Y Posibles Mejoras

- Definir permisos por zona para supervisores urbanos/rurales.
- Agregar evidencias a observaciones.
- Agregar comentarios o historial de seguimiento por observacion.
- Exportar dashboard ejecutivo a PDF.
- Agregar filtros por ejercicio fiscal, zona, programa y estatus.
- Normalizar/aplicar migraciones mediante herramienta formal.
- Mejorar limpieza de mojibake en templates antiguos.

