# Manual técnico

## 1. Alcance y estado

Proyecto `Juanpvivas/tallerDocker`, guía SENA GFPI-F-135. Este manual describe la implementación local en **macOS con Apple Silicon y Colima**, sus verificaciones y una propuesta de evolución. Fecha de documentación: **5 de octubre de 2026**.

Se verificaron los tres servicios, consulta a PostgreSQL, persistencia, aislamiento, despliegue desde una copia del repositorio, publicación en GHCR y reutilización de caché en Actions. El despliegue remoto, la ejecución de pruebas dentro de Actions y el escalamiento no están implementados.

## 2. Arquitectura

![Arquitectura de despliegue](arquitectura.png)

```text
Cliente en el Mac
  → localhost:8080
  → proxy:80 (Nginx)
  → api:8000 (FastAPI y Uvicorn)
  → db:5432 (PostgreSQL)
  → volumen pgdata
```

Colima proporciona la máquina virtual donde Docker Engine ejecuta los contenedores. Los recursos configurados son 2 CPU, 4 GB de RAM y 20 GB de disco virtual. El Mac observado tiene 24 GB de RAM y arquitectura ARM64. Las versiones y comprobaciones están en [entorno.md](entorno.md).

| Servicio | Imagen/base | Puerto interno | Publicación en el Mac | Función |
|---|---|---|---|---|
| `proxy` | `nginx:1.30-alpine` | 80/TCP | `127.0.0.1:8080` | Reenvía solicitudes a `http://api:8000`. |
| `api` | `api-app:1.0.0`, construida desde `python:3.14-slim` | 8000/TCP | Ninguna | Atiende `/health` y `/db`. |
| `db` | `postgres:18-alpine` | 5432/TCP | Ninguna | Base de datos persistente. |

## 3. Archivos y construcción

| Archivo | Responsabilidad |
|---|---|
| `app/main.py` | API y consulta SQL de lectura. |
| `requirements.txt` | Dependencias: FastAPI, Uvicorn y Psycopg con binarios. |
| `Dockerfile` | Instala dependencias en una etapa y las copia a la imagen de ejecución. |
| `.dockerignore` | Excluye credenciales locales, Git y archivos innecesarios de la construcción. |
| `docker-compose.yml` | Define servicios, variables, dependencias de arranque, red y volumen. |
| `nginx/default.conf` | Proxy hacia la API y cabeceras de host e IP del cliente. |
| `.env.example` | Plantilla pública de configuración. |
| `.env` | Configuración privada del entorno; excluida de Git. |
| `.github/workflows/publicar-imagen.yml` | Construcción y publicación automática en GHCR. |
| `Dockerfile.single`, `requirements.compare.txt` | Comparación de una etapa con la imagen multi-etapa del taller. |

La imagen de ejecución usa `appuser`, UID 1001. Se comprobó que el proceso corre con ese UID. El código queda en `/app/app/main.py` y Uvicorn importa `app.main:app`. `EXPOSE 8000` describe el puerto interno; no lo publica en el anfitrión.

La comparación mostró 274 MB de uso en disco y 60,2 MB de contenido para ambas variantes, con la precisión de la salida de Docker. No se observó ahorro de tamaño por separar etapas en este caso.

**Límite de reproducibilidad:** `requirements.txt` no fija versiones y las etiquetas base pueden actualizarse. Una reconstrucción futura puede resolver dependencias distintas. `requirements.compare.txt` fijó versiones para el ejercicio de comparación, pero no es el archivo usado por el Dockerfile principal. Los digests registrados identifican las imágenes publicadas exactas.

## 4. Red y almacenamiento

Los tres servicios comparten `interna`, una red de tipo `bridge` creada por Compose. Se comunican por nombre de servicio, no por IP fija. La IP `172.18.0.2` fue una observación de la prueba y puede cambiar.

La red no tiene configurado `internal: true`; no se ha afirmado ni comprobado que bloquee tráfico saliente. El aislamiento evaluado consiste en que PostgreSQL y la API no publican puertos en el Mac. Solo el proxy publica `127.0.0.1:8080`, accesible localmente.

El volumen lógico `pgdata` se monta en `/var/lib/postgresql`. PostgreSQL 18 guarda sus datos en `/var/lib/postgresql/18/docker`, dentro de ese montaje. Compose suele anteponer el nombre del proyecto al volumen real; cambiar de carpeta o usar `-p` puede crear otro conjunto de recursos.

La prueba de persistencia conservó una fila de `prueba_persistencia` después de `down` y `up -d`. El volumen conserva datos entre recreaciones; no sustituye una copia de seguridad. No se verificó una restauración desde backup.

## 5. Variables de entorno

| Variable | Origen | Uso |
|---|---|---|
| `DB_NAME` | `.env` | Nombre de base; Compose lo pasa como `POSTGRES_DB` a PostgreSQL y `DB_NAME` a la API. |
| `DB_USER` | `.env` | Usuario; se pasa como `POSTGRES_USER` a PostgreSQL y `DB_USER` a la API. |
| `DB_PASSWORD` | `.env` | Contraseña común, requerida por Compose; se pasa como `POSTGRES_PASSWORD` a PostgreSQL. |
| `DB_HOST` | Compose: `db` | Nombre de servicio usado por la API. |
| `DB_PORT` | Compose: `5432` | Puerto de conexión de la API. |

Compose rechaza variables obligatorias ausentes o vacías. Las variables de inicialización de PostgreSQL se aplican al crear una base sobre un directorio de datos vacío: editar `.env` no cambia automáticamente credenciales de una base ya inicializada.

La práctica utiliza `postgres`, un usuario administrador. Antes de exponer una aplicación real, se debe asignar a la API un usuario con permisos limitados a sus operaciones.

## 6. Arranque y comprobaciones

La instalación completa para una copia nueva está en el [README](../README.md). Una vez preparadas las herramientas y `.env`, desde la raíz:

```bash
colima status
docker compose config --quiet
docker compose up -d --build
docker compose ps
curl -i http://localhost:8080/health
curl -i http://localhost:8080/db
```

Si Colima está detenida, iniciar con `colima start`. PostgreSQL se comprueba mediante `pg_isready`; la API espera a su estado saludable. Un healthcheck HTTP comprueba `/health`, y Nginx espera a que la API esté saludable antes de arrancar. Las comprobaciones se ejecutan cada 5 segundos, con timeout de 5 segundos, 10 reintentos y periodo inicial de 10 segundos.

`/health` no consulta la base. Por ello, la validación funcional completa incluye `/db`. Las dependencias de Compose coordinan el arranque; no reparan por sí solas una pérdida posterior de conexión. `restart: unless-stopped` reinicia procesos que terminan, pero un estado `unhealthy` por sí solo no garantiza su reinicio.

Para cambios de código, repetir `docker compose up -d --build`. Para detener y recrear conservando datos:

```bash
docker compose down
docker compose up -d
```

No agregar `-v` a `down` si se desea conservar el volumen. Para consultar los registros sin seguirlos indefinidamente:

```bash
docker compose logs --tail 50 api db proxy
```

## 7. Pruebas y diagnóstico

Las salidas y límites de las verificaciones están en [pruebas.md](pruebas.md):

- HTTP 200 en `/health` y `/db` a través de Nginx.
- Consulta de nombre `db` desde la API y resolución a una IP de la red.
- Registro conservado después de recrear los contenedores.
- Ningún puerto publicado para PostgreSQL y rechazo de conexión a `127.0.0.1:5432` desde el Mac.
- Despliegue desde otra copia de GitHub con un nombre de proyecto y volumen separados, en el mismo motor Docker.

| Síntoma | Comprobación y actuación |
|---|---|
| No conecta con Docker | Consultar `colima status`; iniciar Colima si está detenida. |
| Docker no reconoce Compose | Revisar el plugin y `cliPluginsExtraDirs` según el README. |
| Puerto 8080 ocupado | Revisar `docker ps` y `lsof -nP -iTCP:8080 -sTCP:LISTEN`; detener el despliegue de práctica que lo ocupa antes de iniciar otro. |
| API devuelve 503 en `/db` | Revisar estado y registros de `db` y `api`, nombres de variables y coincidencia de credenciales con la base existente. |
| Nginx devuelve 502 | Verificar que `api` responda y que `proxy_pass` apunte a `api:8000` en la misma red. |
| `docker compose port db 5432` devuelve `invalid IP:0` | No interpretarlo solo: inspeccionar `HostConfig.PortBindings` del contenedor y comprobar el acceso TCP desde el Mac. En la prueba se obtuvo `{}` y conexión rechazada. |
| Actions falla con `permission_denied: read_package` | Revisar el acceso del repositorio al paquete en GHCR: `Manage Actions access`, rol `Write`. |

No eliminar volúmenes para resolver errores de credenciales sin comprobar antes qué datos contienen.

## 8. Publicación y propuesta de despliegue

La publicación automática ya funciona para ARM64 mediante Actions. Las dos ejecuciones verificadas están en [imagenes.md](imagenes.md); la segunda reutilizó siete pasos de construcción. El flujo no contiene pruebas funcionales ni trabajo de despliegue.

El [documento de despliegue automatizado](despliegue-automatizado.md) explica cómo seleccionar una imagen por digest, autenticar el servidor, mantener la configuración privada, verificar el despliegue y volver a una versión anterior. Un servidor AMD64 requiere publicar previamente una variante compatible.

El paso de producción se mantiene como propuesta. La guía distingue este diseño de automatización de la actividad de transferencia remota; esta última queda pendiente de acordar con el instructor.

## 9. Propuesta de escalamiento

Esta propuesta breve corresponde a la actividad de transferencia; no describe cambios ya implementados.

### Diferencias entre local y remoto

En local, Colima proporciona el motor y el proxy escucha solo en el Mac. En un servidor hay que acordar directorio, arquitectura, usuario SSH, puerto, acceso de red y disponibilidad. Se consumiría la imagen de GHCR por digest, sin construirla en el servidor. La configuración sensible residiría en ese entorno. Para un servicio público se necesitarían dominio, HTTPS, controles de acceso, supervisión y copias de seguridad verificadas.

### Qué trasladar a la nube y por qué

| Componente | Propuesta | Beneficio y condición |
|---|---|---|
| API | Ejecutar réplicas en un servicio de contenedores cuando las métricas de tráfico lo justifiquen. | Repartir solicitudes y tolerar la pérdida de una instancia; limitar conexiones a la base y validar el reparto de carga. |
| Proxy | Utilizar un balanceador con HTTPS y comprobación de salud. | Centralizar el acceso, certificados y distribución hacia réplicas saludables. |
| PostgreSQL | Evaluar un servicio administrado con copias de seguridad y restauración probada. | Reducir tareas operativas; revisar costo, ubicación de datos, accesos y objetivos de recuperación. |
| Registros y métricas | Centralizar errores, latencia, CPU, memoria y conexiones. | Detectar saturación y decidir cuándo escalar con datos medidos. |

Antes de aumentar recursos, medir el comportamiento con carga representativa. No se ha realizado una prueba de carga ni se ha verificado el presupuesto de 4 GB con `docker stats`. Definir cuánto tiempo de caída y pérdida de datos sería aceptable antes de elegir redundancia y frecuencia de backups.

### Protección de datos personales

La demostración usa datos de prueba y una consulta de metadatos. Si la aplicación incorporara datos personales, se debería definir e informar la finalidad, obtener autorización cuando corresponda, atender los derechos del titular y restringir el acceso. La Ley 1581 de 2012 contempla principios de finalidad, libertad, seguridad y confidencialidad; artículos 4, 8 y 9. [Texto oficial](https://www.minsalud.gov.co/Normatividad_Nuevo/Ley%201581%20de%202012.pdf).

La propuesta técnica es usar datos ficticios en pruebas y videos, evitar datos personales y secretos en registros, aplicar permisos mínimos, cifrar comunicaciones y proteger las copias de seguridad. Antes de usar proveedores fuera del país, revisar las condiciones aplicables al tratamiento y a las transferencias o transmisiones de datos. Estas medidas propuestas no constituyen una validación de cumplimiento jurídico del proyecto.

## 10. Entrega pendiente

- Subir este manual y el README al repositorio.
- Acordar y realizar, si corresponde al alcance definido por el instructor, el despliegue remoto y registrar sus evidencias.
- Preparar la release final solicitada y el video de 3 a 5 minutos mostrando el despliegue, las rutas y la persistencia, sin exponer credenciales.
- Publicar el enlace del repositorio en el aula virtual.

No se han declarado completadas estas actividades ni las pruebas de consumo de recursos o restauración de backups.
