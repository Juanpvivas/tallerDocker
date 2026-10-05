# Pruebas de despliegue

Registro de validaciones de AA4 y AA5 del taller GFPI-F-135 en macOS con Colima. Fecha: **5 de octubre de 2026**. Las evidencias son salidas de terminal compartidas por el aprendiz; los estados pendientes no se consideran aprobados.

## Resumen

| Prueba | Estado | Evidencia |
|---|---|---|
| Tres servicios en ejecución | Verificada antes de la recreación | `docker compose ps` mostró `api`, `db` y `proxy` en ejecución; `api` y `db` saludables. |
| Proxy hacia la API | Verificada antes de la recreación | `/health` en el puerto 8080 devolvió HTTP 200 y `{"status":"ok"}`. |
| API hacia PostgreSQL | Verificada antes de la recreación | `/db` en el puerto 8080 devolvió HTTP 200, base `appdb` y hora del servidor. |
| Persistencia al recrear contenedores | Verificada según la secuencia seguida por el aprendiz | La consulta posterior devolvió el registro insertado antes de `docker compose down` y `docker compose up -d`. |
| Resolución explícita del nombre `db` | Verificada | La consulta desde la API devolvió `172.18.0.2`. |
| Aislamiento de PostgreSQL | Verificado para la publicación de puertos y el acceso local probado | `PortBindings` devuelve `{}` y la conexión TCP desde el Mac a `127.0.0.1:5432` fue rechazada. |
| Estado de los tres servicios después de recrearlos | Verificado | `api` y `db` aparecen Up (healthy), y `proxy` Up con `127.0.0.1:8080->80/tcp`. |
| Despliegue desde una copia limpia | Pendiente | Recrear contenedores en el proyecto existente no prueba este criterio. |

## Persistencia de datos

Se creó una tabla de práctica y se insertó un registro:

```sql
CREATE TABLE prueba_persistencia (
    id INTEGER PRIMARY KEY,
    mensaje TEXT NOT NULL
);

INSERT INTO prueba_persistencia (id, mensaje)
VALUES (1, 'Los datos sobreviven al recrear los contenedores');
```

La secuencia indicada al aprendiz fue:

```bash
docker compose down
docker compose up -d
docker compose ps
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM prueba_persistencia;"'
```

Se utilizó `down` sin `-v` para conservar el volumen. El aprendiz compartió este resultado de la consulta posterior:

```text
 id |                     mensaje
----+--------------------------------------------------
  1 | Los datos sobreviven al recrear los contenedores
```

**Resultado:** el registro permanece disponible después de la recreación indicada. Esto aporta evidencia de RI-03. No se adjuntaron las salidas de `down` y `up`; la secuencia se registra según el seguimiento del ejercicio por el aprendiz. Posteriormente se recibió la salida de `docker compose ps`, con los tres servicios activos.

Las evidencias de integración previas están en [entorno.md](entorno.md), y las de construcción de la API en [imagenes.md](imagenes.md).

## Red, aislamiento y estado después de la recreación

El aprendiz compartió estas verificaciones:

| Comando | Resultado |
|---|---|
| `docker compose ps` | `docker-api-1` y `docker-db-1` Up (healthy); `docker-proxy-1` Up. Solo el proxy publica `127.0.0.1:8080->80/tcp`. |
| `docker compose exec api python -c "import socket; print(socket.gethostbyname('db'))"` | `172.18.0.2` |
| `docker compose port db 5432` | `invalid IP:0`; salida ambigua, no utilizada por sí sola como evidencia de aislamiento. |
| `nc -vz -G 3 127.0.0.1 5432` | Conexión rechazada (`Connection refused`). |

Para aclarar la salida ambigua, se realizó una consulta adicional de solo lectura al contenedor:

```bash
docker inspect docker-db-1 --format '{{json .HostConfig.PortBindings}}'
```

Resultado observado directamente: `{}`. Esto confirma que el contenedor no tiene puertos publicados. No se determinó la causa exacta del mensaje `invalid IP:0`; no implica que PostgreSQL esté caído, pues el servicio está saludable y la consulta interna ya funcionó.

La dirección `172.18.0.2` es el valor observado durante la prueba y puede cambiar al recrear la red. La API debe seguir utilizando el nombre `db`.

Continúa pendiente la prueba de despliegue desde una copia limpia del repositorio.
