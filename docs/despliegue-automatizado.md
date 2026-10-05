# Publicación automática y propuesta de despliegue

## Estado actual

El proyecto se desarrolla y valida en macOS con Apple Silicon y Colima. GitHub Actions construye la imagen de la API y la publica en GHCR. El despliegue remoto descrito aquí es una propuesta: no está implementado ni se ha ejecutado contra un servidor.

Este documento corresponde al paso 4 de AA5 de la guía GFPI-F-135. Las evidencias se verificaron el **5 de octubre de 2026**.

## Evidencias de publicación

| Evidencia | Referencia |
|---|---|
| Repositorio | [Juanpvivas/tallerDocker](https://github.com/Juanpvivas/tallerDocker) |
| Flujo | [publicar-imagen.yml](../.github/workflows/publicar-imagen.yml) |
| Primera ejecución exitosa | [37367685686, intento 2](https://github.com/Juanpvivas/tallerDocker/actions/runs/37367685686/attempts/2) |
| Imagen descargada y verificada en el Mac | `ghcr.io/juanpvivas/tallerdocker:sha-62ea4a9` |
| Digest de esa imagen | `sha256:0b50b95cf2a58d8b4f9bb4a1adab09b1c22c6706c31ea807599c57bc6a4a1c9c` |
| Segunda ejecución exitosa | [37370587230](https://github.com/Juanpvivas/tallerDocker/actions/runs/37370587230) |
| Imagen de la segunda ejecución | `ghcr.io/juanpvivas/tallerdocker:sha-b548115` |
| Digest de la segunda imagen | `sha256:18eecc7e4c6fe390cb44b9a4a1538a14933c8ae5a4d27ccd4e11363e3002a703` |

## Qué hace el flujo

1. Un cambio enviado a `main` inicia el flujo. También puede iniciarse manualmente o al subir una etiqueta Git con formato `v*.*.*`.
2. GitHub proporciona un ejecutor temporal `ubuntu-24.04-arm` que descarga el código. El entorno de trabajo del aprendiz sigue siendo el Mac.
3. Buildx construye la imagen del Dockerfile para `linux/arm64`.
4. El flujo se autentica en GHCR mediante el `GITHUB_TOKEN` temporal y el permiso `packages: write`.
5. La acción de metadatos calcula las etiquetas: `latest` para la rama principal, `sha-…` asociada al commit y una versión semántica cuando corresponde a una etiqueta Git.
6. La imagen se publica y se exporta la caché para próximas construcciones.

El flujo actual no ejecuta pruebas funcionales de la API ni actualiza contenedores locales o remotos. Las pruebas del taller se han realizado por separado y están registradas en [pruebas.md](pruebas.md).

La primera corrida falló al publicar por falta de acceso al paquete (`permission_denied: read_package`). Se indicó habilitar el repositorio en `Manage Actions access` con rol `Write`; después de la corrección, la repetición terminó en verde.

La segunda ejecución reutilizó siete pasos de construcción. El paso de construir y publicar pasó de 24 a 8 segundos y la duración del trabajo de 43 a 36 segundos, excluyendo la cola. La comparación completa está en [imagenes.md](imagenes.md).

## Cómo continuaría hasta el servidor

La guía indica estudiar y documentar el trabajo de despliegue automático y activarlo únicamente si el instructor habilita un usuario y una carpeta por equipo. La actividad de transferencia solicita además un despliegue remoto guiado. Ninguno de esos despliegues está acreditado por las pruebas locales.

La propuesta para continuar es:

1. **Preparar el destino:** confirmar el servidor y directorio asignados, acceso SSH, Docker Compose, puerto autorizado y arquitectura. Las imágenes actuales son ARM64; si el destino es AMD64, habría que ampliar la construcción para esa arquitectura antes de usarlas allí.
2. **Preparar la configuración:** disponer en el servidor de Nginx, un Compose de despliegue y un `.env` privado. El servicio `api` de ese Compose usaría una imagen de GHCR por digest y omitiría `build:`. Se conservarían la red, el volumen de PostgreSQL y los healthchecks. Solo el proxy publicaría el puerto asignado según las instrucciones de acceso del servidor.
3. **Validar antes de publicar:** añadir pruebas funcionales al flujo para impedir que una imagen que no responda correctamente avance a despliegue.
4. **Seleccionar la imagen exacta:** pasar al trabajo de despliegue el digest producido por el trabajo de construcción. No bastaría con dejar una etiqueta fija antigua en el Compose del servidor.
5. **Desplegar después de publicar:** un trabajo dependiente de `construir-y-publicar`, limitado a `main`, se conectaría por SSH al directorio asignado. Actualizaría la referencia de la API, descargaría la imagen y recrearía los servicios necesarios conservando el volumen.
6. **Verificar:** comprobar servicios saludables y respuestas satisfactorias de `/health` y `/db` a través del proxy. Solo después se consideraría completado el despliegue.

Referencia exacta de la segunda imagen, disponible para una futura prueba:

```text
ghcr.io/juanpvivas/tallerdocker@sha256:18eecc7e4c6fe390cb44b9a4a1538a14933c8ae5a4d27ccd4e11363e3002a703
```

Una etiqueta `sha-…` ayuda a relacionar imagen y commit, pero técnicamente puede sobrescribirse. El digest identifica el contenido exacto. La configuración local actual sigue usando `build: .` y no se ha convertido en un Compose de despliegue remoto.

## Configuración y secretos necesarios

| Elemento | Uso y ubicación propuesta |
|---|---|
| `SERVIDOR_HOST` | Dirección del servidor asignado; configuración de Actions. |
| `SERVIDOR_USUARIO` | Usuario SSH autorizado; configuración de Actions. |
| `SERVIDOR_SSH_KEY` | Clave privada de acceso; secreto del entorno de despliegue en GitHub, nunca en archivos versionados. |
| Clave pública del servidor SSH | Verificarla con el instructor y registrarla en `known_hosts` del trabajo para reconocer el servidor correcto. |
| Directorio y puerto asignados | Configuración específica del equipo, definida antes de activar el trabajo remoto. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Configuración del servicio en el `.env` privado del servidor; no forma parte de la imagen publicada. |
| Acceso de lectura a GHCR | Si el paquete es privado, configurar una credencial con `read:packages` en el servidor sin imprimirla en los registros. La visibilidad del paquete aún debe comprobarse. |

El token personal utilizado para publicar manualmente no se copia al flujo: la publicación automática ya usa `GITHUB_TOKEN`. El acceso SSH solo se configuraría cuando exista un destino autorizado.

## Cómo revertir un despliegue fallido

Antes de actualizar, guardar la referencia por digest de la última versión comprobada. Si la nueva versión no supera las verificaciones:

1. Restaurar en la configuración del servidor el digest anterior de la API.
2. Descargar esa imagen y recrear la API con Compose, sin reconstruirla.
3. Verificar de nuevo los healthchecks, el acceso mediante Nginx y la consulta a PostgreSQL. Comprobar también que el proxy alcance la instancia recreada.
4. Registrar el fallo, la versión retirada y la versión restaurada.

El volumen de PostgreSQL debe conservarse: no utilizar `down -v` en este procedimiento. Volver a una imagen anterior no revierte cambios de datos o de esquema; esos cambios requerirían una estrategia compatible de migración y copias de seguridad. El código actual solo realiza una consulta de lectura desde `/db`.

## Pendientes

- README y manual técnico preparados para el entorno macOS acordado; falta incorporarlos al repositorio remoto.
- Confirmar con el instructor el alcance y acceso de la actividad de transferencia remota.
- Si se habilita ese destino, implementar y probar su despliegue; aún no se han creado secretos ni un trabajo remoto.
- Completar las evidencias finales, propuesta de escalamiento y video solicitados por la guía.
