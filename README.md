# Dashboard de anticipo estimado

Aplicación Streamlit que muestra todas las variables de `temporal.parquet`, la tasa aplicable y el anticipo estimado calculados con los tramos de `TablaTasa.xlsx`. Permite filtrar por ingresos, anticipo y provincia. Al seleccionar una empresa se abre una página con su información de `directorio_core.parquet`.

## Ejecución local

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Despliegue en Streamlit Community Cloud

1. Sube este repositorio a GitHub, incluidos los tres archivos de datos.
2. En Streamlit Community Cloud, crea una app desde el repositorio.
3. Selecciona `app.py` como archivo principal.

El cálculo aplicado es:

```text
Anticipo Estimado = TOTAL (*) × Tarifa del tramo correspondiente
```
