import streamlit as st


def render_sidebar_navigation() -> None:
    with st.sidebar:
        st.page_link("app.py", label="Tabla completa")
        st.page_link(
            "pages/1_Detalle_de_empresa.py",
            label="Detalle de empresa",
        )
