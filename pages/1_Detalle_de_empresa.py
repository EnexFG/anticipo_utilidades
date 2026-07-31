from __future__ import annotations

import pandas as pd
import streamlit as st

from data import ANTICIPO_COLUMN, TASA_COLUMN, load_directory, load_temporal, money


st.set_page_config(
    page_title="Detalle de empresa",
    page_icon="🏢",
    layout="wide",
)


def value_for_display(value: object) -> str:
    if pd.isna(value):
        return "—"
    return str(value)


if st.button("← Volver al dashboard", type="secondary"):
    st.switch_page("app.py")

selected_ruc = st.session_state.get("selected_ruc")
temporal = load_temporal()

if not selected_ruc:
    st.title("Detalle de empresa")
    st.info("Selecciona una empresa desde la tabla principal o ingresa su RUC.")
    entered_ruc = st.text_input("RUC", max_chars=13)
    if entered_ruc:
        entered_ruc = entered_ruc.strip()
        if entered_ruc in set(temporal["RUC"].dropna()):
            st.session_state["selected_ruc"] = entered_ruc
            st.rerun()
        else:
            st.warning("El RUC ingresado no está disponible en temporal.parquet.")
    st.stop()

company_financial = temporal.loc[temporal["RUC"] == str(selected_ruc)].copy()
if company_financial.empty:
    st.error("La empresa seleccionada ya no está disponible en temporal.parquet.")
    if st.button("Limpiar selección"):
        st.session_state.pop("selected_ruc", None)
        st.rerun()
    st.stop()

company_financial = company_financial.sort_values("AÑO", ascending=False)
current = company_financial.iloc[0]
company_name = str(current["NOMBRE"])

st.title(company_name)
st.caption(f"RUC {selected_ruc}")

income_metric, base_metric, advance_metric = st.columns(3)
income_metric.metric("Ingresos (*)", money(float(current["INGRESOS (*)"])))
base_metric.metric("Base imponible · TOTAL (*)", money(float(current["TOTAL (*)"])))
advance_metric.metric(ANTICIPO_COLUMN, money(float(current[ANTICIPO_COLUMN])))

directory = load_directory()
company_directory = directory.loc[directory["RUC"] == str(selected_ruc)]

st.subheader("Información de la empresa")
if company_directory.empty:
    st.warning("No existe información para este RUC en directorio_core.parquet.")
else:
    directory_record = company_directory.iloc[0]
    directory_fields = [column for column in directory.columns if column != "RUC"]
    directory_view = pd.DataFrame(
        {
            "Campo": directory_fields,
            "Valor": [value_for_display(directory_record[field]) for field in directory_fields],
        }
    )
    st.dataframe(
        directory_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Campo": st.column_config.TextColumn("Campo", width="medium"),
            "Valor": st.column_config.TextColumn("Valor", width="large"),
        },
    )

st.subheader("Información financiera")
financial_columns = [
    "AÑO",
    "INGRESOS (*)",
    "TOTAL (*)",
    TASA_COLUMN,
    ANTICIPO_COLUMN,
    "GANANCIA NETA DEL PERIODO (30701)",
    "PÉRDIDA NETA DEL PERIODO (30702)",
    "GANANCIAS ACUMULADAS (30601)",
    "PÉRDIDAS ACUMULADAS (30602)",
]
st.dataframe(
    company_financial.loc[:, financial_columns],
    use_container_width=True,
    hide_index=True,
    column_config={
        column: st.column_config.NumberColumn(column, format="dollar", step=0.01)
        for column in financial_columns
        if column not in {"AÑO", TASA_COLUMN}
    }
    | {
        TASA_COLUMN: st.column_config.NumberColumn(
            TASA_COLUMN, format="percent", step=0.0001
        )
    },
)
