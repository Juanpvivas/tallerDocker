# Requisitos de infraestructura

## Objetivo y alcance

Definir la infraestructura necesaria para desplegar una aplicación web con tres servicios: proxy inverso Nginx, API en Python y base de datos PostgreSQL. El taller se desarrolla en un Mac con Apple Silicon y Colima; los requisitos y las verificaciones se limitan a este entorno. Esta matriz corresponde a AA1 de la guía GFPI-F-135 y orienta la implementación y las verificaciones de AA2 a AA5.

Los criterios describen el resultado esperado del proyecto terminado; no indican que ya se haya implementado o probado. Las pruebas que crean, reinician o eliminan recursos se realizarán más adelante sobre el entorno de práctica.

## Matriz de requisitos

| Código | Requisito de infraestructura | Criterio de aceptación verificable |
|---|---|---|
| RI-01 | El proxy, la API y la base de datos se ejecutan en contenedores independientes. | `docker compose ps` muestra los servicios `proxy`, `api` y `db` en ejecución. |
| RI-02 | Solo el proxy publica un puerto en el equipo anfitrión: el puerto 8080 hacia el 80 del contenedor. | En `docker-compose.yml`, solo `proxy` tiene `ports`; `docker compose ps` muestra `8080->80` para el proxy y ningún puerto publicado para `api` o `db`. |
| RI-03 | Los datos de PostgreSQL se conservan al recrear los contenedores mediante un volumen nombrado. | En el entorno de práctica se inserta un registro, se ejecutan `docker compose down` sin `-v` y `docker compose up -d`, y se comprueba que el registro sigue disponible. El volumen aparece en `docker volume ls`. |
| RI-04 | Los tres servicios pueden operar con un presupuesto de 4 GB de RAM. | Con los tres servicios activos y durante las pruebas funcionales, la suma de sus consumos mostrados por `docker stats --no-stream` se mantiene por debajo de 4 GB y no se observan terminaciones por falta de memoria. |
| RI-05 | Las credenciales se suministran mediante variables de entorno y no se versionan. | La configuración de conexión recibe las credenciales desde el entorno; `.env` está excluido por `.gitignore`, `git ls-files .env` no devuelve resultados y `.env.example` contiene únicamente valores de ejemplo. No hay contraseñas reales en los archivos versionados. |
| RI-06 | Los servicios se comunican por una red privada de Compose y por sus nombres de servicio. | El archivo Compose define la red compartida; su inspección muestra los tres contenedores conectados. El proxy utiliza `api:8000` y la API utiliza `db:5432`, sin depender de direcciones IP fijas. |
| RI-07 | Nginx reenvía las solicitudes del cliente a la API. | Con la solución activa, `curl -i http://localhost:8080/health` devuelve HTTP 200 y la respuesta de salud de la API. |
| RI-08 | La API puede conectarse a PostgreSQL dentro de la red de contenedores. | Una solicitud a través del proxy al endpoint de consulta de la API devuelve HTTP 200 y datos obtenidos de PostgreSQL. La ruta del endpoint y el resultado esperado quedan documentados en el README. |
| RI-09 | La API espera a que PostgreSQL esté disponible. | Compose define un `healthcheck` de PostgreSQL con `pg_isready` y la dependencia de la API usa `condition: service_healthy`. Al iniciar la solución, `db` alcanza el estado `healthy` y la API responde a las pruebas. |
| RI-10 | Las imágenes base usan etiquetas explícitas y admiten la arquitectura del equipo. | Dockerfile y Compose usan las etiquetas indicadas en la tabla de componentes, sin `latest`. En el Mac, las imágenes descargadas reportan arquitectura `arm64` mediante `docker image inspect`. |
| RI-11 | La imagen de la API se construye por etapas y se ejecuta sin privilegios de administrador. | El Dockerfile contiene una etapa de construcción y otra de ejecución con `USER` no raíz. `docker compose exec api id -u` devuelve un valor distinto de `0`. |
| RI-12 | La solución se despliega con un único comando después de preparar sus variables de entorno. | Desde una copia limpia del repositorio, tras copiar y completar `.env.example` como `.env`, `docker compose up -d --build` inicia los tres servicios y la prueba de `/health` devuelve HTTP 200. |
| RI-13 | El equipo dispone de los recursos mínimos del taller. | Se registran en `docs/entorno.md` al menos 4 GB de RAM, 15 GB libres de disco y procesador Apple Silicon con arquitectura `arm64`. Se recomiendan 8 GB de RAM, 25 GB libres y al menos 2 núcleos. |
| RI-14 | El entorno cuenta con Docker Engine, el comando `docker compose` y conectividad para obtener las imágenes. | `docker --version`, `docker compose version` y `docker info` responden correctamente; la prueba `hello-world` finaliza con su mensaje de éxito. Las versiones y la ruta de instalación se registran en `docs/entorno.md`. |
| RI-OS-01 | En macOS, Docker Engine se ejecuta dentro de Colima. | El equipo usa macOS 13 o superior; `colima status` indica que está en ejecución con runtime Docker y `docker info` responde. Colima dispone de 2 CPU, 4 GB de RAM y 20 GB de disco como configuración de referencia del taller. |

**Excepción de práctica:** en AA2 la guía publica temporalmente PostgreSQL en el puerto 5432 para el ejercicio individual. RI-02 describe el despliegue final de AA4, donde la base de datos deja de publicar ese puerto.

## Componentes de hardware y software

### Servicios de la solución

Las siguientes imágenes y versiones son las referencias indicadas en la guía del taller.

| Componente | Imagen base | Puerto interno | Acceso y almacenamiento |
|---|---|---|---|
| Proxy inverso (`proxy`) | `nginx:1.30-alpine` | 80/TCP | Recibe solicitudes en el puerto 8080 del anfitrión y las reenvía a la API. |
| API backend (`api`) | `python:3.14-slim` | 8000/TCP | Recibe solicitudes del proxy y consulta `db:5432`; no publica puertos en el anfitrión. |
| Base de datos (`db`) | `postgres:18-alpine` | 5432/TCP | Accesible desde la API por la red privada; guarda los datos en un volumen nombrado. El destino del montaje debe corresponder a la versión de PostgreSQL usada. |

### Equipo local observado

Datos consultados el 30 de septiembre de 2026, sin modificar la configuración:

| Recurso | Valor observado |
|---|---|
| Sistema operativo | macOS 26.6.2 |
| Procesador | Apple M5 Pro, 15 núcleos |
| Arquitectura | `arm64` (Apple Silicon) |
| Memoria RAM | 24 GB |
| Espacio libre en el disco del proyecto | Aproximadamente 1,6 TB |
| Cliente Docker | 29.8.0 |
| Docker Compose | 5.5.1 |
| Colima | 0.10.3 |
| Recursos configurados para Colima | 2 CPU, 4 GB de RAM y 20 GB de disco; arquitectura `aarch64`, runtime Docker |
| Estado durante la revisión | Colima detenida; no se verificaron el servidor Docker, las imágenes ni los contenedores. |

El equipo cumple los requisitos de hardware y sistema operativo de la guía. Después de la revisión inicial, el aprendiz inició Colima y verificó el motor mediante `docker info` y `hello-world`; los resultados están registrados en [entorno.md](entorno.md). Compose responde con la versión 5.5.1; esta difiere de la referencia v2.x de la guía y se documenta tal como fue observada.

## Arquitectura prevista y evidencias pendientes

Flujo de solicitudes: **cliente → localhost:8080 → Nginx:80 → API:8000 → PostgreSQL:5432**. Los servicios se comunican por la red privada de Compose y PostgreSQL conserva los datos en un volumen nombrado.

- **AA1:** diagrama creado en [arquitectura.png](arquitectura.png) con los tres servicios, puertos, red y volumen.
- **AA2:** finalizada, con resultados registrados en [entorno.md](entorno.md), inventario en [imagenes.md](imagenes.md) y limpieza de los recursos de práctica confirmada por el aprendiz.
- **AA3:** completados los ejercicios de construcción y administración de la imagen; `/health` responde HTTP 200 y el proceso usa UID 1001. Etiquetado, inspección, comparación de tamaños y eliminación de la imagen de comparación registrados en [imagenes.md](imagenes.md).
- **AA4:** integración local verificada: tres servicios activos, API y PostgreSQL saludables, y respuestas HTTP 200 de `/health` y `/db` a través del proxy. Evidencias en [entorno.md](entorno.md). Persistencia del registro, estado de los tres servicios tras la recreación, resolución de nombres y aislamiento de PostgreSQL documentados en [pruebas.md](pruebas.md).
- **AA5:** pruebas locales registradas en [pruebas.md](pruebas.md); publicación manual, primera publicación automática en verde y descarga de la imagen automática con digest coincidente registradas en [imagenes.md](imagenes.md). Segunda ejecución en verde con caché verificada y propuesta documentada en [despliegue-automatizado.md](despliegue-automatizado.md). Pendientes: README, manual técnico y demás entregables de la guía, incluido el despliegue remoto según el alcance acordado con el instructor.

## Fuente

Guía de aprendizaje **GFPI-F-135, versión 04 — Despliegue de aplicaciones y servicios en contenedores Docker**, SENA, septiembre de 2026: requisitos técnicos (páginas 2–3), AA1 (páginas 6–7), AA2 para macOS (páginas 12–14) y criterios del repositorio (Anexo C, página 31).
