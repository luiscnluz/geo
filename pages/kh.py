import streamlit as st
import math

# Modulo de elasticidade do betão
material_Ec = {
    'C25/30': 31e6,
    'C30/37': 33e6,
    'C35/45': 34e6,
    'C40/50': 35e6,
    'C45/55': 36e6,
    'C50/60': 37e6
}

st.set_page_config(page_title="kh em Estacas (Vesic)", layout="centered")
st.title("Cálculo do coeficiente de reação horizontal em estacas (Vesic)")

st.markdown(
    """
    **Fórmula usada (Vesic):**

    `kh = 0.65 * ((Es * d⁴) / (Ec * I))^(1/12) * (Es / (d * (1 - v²)))`

    Segundo Santos (2008), kh deve ser multiplicado por 2.  
    Este programa já faz essa correção automaticamente.
    """
)

# Inputs
material = st.selectbox("Classe de betão", list(material_Ec.keys()), index=1)
pile_diameter = st.number_input("Diâmetro da estaca (m)", min_value=0.01, max_value=5.0, value=0.6, step=0.01, format="%.2f")

st.markdown("### Solos (até 3 camadas)")
soils = []
for i in range(1, 4):
    cols = st.columns(3)
    Es = cols[0].number_input(f"Es{i} (kPa)", min_value=0.0, value=0.0, step=1000.0, format="%.0f", key=f"Es_{i}")
    v = cols[1].number_input(f"Poisson v{i} (0-0.5)", min_value=0.0, max_value=0.499, value=0.3, step=0.01, format="%.3f", key=f"v_{i}")
    if Es > 0:
        soils.append((Es, v))

Ec = material_Ec[material]
inertia = (math.pi * pile_diameter**4) / 64

show_results = st.button("Calcular")

if show_results:
    if pile_diameter <= 0 or len(soils) == 0 or any(not (0 < v < 0.5) for _, v in soils):
        st.error("Verifica se todos os valores são positivos e válidos:\n- Diâmetro > 0\n- Poisson entre 0 e 0.5\n- Es > 0\n- Pelo menos um solo preenchido")
    else:
        st.markdown("#### Resultados:")
        st.write(f"**Material selecionado:** {material}")
        st.write(f"**Módulo de elasticidade (Ec):** {Ec:,.0f} kPa")
        st.write(f"**Diâmetro da estaca:** {pile_diameter:.2f} m")
        st.write(f"**Momento de inércia (I):** {inertia:.6f} m⁴")

        for idx, (Es, v) in enumerate(soils, start=1):
            kh_ = 0.65 * (Es * pile_diameter**4 / (Ec * inertia))**(1/12) * (Es / (pile_diameter * (1 - v**2)))
            kh = kh_ * 2 * pile_diameter
            st.write(
                f"**Solo {idx}:** Es = {Es:,.0f} kPa | v = {v:.3f} | kh = {kh:,.2f} kN/m"
            )

st.markdown("---")
st.caption("Kh Vesic | 2025")
