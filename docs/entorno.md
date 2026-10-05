# Entorno de trabajo y verificación de Docker

## Alcance y fecha

Evidencia de AA2 y de la integración local de AA4 de la guía GFPI-F-135. El taller se desarrolla en un Mac con Apple Silicon mediante la ruta **2C: macOS con Colima**.

Fecha de verificación: **30 de septiembre de 2026**. Los datos del equipo provienen de la revisión local y los resultados de ejecución provienen de las salidas de terminal compartidas por el aprendiz. Este documento registra esas observaciones; no representa una nueva ejecución de las pruebas.

## Equipo y recursos

| Recurso | Valor observado |
|---|---|
| Sistema operativo anfitrión | macOS 26.6.2 |
| Procesador | Apple M5 Pro, 15 núcleos |
| Arquitectura del Mac | `arm64` |
| RAM del Mac | 24 GB |
| Espacio libre del disco del proyecto | Aproximadamente 1,6 TB durante la revisión inicial |
| Colima | 0.10.3 |
| Recursos configurados para Colima | 2 CPU, 4 GB de RAM y 20 GB de disco |
| Recursos reportados por Docker Engine | 2 CPU y 3.813 GiB de memoria |

El Mac cumple los mínimos de hardware y sistema operativo del taller. La memoria reportada por el motor corresponde al entorno virtual de Colima, no a los 24 GB totales del Mac.

## Ruta de instalación y configuración observada

Las herramientas ya estaban instaladas al comenzar la revisión; no se dispone del registro de su instalación original.

- Cliente Docker disponible en `/opt/homebrew/bin/docker`.
- Colima disponible en `/opt/homebrew/bin/colima`.
- Plugin Compose disponible en `/opt/homebrew/lib/docker/cli-plugins/docker-compose`.
- Contexto Docker activo: `colima`.
- Colima utiliza `macOS Virtualization.Framework`, arquitectura `aarch64`, runtime `docker` y montaje `virtiofs`.
- El servidor Docker se ejecuta en la máquina virtual administrada por Colima, que reporta Ubuntu 24.04.4 LTS y kernel `6.8.0-117-generic`. Esto forma parte del entorno de Colima usado desde macOS.

## Verificación del motor

Al inicio Colima estaba detenida. El aprendiz ejecutó `colima start`, que finalizó con `done`, y comprobó lo siguiente:

| Comando | Resultado observado | Estado |
|---|---|---|
| `colima status` | `colima is running using macOS Virtualization.Framework`; runtime `docker`, arquitectura `aarch64` | Correcto |
| `docker --version` | `Docker version 29.8.0, build 88096ef005` | Correcto |
| `docker compose version` | `Docker Compose version 5.5.1` | Comando disponible |
| `docker info` | Contexto `colima`, servidor 29.5.2, arquitectura `aarch64`, 2 CPU, 3.813 GiB de memoria | Comunicación con el servidor correcta |
| `docker run --rm hello-world` | `Hello from Docker!` | Ejecución de un contenedor confirmada |

El cliente Docker (29.8.0) y el servidor (29.5.2) reportan versiones distintas; la comunicación y la prueba de ejecución fueron satisfactorias. Compose reporta 5.5.1, que difiere de la referencia v2.x de la guía. En esta etapa se verificó su disponibilidad; el despliegue mediante Compose se probará en AA4.

## Práctica de PostgreSQL

Se utilizó este comando para crear el servicio y su volumen de práctica. La contraseña que aparece es el valor de ejemplo del taller:

```bash
docker run -d --name db-app \
  -e POSTGRES_PASSWORD=claveAdmin123 \
  -e POSTGRES_DB=appdb \
  -p 127.0.0.1:5432:5432 \
  -v pgdata-practica:/var/lib/postgresql \
  postgres:18-alpine \
  -c shared_buffers=32MB \
  -c max_connections=20
```

| Verificación | Evidencia compartida |
|---|---|
| `docker ps --filter name=db-app` | Contenedor `db-app`, imagen `postgres:18-alpine`, estado `Up`, puerto `127.0.0.1:5432->5432/tcp` |
| `docker logs --tail 20 db-app` | PostgreSQL 18.6; mensaje final `database system is ready to accept connections` |
| `docker exec db-app pg_isready -U postgres -d appdb` | `/var/run/postgresql:5432 - accepting connections` |
| `docker volume ls` | Volumen `pgdata-practica`, controlador `local` |

**Ajuste a la guía:** la inspección de la imagen mostró `PGDATA=/var/lib/postgresql/18/docker`. Para PostgreSQL 18 se montó el volumen en `/var/lib/postgresql`, siguiendo la [documentación oficial de Docker](https://docs.docker.com/guides/postgresql/networking-and-connectivity/). La guía del taller propone `/var/lib/postgresql/data`; ese destino se corrigió para esta versión.

El puerto se publicó en `127.0.0.1` para acceder desde el Mac. En el despliegue final de AA4, PostgreSQL quedará sin puertos publicados, conforme a RI-02.

Los registros muestran un apagado durante la inicialización seguido del arranque definitivo satisfactorio. La creación del volumen y la disponibilidad del servicio quedaron verificadas. Aún no se ha probado que un registro se conserve después de recrear el contenedor.

## Práctica de Nginx

Comando utilizado:

```bash
docker run -d --name web \
  -p 127.0.0.1:8080:80 \
  nginx:1.30-alpine
```

| Verificación | Evidencia compartida |
|---|---|
| `docker ps --filter name=web` | Contenedor `web`, imagen `nginx:1.30-alpine`, estado `Up`, puerto `127.0.0.1:8080->80/tcp` |
| `curl -i http://localhost:8080` | `HTTP/1.1 200 OK`, cabecera `Server: nginx/1.30.5`, contenido HTML con `Welcome to nginx!` |

En la práctica de AA2, Nginx sirvió correctamente su página de bienvenida. La verificación posterior del enrutamiento hacia la API se registra en la sección de AA4 al final de este documento.

## Estado de cierre de AA2

- Verificados: inicio de Colima, comunicación con Docker Engine, disponibilidad de Compose y ejecución de `hello-world`.
- Verificados: descarga de imágenes de PostgreSQL y Nginx, inspección de PostgreSQL y funcionamiento de ambos servicios de práctica.
- Registradas las imágenes y sus tamaños en [imagenes.md](imagenes.md).
- **Limpieza realizada según confirmación del aprendiz:** eliminación de los contenedores `web` y `db-app` y del volumen `pgdata-practica`. No se adjuntó una salida de terminal posterior a la limpieza.
- **AA2 finalizada:** verificaciones y documentación registradas; limpieza confirmada por el aprendiz.
- La prueba posterior de persistencia al recrear contenedores se registra en [pruebas.md](pruebas.md).

Antes de estas prácticas se observaron dos contenedores antiguos detenidos con `Exited (1)` durante comandos de instalación de dependencias. Su causa no se investigó y no impidieron las verificaciones posteriores.

## AA4: integración local con Compose

Resultados compartidos por el aprendiz el **5 de octubre de 2026**, después de iniciar la solución con Compose:

| Servicio | Contenedor | Imagen | Estado observado | Puertos mostrados |
|---|---|---|---|---|
| `api` | `docker-api-1` | `api-app:1.0.0` | Up (healthy) | `8000/tcp`, sin publicación en el anfitrión |
| `db` | `docker-db-1` | `postgres:18-alpine` | Up (healthy) | `5432/tcp`, sin publicación en el anfitrión |
| `proxy` | `docker-proxy-1` | `nginx:1.30-alpine` | Up | `127.0.0.1:8080->80/tcp` |

Pruebas realizadas desde el Mac:

| Comando | Resultado |
|---|---|
| `curl -i http://localhost:8080/health` | HTTP 200, cabecera `Server: nginx/1.30.5`, cuerpo `{"status":"ok"}` |
| `curl -i http://localhost:8080/db` | HTTP 200, cabecera `Server: nginx/1.30.5`, cuerpo `{"status":"ok","database":"appdb","server_time":"2026-10-05T19:22:41.179087+00:00"}` |

Estos resultados confirman el recorrido cliente → Nginx → API y la consulta de la API a PostgreSQL. La salida de Compose confirma que solo el proxy publica un puerto entre los tres servicios del proyecto.

Persistencia verificada según el ejercicio seguido por el aprendiz: después de recrear los contenedores, la consulta devolvió el registro de `prueba_persistencia` insertado previamente. La evidencia y los límites de la comprobación se registran en [pruebas.md](pruebas.md).

También se verificaron los tres servicios activos después de recrearlos, la resolución de `db` desde la API y la ausencia de puertos publicados para PostgreSQL, con rechazo de la conexión a `127.0.0.1:5432` desde el Mac. Evidencias en [pruebas.md](pruebas.md). Queda pendiente el despliegue desde una copia limpia.
