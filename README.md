# Observatorio Económico y Social de Nariño

Prototipo tecnológico centrado en Nariño y comparativo con el resto de departamentos de Colombia.

## Características

- 4 indicadores reales de fuentes oficiales:
  - PIB departamental (constantes 2015) – DANE
  - Homicidios – MinDefensa
  - Violencia intrafamiliar – MinDefensa
  - Recursos públicos DNP
- Sección “Nariño en cifras” con KPIs, ranking y variación anual
- Diagnóstico automático generado a partir de los datos
- Gráficos Plotly interactivos
- Estadística descriptiva + descarga CSV
- Regla antialucinación: cero datos sintéticos

## Despliegue

1. Sube app.py, requirements.txt y README.md a un repositorio público de GitHub.
2. Ve a https://share.streamlit.io → Create app → selecciona el repositorio y app.py.
3. Deploy. Copia el link público.

## Ejecución local

pip install -r requirements.txt
streamlit run app.py