from __future__ import annotations

import pandas as pd
import streamlit as st

from data import ANTICIPO_COLUMN, compact_money, load_dashboard_data


st.set_page_config(
    page_title="Anticipo de utilidades",
    page_icon="📊",
    layout="wide",
)


def render_company_table(filtered: pd.DataFrame) -> None:
    table_columns = [
        "NOMBRE",
        "RUC",
        "AÑO",
        "INGRESOS (*)",
        "TOTAL (*)",
        ANTICIPO_COLUMN,
        "GANANCIA NETA DEL PERIODO (30701)",
        "PÉRDIDA NETA DEL PERIODO (30702)",
        "GANANCIAS ACUMULADAS (30601)",
        "PÉRDIDAS ACUMULADAS (30602)",
        "PROVINCIA",
    ]
    display_data = filtered.loc[:, table_columns].reset_index(drop=True)

    event = st.dataframe(
        display_data,
        key="company_table",
        use_container_width=True,
        height=610,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "NOMBRE": st.column_config.TextColumn("Empresa", width="large"),
            "RUC": st.column_config.TextColumn("RUC", width="medium"),
            "AÑO": st.column_config.TextColumn("Año", width="small"),
            "INGRESOS (*)": st.column_config.NumberColumn(
                "Ingresos (*)", format="$%.2f"
            ),
            "TOTAL (*)": st.column_config.NumberColumn(
                "Base imponible · TOTAL (*)", format="$%.2f"
            ),
            ANTICIPO_COLUMN: st.column_config.NumberColumn(
                ANTICIPO_COLUMN, format="$%.2f"
            ),
            "GANANCIA NETA DEL PERIODO (30701)": st.column_config.NumberColumn(
                "Ganancia neta del período", format="$%.2f"
            ),
            "PÉRDIDA NETA DEL PERIODO (30702)": st.column_config.NumberColumn(
                "Pérdida neta del período", format="$%.2f"
            ),
            "GANANCIAS ACUMULADAS (30601)": st.column_config.NumberColumn(
                "Ganancias acumuladas", format="$%.2f"
            ),
            "PÉRDIDAS ACUMULADAS (30602)": st.column_config.NumberColumn(
                "Pérdidas acumuladas", format="$%.2f"
            ),
            "PROVINCIA": st.column_config.TextColumn("Provincia", width="medium"),
        },
    )

    if event.selection.rows:
        selected_position = event.selection.rows[0]
        st.session_state["selected_ruc"] = str(
            display_data.iloc[selected_position]["RUC"]
        )
        st.switch_page("pages/1_Detalle_de_empresa.py")


st.title("Anticipo estimado de utilidades")
st.caption(
    "El anticipo estimado corresponde a TOTAL (*) multiplicado por la tarifa "
    "del tramo definido en TablaTasa.xlsx. Selecciona una fila para ver el detalle."
)

try:
    data = load_dashboard_data()
except (FileNotFoundError, KeyError, ValueError, ImportError) as exc:
    st.error(f"No fue posible cargar las fuentes de datos: {exc}")
    st.stop()

income_minimum = float(data["INGRESOS (*)"].min())
income_maximum = float(data["INGRESOS (*)"].max())
advance_minimum = float(data[ANTICIPO_COLUMN].min())
advance_maximum = float(data[ANTICIPO_COLUMN].max())
province_options = sorted(data["PROVINCIA"].dropna().unique().tolist())

st.subheader("Filtros")
income_column, advance_column, province_column = st.columns(3, gap="large")

with income_column:
    income_filter_min = st.number_input(
        "Ingresos (*) desde",
        min_value=income_minimum,
        max_value=income_maximum,
        value=income_minimum,
        step=1_000.0,
        format="%.2f",
    )
    income_filter_max = st.number_input(
        "Ingresos (*) hasta",
        min_value=income_minimum,
        max_value=income_maximum,
        value=income_maximum,
        step=1_000.0,
        format="%.2f",
    )

with advance_column:
    advance_filter_min = st.number_input(
        "Anticipo estimado desde",
        min_value=advance_minimum,
        max_value=advance_maximum,
        value=advance_minimum,
        step=100.0,
        format="%.2f",
    )
    advance_filter_max = st.number_input(
        "Anticipo estimado hasta",
        min_value=advance_minimum,
        max_value=advance_maximum,
        value=advance_maximum,
        step=100.0,
        format="%.2f",
    )

with province_column:
    selected_provinces = st.multiselect(
        "Provincia",
        options=province_options,
        placeholder="Todas las provincias",
    )

if income_filter_min > income_filter_max:
    st.warning("El ingreso mínimo no puede ser mayor que el ingreso máximo.")
    st.stop()
if advance_filter_min > advance_filter_max:
    st.warning("El anticipo mínimo no puede ser mayor que el anticipo máximo.")
    st.stop()

mask = data["INGRESOS (*)"].between(income_filter_min, income_filter_max)
mask &= data[ANTICIPO_COLUMN].between(advance_filter_min, advance_filter_max)
if selected_provinces:
    mask &= data["PROVINCIA"].isin(selected_provinces)

filtered_data = data.loc[mask].copy()

metric_companies, metric_income, metric_advance = st.columns([0.7, 1.5, 1.1])
metric_companies.metric("Empresas", f"{len(filtered_data):,}")
metric_income.metric(
    "Ingresos filtrados", compact_money(filtered_data["INGRESOS (*)"].sum())
)
metric_advance.metric(
    "Anticipo estimado filtrado",
    compact_money(filtered_data[ANTICIPO_COLUMN].sum()),
)

if filtered_data.empty:
    st.info("No hay empresas que coincidan con los filtros seleccionados.")
else:
    render_company_table(filtered_data)
