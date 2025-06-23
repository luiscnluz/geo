import streamlit as st

# Dicionário com módulos de elasticidade
material_Ec = {
    'C25/30': 31e6,
    'C30/37': 33e6,
    'C35/45': 34e6,
    'C40/50': 35e6,
    'C45/55': 36e6,
    'C50/60': 37e6
}

st.title("Properties of the Diaphragm Wall")

# Seletor de classe de betão
material = st.selectbox("Select concrete class:", list(material_Ec.keys()))
Ec = material_Ec[material]

# Input da espessura
thickness = st.number_input("Insert thickness [m]:", min_value=0.0, format="%.2f")

if thickness > 0:
    weight = thickness * 25  # kN/m² (assumindo densidade ~25 kN/m³)
    inertia = thickness**3 / 12  # m^4/m
    flexural_rigidity = Ec * inertia  # kN·m²/m
    normal_stiffness = thickness * Ec  # kN/m

    # Resultados
    st.subheader("Results")
    st.write(f"**Ec:** {Ec:.0f} kN/m²")
    st.write(f"**Thickness:** {thickness:.2f} m")
    st.write(f"**Flexural rigidity:** {flexural_rigidity:.2e} kNm²/m")
    st.write(f"**Normal stiffness:** {normal_stiffness:.2e} kN/m")
    st.write(f"**Weight (self-weight per m²):** {weight:.2f} kN/m²")
