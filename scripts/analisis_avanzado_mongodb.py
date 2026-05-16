# analisis_avanzado_mongodb.py
# Objetivo:
# Realizar análisis BI avanzado desde MongoDB.
# Se evalúa merma, rechazo, pérdida económica estimada y acciones de mejora.

from pymongo import MongoClient


# ============================
# 1. CONFIGURACIÓN GENERAL
# ============================

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

def titulo(texto):
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


def obtener_primero(lista, campo, default=0):
    if lista and campo in lista[0]:
        return lista[0][campo]
    return default


# ============================
# 4. INDICADORES GENERALES
# ============================

titulo("1. INDICADORES GENERALES BI")

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

tasa_aprobacion = total_aprobados / total_registros if total_registros else 0
tasa_observacion = total_observados / total_registros if total_registros else 0
tasa_rechazo = total_rechazados / total_registros if total_registros else 0

print(f"Total de registros activos: {total_registros}")
print(f"Aprobados: {total_aprobados} | Tasa: {tasa_aprobacion:.2%}")
print(f"Observados: {total_observados} | Tasa: {tasa_observacion:.2%}")
print(f"Rechazados: {total_rechazados} | Tasa: {tasa_rechazo:.2%}")


# ============================
# 5. RESUMEN ECONÓMICO GENERAL
# ============================

titulo("2. RESUMEN ECONÓMICO GENERAL")

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

print(f"Producción total: {produccion_total:,.2f} KG")
print(f"Merma total: {merma_total:,.2f} KG")
print(f"Porcentaje de merma: {porcentaje_merma:.2%}")
print(f"Pérdida económica estimada: S/ {perdida_total:,.2f}")


# ============================
# 6. PÉRDIDA ECONÓMICA POR PRODUCTO
# ============================

titulo("3. PRODUCTOS CON MAYOR PÉRDIDA ECONÓMICA")

perdida_por_producto = list(coleccion.aggregate([
    {"$match": {"estado_registro": "ACTIVO"}},
    {"$group": {
        "_id": "$producto",
        "kg_merma": {"$sum": "$produccion.kg_merma"},
        "perdida_total": {"$sum": "$economico.perdida_estimada"},
        "registros": {"$sum": 1}
    }},
    {"$sort": {"perdida_total": -1}},
    {"$limit": 8}
]))

for item in perdida_por_producto:
    print(
        f"{item['_id']}: "
        f"Merma {item['kg_merma']:,.2f} KG | "
        f"Pérdida S/ {item['perdida_total']:,.2f} | "
        f"Registros: {item['registros']}"
    )


# ============================
# 7. PÉRDIDA ECONÓMICA POR ÁREA
# ============================

titulo("4. ÁREAS CON MAYOR PÉRDIDA ECONÓMICA")

perdida_por_area = list(coleccion.aggregate([
    {"$match": {"estado_registro": "ACTIVO"}},
    {"$group": {
        "_id": "$area",
        "kg_merma": {"$sum": "$produccion.kg_merma"},
        "perdida_total": {"$sum": "$economico.perdida_estimada"},
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

for item in perdida_por_area:
    print(
        f"{item['_id']}: "
        f"Pérdida S/ {item['perdida_total']:,.2f} | "
        f"Merma {item['kg_merma']:,.2f} KG | "
        f"Rechazos: {item['rechazos']}"
    )


# ============================
# 8. PÉRDIDA ECONÓMICA POR TURNO
# ============================

titulo("5. TURNOS CON MAYOR PÉRDIDA ECONÓMICA")

perdida_por_turno = list(coleccion.aggregate([
    {"$match": {"estado_registro": "ACTIVO"}},
    {"$group": {
        "_id": "$turno",
        "kg_merma": {"$sum": "$produccion.kg_merma"},
        "perdida_total": {"$sum": "$economico.perdida_estimada"},
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

for item in perdida_por_turno:
    print(
        f"Turno {item['_id']}: "
        f"Pérdida S/ {item['perdida_total']:,.2f} | "
        f"Merma {item['kg_merma']:,.2f} KG | "
        f"Rechazos: {item['rechazos']}"
    )


# ============================
# 9. RECHAZOS CON MAYOR IMPACTO ECONÓMICO
# ============================

titulo("6. TOP 10 RECHAZOS CON MAYOR IMPACTO ECONÓMICO")

top_rechazos = list(coleccion.find(
    {
        "estado_registro": "ACTIVO",
        "calidad.estado_calidad": "Rechazado"
    },
    {
        "_id": 0,
        "id_registro": 1,
        "fecha": 1,
        "sede": 1,
        "area": 1,
        "turno": 1,
        "producto": 1,
        "lote": 1,
        "produccion.kg_merma": 1,
        "produccion.porcentaje_merma": 1,
        "economico.precio_kg": 1,
        "economico.perdida_estimada": 1
    }
).sort("economico.perdida_estimada", -1).limit(10))

for doc in top_rechazos:
    prod = doc.get("produccion", {})
    eco = doc.get("economico", {})

    print(
        f"{doc.get('id_registro')} | "
        f"{doc.get('producto')} | "
        f"Área: {doc.get('area')} | "
        f"Turno: {doc.get('turno')} | "
        f"Lote: {doc.get('lote')} | "
        f"Merma: {prod.get('kg_merma', 0):,.2f} KG | "
        f"Pérdida: S/ {eco.get('perdida_estimada', 0):,.2f}"
    )


# ============================
# 10. CLASIFICACIÓN DE RIESGO
# ============================

titulo("7. CLASIFICACIÓN DE RIESGO POR MERMA")

riesgo_alto = coleccion.count_documents({
    "estado_registro": "ACTIVO",
    "produccion.porcentaje_merma": {"$gt": 0.08}
})

riesgo_medio = coleccion.count_documents({
    "estado_registro": "ACTIVO",
    "produccion.porcentaje_merma": {"$gt": 0.04, "$lte": 0.08}
})

riesgo_bajo = coleccion.count_documents({
    "estado_registro": "ACTIVO",
    "produccion.porcentaje_merma": {"$lte": 0.04}
})

print(f"Riesgo alto  (> 8% merma): {riesgo_alto} registros")
print(f"Riesgo medio (4% - 8% merma): {riesgo_medio} registros")
print(f"Riesgo bajo  (<= 4% merma): {riesgo_bajo} registros")


# ============================
# 11. POSIBLE RECUPERACIÓN ECONÓMICA
# ============================

titulo("8. ESCENARIO DE MEJORA / RECUPERACIÓN ECONÓMICA")

# Supuesto: si se reduce la merma total en 10%, 15% y 20%
for reduccion in [0.10, 0.15, 0.20]:
    ahorro_estimado = perdida_total * reduccion
    print(
        f"Si se reduce la merma en {reduccion:.0%}, "
        f"el ahorro estimado sería: S/ {ahorro_estimado:,.2f}"
    )


# ============================
# 12. PROPUESTA DE MEJORA
# ============================

titulo("9. PROPUESTA DE MEJORA BASADA EN DATOS")

print("Problema principal identificado:")
print(
    f"El proceso presenta una tasa de rechazo de {tasa_rechazo:.2%} "
    f"y una pérdida económica estimada de S/ {perdida_total:,.2f}."
)

print("\nInterpretación:")
print(
    "La alta cantidad de registros rechazados evidencia una oportunidad de mejora "
    "en el control operativo, especialmente en productos, áreas y turnos con mayor impacto económico."
)

print("\nAcciones recomendadas:")

if tasa_rechazo > 0.30:
    print("- Implementar una alerta preventiva para lotes con merma mayor al 8%.")
    print("- Priorizar inspección en productos con mayor pérdida económica.")
    print("- Reforzar supervisión en áreas con mayor concentración de rechazos.")
    print("- Aplicar checklist de calidad antes del despacho o liberación del lote.")
    print("- Evaluar reproceso seguro para productos observados, siempre que cumplan condiciones sanitarias.")
elif tasa_rechazo > 0.15:
    print("- Monitorear semanalmente la merma por producto y área.")
    print("- Aplicar controles correctivos en lotes con riesgo medio y alto.")
    print("- Capacitar al personal de los turnos críticos.")
else:
    print("- Mantener el control actual y realizar seguimiento mensual de indicadores.")

print("\nRegla de negocio propuesta:")
print(
    "Todo lote con porcentaje de merma mayor al 8% será clasificado como RIESGO ALTO "
    "y deberá pasar por inspección preventiva antes de despacho o venta."
)

print("\nConclusión ejecutiva:")
print(
    "El análisis económico permite priorizar acciones correctivas no solo por cantidad de rechazos, "
    "sino por impacto monetario. Esto mejora la toma de decisiones y permite reducir pérdidas "
    "sin depender únicamente de revisiones manuales."
)