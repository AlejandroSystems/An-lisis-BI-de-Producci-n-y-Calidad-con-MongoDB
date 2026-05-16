# Proyecto BI con MongoDB y Python

## Descripción
Proyecto de inteligencia de negocios basado en una base de datos NoSQL MongoDB. Se simula un reporte ERP en Excel, se procesa con Python, se transforma en documentos JSON y se carga a MongoDB para realizar análisis operativo y económico.

## Objetivo
Analizar datos de producción, calidad, merma y pérdida económica mediante Python y MongoDB, identificando productos, áreas y turnos críticos.

## Tecnologías usadas
- Python
- MongoDB
- MongoDB Compass
- openpyxl
- pymongo
- Excel
- Flask
- HTML/CSS

## Flujo del proyecto
Excel ERP simulado → Python → JSON → MongoDB → Análisis BI → Dashboard web

## Indicadores analizados
- Producción total
- Merma total
- Porcentaje de merma
- Tasa de rechazo
- Pérdida económica estimada
- Productos con mayor pérdida
- Áreas críticas
- Turnos críticos
- Escenarios de ahorro

## Resultados principales
- Registros analizados: 3000
- Producción total: 1,943,399 KG
- Merma total: 126,760.29 KG
- Tasa de rechazo: 35.40%
- Pérdida estimada: S/ 3,194,910.79

## Propuesta de mejora
Implementar alertas preventivas para lotes con merma mayor al 8%, reforzar controles en áreas críticas y priorizar inspecciones en productos con mayor impacto económico.

El archivo .xlsm contiene el formulario operativo y macros de simulación.
El archivo .xlsx puede utilizarse como versión de datos limpia para pruebas.
