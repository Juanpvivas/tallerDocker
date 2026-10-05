import os

import psycopg
from fastapi import FastAPI, HTTPException


app = FastAPI(title="API del taller Docker")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db")
def consultar_base_de_datos():
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise HTTPException(
            status_code=503,
            detail="Falta configurar DB_PASSWORD",
        )

    try:
        with psycopg.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "appdb"),
            user=os.getenv("DB_USER", "postgres"),
            password=password,
            connect_timeout=5,
        ) as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT current_database(), CURRENT_TIMESTAMP"
                )
                nombre, fecha = cursor.fetchone()

        return {
            "status": "ok",
            "database": nombre,
            "server_time": fecha.isoformat(),
        }

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar PostgreSQL",
        )