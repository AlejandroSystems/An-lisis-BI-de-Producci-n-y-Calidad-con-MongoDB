# dashboard/app.py
# Objetivo:
# Crear un dashboard web local usando Flask.
# El dashboard consulta MongoDB y muestra indicadores BI de producción,
# calidad, merma y pérdida económica.

from flask import Flask, render_template
from pymongo import MongoClient


# ============================
# 1. CONFIGURACIÓN GENERAL
# ============================

app = Flask(__name__)

MONGO_URI = "mongodb://localhost:27017/"
NOMBRE_BD = "bi_produccion_calidad"
NOMBRE_COLECCION = "reporte_erp_produccion"


# ============================
# 2. CONEXIÓN A MONGODB
# ============================

cliente = MongoClient(MONGO_URI)
db = cliente[NOMBRE_BD]
coleccion = db[NOMBRE_COLECCION]


# ============================
# 3. FUNCIONES AUXILIARES
# ============================

def obtener_primero(lista, campo, default=0):
    """
    Devuelve el primer valor de una lista de agregación.
    Si no existe, devuelve un valor por defecto.
    """
    if lista and campo in lista[0]:
        return lista[0][campo]
    return default


def formato_soles(valor):
    """
    Formatea un número como moneda peruana.
    """
    return f"S/ {valor:,.2f}"


def formato_kg(valor):
    """
    Formatea un número como kilogramos.
    """
    return f"{valor:,.2f} KG"


def formato_porcentaje(valor):
    """
    Formatea un valor decimal como porcentaje.
    """
    return f"{valor:.2%}"


# ============================
# 4. RUTA PRINCIPAL DASHBOARD
# ============================

@app.route("/")
def dashboard():

    # ============================
    # KPIs generales
    # ============================

    total_registros = coleccion.count_documents({"estado_registro": "ACTIVO"})

    total_aprobados = coleccion.count_documents({
        "estado_registro": "ACTIVO",
        "calidad.estado_calidad": "Aprobado"
    })

    total_observados = coleccion.count_documents({
        "estado_registro": "ACTIVO",
        "calidad.estado_calidad": "Observado"
    })

    total_rechazados = coleccion.count_documents({
        "estado_registro": "ACTIVO",
        "calidad.estado_calidad": "Rechazado"
    })

    tasa_rechazo = total_rechazados / total_registros if total_registros else 0

    resumen = list(coleccion.aggregate([
        {"$match": {"estado_registro": "ACTIVO"}},
        {"$group": {
            "_id": None,
            "produccion_total": {"$sum": "$produccion.kg_producidos"},
            "merma_total": {"$sum": "$produccion.kg_merma"},
            "perdida_total": {"$sum": "$economico.perdida_estimada"}
        }}
    ]))

    produccion_total = obtener_primero(resumen, "produccion_total")
    merma_total = obtener_primero(resumen, "merma_total")
    perdida_total = obtener_primero(resumen, "perdida_total")
    porcentaje_merma = merma_total / produccion_total if produccion_total else 0

    # ============================
    # Pérdida por producto
    # ============================

    perdida_por_producto = list(coleccion.aggregate([
        {"$match": {"estado_registro": "ACTIVO"}},
        {"$group": {
            "_id": "$producto",
            "perdida_total": {"$sum": "$economico.perdida_estimada"},
            "kg_merma": {"$sum": "$produccion.kg_merma"}
        }},
        {"$sort": {"perdida_total": -1}},
        {"$limit": 8}
    ]))

    productos_labels = [item["_id"] for item in perdida_por_producto]
    productos_valores = [round(item["perdida_total"], 2) for item in perdida_por_producto]

    # ============================
    # Pérdida por área
    # ============================

    perdida_por_area = list(coleccion.aggregate([
        {"$match": {"estado_registro": "ACTIVO"}},
        {"$group": {
            "_id": "$area",
            "perdida_total": {"$sum": "$economico.perdida_estimada"},
            "kg_merma": {"$sum": "$produccion.kg_merma"},
            "rechazos": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$calidad.estado_calidad", "Rechazado"]},
                        1,
                        0
                    ]
                }
            }
        }},
        {"$sort": {"perdida_total": -1}}
    ]))

    areas_labels = [item["_id"] for item in perdida_por_area]
    areas_valores = [round(item["perdida_total"], 2) for item in perdida_por_area]

    # ============================
    # Calidad por estado
    # ============================

    calidad_por_estado = list(coleccion.aggregate([
        {"$match": {"estado_registro": "ACTIVO"}},
        {"$group": {
            "_id": "$calidad.estado_calidad",
            "cantidad": {"$sum": 1}
        }},
        {"$sort": {"cantidad": -1}}
    ]))

    calidad_labels = [item["_id"] for item in calidad_por_estado]
    calidad_valores = [item["cantidad"] for item in calidad_por_estado]

    # ============================
    # Pérdida por turno
    # ============================

    perdida_por_turno = list(coleccion.aggregate([
        {"$match": {"estado_registro": "ACTIVO"}},
        {"$group": {
            "_id": "$turno",
            "perdida_total": {"$sum": "$economico.perdida_estimada"},
            "kg_merma": {"$sum": "$produccion.kg_merma"},
            "rechazos": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$calidad.estado_calidad", "Rechazado"]},
                        1,
                        0
                    ]
                }
            }
        }},
        {"$sort": {"perdida_total": -1}}
    ]))

    turnos_labels = [item["_id"] for item in perdida_por_turno]
    turnos_valores = [round(item["perdida_total"], 2) for item in perdida_por_turno]

    # ============================
    # Top 10 rechazos con mayor impacto
    # ============================

    top_rechazos = list(coleccion.find(
        {
            "estado_registro": "ACTIVO",
            "calidad.estado_calidad": "Rechazado"
        },
        {
            "_id": 0,
            "id_registro": 1,
            "producto": 1,
            "area": 1,
            "turno": 1,
            "lote": 1,
            "produccion.kg_merma": 1,
            "economico.perdida_estimada": 1
        }
    ).sort("economico.perdida_estimada", -1).limit(10))

    # Preparar tabla
    tabla_rechazos = []

    for item in top_rechazos:
        produccion = item.get("produccion", {})
        economico = item.get("economico", {})

        tabla_rechazos.append({
            "id_registro": item.get("id_registro"),
            "producto": item.get("producto"),
            "area": item.get("area"),
            "turno": item.get("turno"),
            "lote": item.get("lote"),
            "kg_merma": formato_kg(produccion.get("kg_merma", 0)),
            "perdida": formato_soles(economico.get("perdida_estimada", 0))
        })

    # ============================
    # Escenarios de ahorro
    # ============================

    ahorro_10 = perdida_total * 0.10
    ahorro_15 = perdida_total * 0.15
    ahorro_20 = perdida_total * 0.20

    # ============================
    # Enviar datos al HTML
    # ============================

    return render_template(
        "dashboard.html",

        total_registros=total_registros,
        produccion_total=formato_kg(produccion_total),
        merma_total=formato_kg(merma_total),
        porcentaje_merma=formato_porcentaje(porcentaje_merma),
        perdida_total=formato_soles(perdida_total),
        tasa_rechazo=formato_porcentaje(tasa_rechazo),

        total_aprobados=total_aprobados,
        total_observados=total_observados,
        total_rechazados=total_rechazados,

        productos_labels=productos_labels,
        productos_valores=productos_valores,

        areas_labels=areas_labels,
        areas_valores=areas_valores,

        calidad_labels=calidad_labels,
        calidad_valores=calidad_valores,

        turnos_labels=turnos_labels,
        turnos_valores=turnos_valores,

        tabla_rechazos=tabla_rechazos,

        ahorro_10=formato_soles(ahorro_10),
        ahorro_15=formato_soles(ahorro_15),
        ahorro_20=formato_soles(ahorro_20)
    )


# ============================
# 5. EJECUCIÓN DEL SERVIDOR
# ============================

if __name__ == "__main__":
    app.run(debug=True)