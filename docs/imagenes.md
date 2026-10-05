# Registro de imágenes Docker

## Alcance

Evidencias de AA2 y AA3 de la guía GFPI-F-135, a partir de las salidas de terminal compartidas por el aprendiz. El inventario inicial corresponde al **30 de septiembre de 2026**; la construcción y comparación de la API se registran el **5 de octubre de 2026**. Los tamaños son observaciones de cada práctica y pueden variar si las etiquetas se actualizan en el registry.

## Inventario observado en AA2

| Imagen y etiqueta | ID corto | DISK USAGE | CONTENT SIZE | Propósito |
|---|---|---|---|---|
| `postgres:18-alpine` | `77f585114c32` | 425 MB | 119 MB | Base de datos del proyecto; utilizada en AA2 mediante el contenedor `db-app`. |
| `nginx:1.30-alpine` | `0985e772fb9f` | 92.9 MB | 26.9 MB | Servidor web en AA2 mediante el contenedor `web`; proxy inverso previsto para AA4. |
| `python:3.14-slim` | `cad9a2c87176` | 217 MB | 49.2 MB | Base prevista para construir la imagen de la API en AA3. |
| `api-app-jp:1.0.0` | `5019fb958624` | 220 MB | 48.2 MB | Imagen local de un ejercicio anterior de la API. Su existencia está confirmada; su funcionamiento no se ha validado. |
| `hello-world:latest` | `5e2309035332` | 22.6 kB | 10.3 kB | Comprobación de que Docker puede ejecutar un contenedor; la prueba imprimió `Hello from Docker!`. |

Los encabezados `DISK USAGE` y `CONTENT SIZE` se conservan tal como los muestra `docker images`, para distinguir las dos medidas reportadas. Los valores no se han sumado para estimar el uso total de Docker.

Las imágenes de la solución utilizan etiquetas explícitas. `hello-world:latest` se empleó únicamente para la prueba de instalación indicada en la guía y no forma parte de los tres servicios del proyecto.

## Inspección de PostgreSQL

Comando ejecutado:

```bash
docker image inspect postgres:18-alpine | head -30
```

Datos observados:

| Campo | Valor |
|---|---|
| Etiqueta | `postgres:18-alpine` |
| ID completo | `sha256:77f585114c32fbca283dc835b0596f4e52b51b4c6662d7810b2f4084f60a1873` |
| RepoDigest | `postgres@sha256:77f585114c32fbca283dc835b0596f4e52b51b4c6662d7810b2f4084f60a1873` |
| Fecha de creación reportada | `2026-09-17T21:30:59.665677387Z` |
| Puerto declarado por la imagen | `5432/tcp` |
| Versión mayor | `PG_MAJOR=18` |
| Versión de PostgreSQL | `PG_VERSION=18.6` |
| Directorio de datos | `PGDATA=/var/lib/postgresql/18/docker` |
| Entrypoint | `docker-entrypoint.sh` |
| Comando predeterminado | `postgres` |

El puerto declarado en la imagen no lo publica por sí solo en el Mac; en esta práctica la publicación se configuró al crear el contenedor.

La salida se limitó a las primeras 30 líneas y no incluye el campo de arquitectura de la imagen. Los registros posteriores de PostgreSQL indican que se ejecuta como `aarch64`; no se han registrado inspecciones de arquitectura de todas las imágenes.

## Comprobaciones de ejecución

| Imagen | Resultado |
|---|---|
| `hello-world:latest` | Ejecución satisfactoria con `docker run --rm hello-world`. |
| `postgres:18-alpine` | `db-app` en estado `Up`; registros indican que está listo y `pg_isready` responde `accepting connections`. Volumen `pgdata-practica` creado. |
| `nginx:1.30-alpine` | `web` en estado `Up`; `http://localhost:8080` devuelve HTTP 200 y `Welcome to nginx!`. Cabecera del servidor: `nginx/1.30.5`. |
| `python:3.14-slim` | Imagen disponible; no se aportó una prueba independiente de ejecución. |
| `api-app-jp:1.0.0` | Imagen disponible; API pendiente de validar. |

Los comandos y resultados de los servicios están registrados en [entorno.md](entorno.md).

## Limpieza de práctica

**Realizada según confirmación del aprendiz:** se eliminaron los contenedores `web` y `db-app` y el volumen `pgdata-practica`. No se adjuntó una salida de terminal posterior a la limpieza. El inventario y las comprobaciones anteriores se conservan como evidencia de la práctica; no representan el estado actual de los contenedores. Las imágenes pueden conservarse para las siguientes actividades.

## AA3: construcción y comparación de la API

Resultados compartidos el **5 de octubre de 2026**:

| Imagen | ID corto | DISK USAGE | CONTENT SIZE | Construcción |
|---|---|---|---|---|
| `api-app:1.0.0` | `bd061140b63d` | 274 MB | 60.2 MB | Dockerfile multi-etapa del proyecto |
| `api-app:latest` | `bd061140b63d` | 274 MB | 60.2 MB | Etiqueta adicional de la misma imagen, creada como ejercicio |
| `api-app:single-stage` | `1ff80c076e93` | 274 MB | 60.2 MB | Dockerfile de una sola etapa para comparación |

La comparación se planteó con la misma base `python:3.14-slim`, la misma aplicación y las versiones de dependencias exportadas desde el contenedor funcional mediante `pip freeze` a `requirements.compare.txt`. La variante se construyó con `Dockerfile.single`.

**Resultado:** ambas construcciones muestran el mismo tamaño con la precisión de `docker images`. No se observa una reducción de tamaño por usar varias etapas en este ejercicio; no se midieron diferencias en bytes. Ambas variantes usan una base slim e instalan las dependencias sin caché, sin añadir compiladores. La separación por etapas resulta más útil para reducir tamaño cuando permite dejar herramientas o archivos de construcción fuera de la imagen final.

Las etiquetas `1.0.0` y `latest` comparten ID, por lo que no representan dos copias independientes. El proyecto conserva `1.0.0` como etiqueta explícita de ejecución.

### Inspección y ejecución

- `docker history api-app:1.0.0` muestra una capa de copia de dependencias de 46.4 MB, una copia de la aplicación de 20.5 kB y la instrucción `USER appuser`.
- `docker image inspect api-app:1.0.0 --format '{{.Config.User}}'` devuelve `appuser`.
- El contenedor `api-app` inició con Uvicorn y publicó `127.0.0.1:8000->8000/tcp`.
- `curl -i http://localhost:8000/health` devolvió HTTP 200 y `{"status":"ok"}`.
- `docker exec api-app id -u` devolvió `1001`, confirmando la ejecución sin usuario raíz.
- En AA3 se probó `/health`; posteriormente, en AA4, `/db` respondió HTTP 200 con la base `appdb` a través del proxy, según se registra en [entorno.md](entorno.md). No se ha probado la ejecución de la variante `single-stage`.

### Espacio de Docker antes de construir la variante

| Tipo | Total | Activos | Tamaño | Recuperable |
|---|---|---|---|---|
| Imágenes | 10 | 3 | 901.3 MB | 592.6 MB (65 %) |
| Contenedores | 3 | 1 | 20.71 MB | 20.7 MB (99 %) |
| Volúmenes locales | 0 | 0 | 0 B | 0 B |
| Caché de construcción | 0 | 0 | 0 B | 0 B |

Esta medición corresponde a la salida de `docker system df` previa a la construcción de `single-stage`, no al estado posterior.

### Eliminación de la imagen de comparación

Ejercicio completado según la salida compartida por el aprendiz: después de la limpieza, `docker images api-app` muestra únicamente `api-app:1.0.0` y `api-app:latest`, ambas con ID `bd061140b63d` y marca de uso `U`. La etiqueta `api-app:single-stage` ya no aparece.

Comandos del ejercicio:

```bash
docker rmi api-app:single-stage
docker images api-app
```

Se conservaron las etiquetas de la imagen del proyecto. No se midió el espacio liberado ni se repitió la prueba de salud después de esta limpieza. Las imágenes pueden compartir capas, por lo que eliminar una imagen no implica recuperar todo su tamaño mostrado.

## AA5: publicación manual en GHCR

El **5 de octubre de 2026**, el aprendiz compartió una publicación satisfactoria de la imagen:

- Imagen: `ghcr.io/juanpvivas/tallerdocker:1.0.0`.
- Digest reportado: `sha256:36fc91f544d96a4d11007dd07a7de741d3b0fdff485a68713ddfafb9b60319b7`.
- Salida final: `1.0.0: digest: sha256:36fc91f544d96a4d11007dd07a7de741d3b0fdff485a68713ddfafb9b60319b7 size: 2056`.
- Las capas indicaron `Layer already exists`; el registry ya disponía de ellas y no necesitó volver a transferirlas.
- El Dockerfile incluye `org.opencontainers.image.source=https://github.com/Juanpvivas/tallerDocker`, agregado en el commit `8f4d3da` y subido a `main`.

El valor `size: 2056` corresponde al manifiesto publicado, no al tamaño total de la imagen. El digest permite identificar el contenido publicado independientemente de cambios posteriores en la etiqueta.

La salida confirma el envío a GHCR. Quedan pendientes la prueba de descarga y comprobar la visibilidad y vinculación del paquete en GitHub. La primera publicación automática se verificó posteriormente y se registra a continuación.

## AA5: primera publicación automática verificada

El **5 de octubre de 2026** se consultaron directamente con GitHub CLI el estado y los registros de la [ejecución 37367685686](https://github.com/Juanpvivas/tallerDocker/actions/runs/37367685686), intento 2.

| Dato | Resultado |
|---|---|
| Flujo | `Publicar imagen` |
| Estado | `completed`, conclusión `success` |
| Commit construido | `62ea4a9b4c8db6c195807d25435552533953e649` |
| Plataforma de construcción | `linux/arm64` |
| Etiquetas publicadas | `ghcr.io/juanpvivas/tallerdocker:latest` y `ghcr.io/juanpvivas/tallerdocker:sha-62ea4a9` |
| Digest de ambas etiquetas en esta ejecución | `sha256:0b50b95cf2a58d8b4f9bb4a1adab09b1c22c6706c31ea807599c57bc6a4a1c9c` |
| Duración del trabajo | Aproximadamente 43 segundos, de 20:23:21 a 20:24:04 UTC, sin contar la cola |

Los registros muestran que la construcción, publicación y exportación de caché finalizaron correctamente. La etiqueta `latest` puede cambiar con futuras publicaciones; `sha-62ea4a9` identifica el commit usado para esta construcción. Para referenciar exactamente el contenido publicado se utiliza el digest.

El intento 1 construyó la imagen, pero GHCR rechazó su publicación con `denied: permission_denied: read_package`. Se indicó conceder al repositorio `Juanpvivas/tallerDocker` acceso `Write` en la sección `Manage Actions access` del paquete. Después de la corrección y repetición del flujo realizadas por el aprendiz, el intento 2 terminó correctamente.

La descarga de la imagen automática desde el Mac y la reutilización de caché en la segunda ejecución quedaron verificadas, como se detalla a continuación. El flujo actual construye y publica; no incluye pruebas funcionales ni despliegue automático en un servidor.

### Descarga de la imagen automática

El aprendiz ejecutó:

```bash
docker pull ghcr.io/juanpvivas/tallerdocker:sha-62ea4a9
```

La salida indicó `Status: Downloaded newer image` y el digest `sha256:0b50b95cf2a58d8b4f9bb4a1adab09b1c22c6706c31ea807599c57bc6a4a1c9c`, coincidente con el publicado por Actions. Queda confirmada la descarga desde GHCR al Mac. Esta prueba no ejecuta la imagen ni demuestra acceso anónimo, pues el cliente había iniciado sesión en GHCR.

### Segunda ejecución

El commit de documentación `b548115d329cba915bc8fa70fd3a47cab3db8d97` disparó la [ejecución 37370587230](https://github.com/Juanpvivas/tallerDocker/actions/runs/37370587230). Se verificó con GitHub CLI que terminó con estado `completed` y conclusión `success`.

| Medición | Primera ejecución exitosa (intento 2) | Segunda ejecución |
|---|---|---|
| Duración del trabajo, sin cola | 43 segundos | 36 segundos |
| Paso Construir y publicar | 24 segundos | 8 segundos |
| Caché de construcción | Exportada al finalizar | Importada desde `gha`; siete pasos (`#8` a `#14`) con resultado `CACHED` |

La segunda ejecución tuvo lugar de 20:45:23 a 20:45:59 UTC del 5 de octubre de 2026. El paso de construcción y publicación fue 16 segundos más corto, aproximadamente un 67 %. Los registros confirman la reutilización de caché; las duraciones también dependen de la preparación del ejecutor y de las transferencias. La espera en cola no está incluida en esta comparación.

Publicó `ghcr.io/juanpvivas/tallerdocker:latest` y `ghcr.io/juanpvivas/tallerdocker:sha-b548115`, ambas con digest `sha256:18eecc7e4c6fe390cb44b9a4a1538a14933c8ae5a4d27ccd4e11363e3002a703`. La descarga comprobada anteriormente sigue correspondiendo a `sha-62ea4a9`.
