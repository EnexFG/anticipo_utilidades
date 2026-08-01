from __future__ import annotations

import importlib
import math

import pandas as pd
import streamlit as st

import data as data_source
from navigation import render_sidebar_navigation


# Streamlit Cloud can briefly retain an older imported module after a Git update.
# Reload only when the app detects that app.py and data.py are out of sync.
if not hasattr(data_source, "CLIENTE_ANDERSEN_COLUMN"):
    importlib.invalidate_caches()
    data_source = importlib.reload(data_source)

ANTICIPO_COLUMN = data_source.ANTICIPO_COLUMN
CLIENTE_ANDERSEN_COLUMN = data_source.CLIENTE_ANDERSEN_COLUMN
TASA_COLUMN = data_source.TASA_COLUMN
compact_money = data_source.compact_money
load_dashboard_data = data_source.load_dashboard_data


st.set_page_config(
    page_title="Tabla completa",
    page_icon="📊",
    layout="wide",
)
render_sidebar_navigation()


def render_company_table(filtered: pd.DataFrame) -> None:
    table_columns = [
        "NOMBRE",
        "RUC",
        CLIENTE_ANDERSEN_COLUMN,
        "AÑO",
        "INGRESOS (*)",
        "TOTAL (*)",
        TASA_COLUMN,
        ANTICIPO_COLUMN,
        "GANANCIA NETA DEL PERIODO (30701)",
        "PÉRDIDA NETA DEL PERIODO (30702)",
        "GANANCIAS ACUMULADAS (30601)",
        "PÉRDIDAS ACUMULADAS (30602)",
        "PROVINCIA",
    ]

    sort_options = {
        "Empresa": "NOMBRE",
        "RUC": "RUC",
        "Año": "AÑO",
        "Ingresos (*)": "INGRESOS (*)",
        "Base imponible · TOTAL (*)": "TOTAL (*)",
        TASA_COLUMN: TASA_COLUMN,
        ANTICIPO_COLUMN: ANTICIPO_COLUMN,
        "Ganancia neta del período": "GANANCIA NETA DEL PERIODO (30701)",
        "Pérdida neta del período": "PÉRDIDA NETA DEL PERIODO (30702)",
        "Ganancias acumuladas": "GANANCIAS ACUMULADAS (30601)",
        "Pérdidas acumuladas": "PÉRDIDAS ACUMULADAS (30602)",
        "Provincia": "PROVINCIA",
        CLIENTE_ANDERSEN_COLUMN: CLIENTE_ANDERSEN_COLUMN,
    }

    st.subheader("Tabla de empresas")
    sort_column_ui, sort_direction_ui, page_size_ui = st.columns([1.5, 1, 1])
    with sort_column_ui:
        sort_label = st.selectbox("Ordenar por", options=list(sort_options))
    with sort_direction_ui:
        descending = st.toggle("Orden descendente", value=False)
    with page_size_ui:
        page_size = st.selectbox(
            "Filas por página", options=[100, 250, 500, 1_000], index=1
        )

    sorted_data = filtered.sort_values(
        by=sort_options[sort_label],
        ascending=not descending,
        na_position="last",
        kind="stable",
    )
    total_rows = len(sorted_data)
    total_pages = max(1, math.ceil(total_rows / page_size))

    if st.session_state.get("table_page", 1) > total_pages:
        st.session_state["table_page"] = 1

    page_ui, range_ui = st.columns([1, 3])
    with page_ui:
        current_page = st.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            step=1,
            key="table_page",
        )

    start = (current_page - 1) * page_size
    end = min(start + page_size, total_rows)
    with range_ui:
        st.caption(
            f"Mostrando {start + 1:,}–{end:,} de {total_rows:,} empresas "
            f"· Página {current_page:,} de {total_pages:,}"
        )

    display_data = (
        sorted_data.iloc[start:end].loc[:, table_columns].reset_index(drop=True)
    )

    event = st.dataframe(
        display_data,
        key=f"company_table_{sort_options[sort_label]}_{descending}_{current_page}_{page_size}",
        use_container_width=True,
        height=610,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "NOMBRE": st.column_config.TextColumn("Empresa", width="large"),
            "RUC": st.column_config.TextColumn("RUC", width="medium"),
            CLIENTE_ANDERSEN_COLUMN: st.column_config.TextColumn(
                CLIENTE_ANDERSEN_COLUMN, width="medium"
            ),
            "AÑO": st.column_config.TextColumn("Año", width="small"),
            "INGRESOS (*)": st.column_config.NumberColumn(
                "Ingresos (*)", format="dollar", step=0.01
            ),
            "TOTAL (*)": st.column_config.NumberColumn(
                "Base imponible · TOTAL (*)", format="dollar", step=0.01
            ),
            TASA_COLUMN: st.column_config.NumberColumn(
                TASA_COLUMN, format="percent", step=0.0001
            ),
            ANTICIPO_COLUMN: st.column_config.NumberColumn(
                ANTICIPO_COLUMN, format="dollar", step=0.01
            ),
            "GANANCIA NETA DEL PERIODO (30701)": st.column_config.NumberColumn(
                "Ganancia neta del período", format="dollar", step=0.01
            ),
            "PÉRDIDA NETA DEL PERIODO (30702)": st.column_config.NumberColumn(
                "Pérdida neta del período", format="dollar", step=0.01
            ),
            "GANANCIAS ACUMULADAS (30601)": st.column_config.NumberColumn(
                "Ganancias acumuladas", format="dollar", step=0.01
            ),
            "PÉRDIDAS ACUMULADAS (30602)": st.column_config.NumberColumn(
                "Pérdidas acumuladas", format="dollar", step=0.01
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
st.markdown(
    """
**Fórmulas de cálculo**

- **TOTAL (*)** = Ganancia neta del período − Pérdida neta del período + Ganancias acumuladas − Pérdidas acumuladas.
- **Anticipo Estimado** = TOTAL (*) × Tasa Aplicable.
"""
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
income_column, advance_column, province_column, client_column = st.columns(
    [1, 1, 1, 0.8], gap="large"
)

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

with client_column:
    client_filter = st.selectbox(
        CLIENTE_ANDERSEN_COLUMN,
        options=["Todos", "Si", "No"],
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
if client_filter != "Todos":
    mask &= data[CLIENTE_ANDERSEN_COLUMN].eq(client_filter)

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
