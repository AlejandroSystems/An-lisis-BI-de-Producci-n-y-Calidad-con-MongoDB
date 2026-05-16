# analizar_mongodb.py
# Objetivo: consultar MongoDB y generar indicadores BI básicos

from pymongo import MongoClient


# ============================
# 1. CONEXIÓN A MONGODB
# ============================

MONGO_URI = "mongodb://localhost:27017/"
NOMBRE_BD = "bi_produccion_calidad"
NOMBRE_COLECCION = "reporte_erp_produccion"

cliente = MongoClient(MONGO_URI)
db = cliente[NOMBRE_BD]
coleccion = db[NOMBRE_COLECCION]


# ============================
# 2. INDICADORES GENERALES
# ============================

total_registros = coleccion.count_documents({"estado_registro": "ACTIVO"})

produccion_total = list(coleccion.aggregate([
    {"$match": {"estado_registro": "ACTIVO"}},
    {"$group": {
        "_id": None,
        "total_kg_producidos": {"$sum": "$produccion.kg_producidos"},
        "total_kg_merma": {"$sum": "$produccion.kg_merma"}
    }}
]))

if produccion_total:
    total_kg = produccion_total[0]["total_kg_producidos"]
    total_merma = produccion_total[0]["total_kg_merma"]
    porcentaje_merma_general = total_merma / total_kg if total_kg > 0 else 0
else:
    total_kg = 0
    total_merma = 0
    porcentaje_merma_general = 0


# ============================
# 3. PRODUCCIÓN POR ÁREA
# ============================

produccion_por_area = list(coleccion.aggregate([
    {"$match": {"estado_registro": "ACTIVO"}},
    {"$group": {
        "_id": "$area",
        "kg_producidos": {"$sum": "$produccion.kg_producidos"},
        "kg_merma": {"$sum": "$produccion.kg_merma"},
        "registros": {"$sum": 1}
    }},
    {"$sort": {"kg_producidos": -1}}
]))


# ============================
# 4. CALIDAD POR ESTADO
# ============================

calidad_por_estado = list(coleccion.aggregate([
    {"$match": {"estado_registro": "ACTIVO"}},
    {"$group": {
        "_id": "$calidad.estado_calidad",
        "cantidad": {"$sum": 1}
    }},
    {"$sort": {"cantidad": -1}}
]))


# ============================
# 5. MERMA POR PRODUCTO
# ============================

merma_por_producto = list(coleccion.aggregate([
    {"$match": {"estado_registro": "ACTIVO"}},
    {"$group": {
        "_id": "$producto",
        "kg_merma": {"$sum": "$produccion.kg_merma"},
        "kg_producidos": {"$sum": "$produccion.kg_producidos"}
    }},
    {"$addFields": {
        "porcentaje_merma": {
            "$cond": [
                {"$gt": ["$kg_producidos", 0]},
                {"$divide": ["$kg_merma", "$kg_producidos"]},
                0
            ]
        }
    }},
    {"$sort": {"porcentaje_merma": -1}}
]))


# ============================
# 6. RESULTADOS EN CONSOLA
# ============================

print("\n===== INDICADORES BI GENERALES =====")
print(f"Total de registros activos: {total_registros}")
print(f"Producción total: {total_kg:,.2f} KG")
print(f"Merma total: {total_merma:,.2f} KG")
print(f"Porcentaje de merma general: {porcentaje_merma_general:.2%}")


print("\n===== PRODUCCIÓN POR ÁREA =====")
for item in produccion_por_area:
    print(f"{item['_id']}: {item['kg_producidos']:,.2f} KG | Merma: {item['kg_merma']:,.2f} KG")


print("\n===== CALIDAD POR ESTADO =====")
for item in calidad_por_estado:
    print(f"{item['_id']}: {item['cantidad']} registros")


print("\n===== MERMA POR PRODUCTO =====")
for item in merma_por_producto:
    print(f"{item['_id']}: {item['porcentaje_merma']:.2%} de merma")