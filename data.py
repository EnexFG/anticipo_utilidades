from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
TEMPORAL_PATH = BASE_DIR / "temporal.parquet"
DIRECTORIO_PATH = BASE_DIR / "directorio_core.parquet"
TASAS_PATH = BASE_DIR / "TablaTasa.xlsx"

ANTICIPO_COLUMN = "Anticipo Estimado"
TASA_COLUMN = "Tasa Aplicable"
PROVINCIA_SIN_DATOS = "SIN INFORMACIÓN"


def _clean_ruc(series: pd.Series) -> pd.Series:
    """Normalize identifiers without converting them to numbers."""
    return series.astype("string").str.strip()


@st.cache_data(show_spinner=False)
def load_rate_table() -> pd.DataFrame:
    """Read and validate the rate brackets used by the dashboard."""
    rates = pd.read_excel(TASAS_PATH)
    rates.columns = rates.columns.astype(str).str.strip()

    required = {"Tramo", "Desde", "Hasta", "Tarifa"}
    missing = required.difference(rates.columns)
    if missing:
        raise ValueError(
            "TablaTasa.xlsx no contiene las columnas requeridas: "
            + ", ".join(sorted(missing))
        )

    rates = rates.loc[:, ["Tramo", "Desde", "Hasta", "Tarifa"]].copy()
    rates["Desde"] = pd.to_numeric(rates["Desde"], errors="raise")
    rates["Tarifa"] = pd.to_numeric(rates["Tarifa"], errors="raise")
    rates["Hasta numérico"] = pd.to_numeric(rates["Hasta"], errors="coerce")
    rates["Hasta numérico"] = rates["Hasta numérico"].fillna(np.inf)
    rates = rates.sort_values("Desde", kind="stable").reset_index(drop=True)

    if rates.empty:
        raise ValueError("TablaTasa.xlsx no contiene tramos.")
    if not rates["Hasta numérico"].is_monotonic_increasing:
        raise ValueError("Los límites superiores de TablaTasa.xlsx no están ordenados.")
    if (rates["Tarifa"] < 0).any():
        raise ValueError("TablaTasa.xlsx contiene una tarifa negativa.")

    return rates


def calculate_applicable_rate(
    taxable_base: pd.Series, rate_table: pd.DataFrame
) -> pd.Series:
    """Return the flat rate corresponding to each TOTAL (*) bracket."""
    base = pd.to_numeric(taxable_base, errors="coerce").fillna(0.0).clip(lower=0.0)
    upper_bounds = rate_table["Hasta numérico"].to_numpy(dtype=float)
    tariffs = rate_table["Tarifa"].to_numpy(dtype=float)

    bracket_index = np.searchsorted(upper_bounds, base.to_numpy(dtype=float), side="left")
    bracket_index = np.clip(bracket_index, 0, len(tariffs) - 1)
    applicable_rate = tariffs[bracket_index]

    return pd.Series(applicable_rate, index=taxable_base.index, name=TASA_COLUMN)


def calculate_estimated_advance(
    taxable_base: pd.Series, applicable_rate: pd.Series
) -> pd.Series:
    """Calculate TOTAL (*) multiplied by its applicable flat rate."""
    base = pd.to_numeric(taxable_base, errors="coerce").fillna(0.0).clip(lower=0.0)
    rate = pd.to_numeric(applicable_rate, errors="coerce").fillna(0.0)
    estimated = np.round(base.to_numpy(dtype=float) * rate.to_numpy(dtype=float), 2)

    return pd.Series(estimated, index=taxable_base.index, name=ANTICIPO_COLUMN)


@st.cache_data(show_spinner="Cargando información empresarial…")
def load_temporal() -> pd.DataFrame:
    temporal = pd.read_parquet(TEMPORAL_PATH)
    temporal["RUC"] = _clean_ruc(temporal["RUC"])
    temporal[TASA_COLUMN] = calculate_applicable_rate(
        temporal["TOTAL (*)"], load_rate_table()
    )
    temporal[ANTICIPO_COLUMN] = calculate_estimated_advance(
        temporal["TOTAL (*)"], temporal[TASA_COLUMN]
    )
    return temporal


@st.cache_data(show_spinner=False)
def load_directory() -> pd.DataFrame:
    directory = pd.read_parquet(DIRECTORIO_PATH)
    directory["RUC"] = _clean_ruc(directory["RUC"])
    return directory


@st.cache_data(show_spinner="Preparando dashboard…")
def load_dashboard_data() -> pd.DataFrame:
    temporal = load_temporal()
    provinces = (
        load_directory()
        .dropna(subset=["RUC"])
        .drop_duplicates(subset=["RUC"], keep="first")
        .loc[:, ["RUC", "PROVINCIA"]]
    )
    dashboard = temporal.merge(provinces, on="RUC", how="left", validate="one_to_one")
    dashboard["PROVINCIA"] = dashboard["PROVINCIA"].fillna(PROVINCIA_SIN_DATOS)
    return dashboard


def money(value: float) -> str:
    return f"${value:,.2f}"


def compact_money(value: float) -> str:
    absolute_value = abs(value)
    if absolute_value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f} mil millones"
    if absolute_value >= 1_000_000:
        return f"${value / 1_000_000:,.2f} millones"
    return money(value)
