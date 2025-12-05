import streamlit as st
import pandas as pd
import math

# ===================================================================
# CATALOG — MICROPILES
# ===================================================================
def micropiles_catalog():
    micropiles = {
        "ext_diameter_mm": [88.9, 88.9, 88.9, 101.6, 114.3, 114.3, 127.0, 139.7, 177.8, 177.8, 177.8],
        "thickness_mm":    [6.5, 7.5, 9.5, 9.0, 7.0, 9.0, 9.0, 9.0, 9.0, 10.0, 11.5],
        "A_cm2":           [16.83, 19.18, 23.70, 26.18, 23.60, 29.77, 33.36, 36.95, 47.73, 52.72, 60.08],
        "I_cm4":           [144, 160, 189, 283, 341, 416, 584, 793, 1710, 1860, 2090],
    }
    df = pd.DataFrame(micropiles)
    df["section"] = "CHS " + df["ext_diameter_mm"].astype(str) + "x" + df["thickness_mm"].astype(str)
    df.set_index("section", inplace=True)
    return df


df_micro = micropiles_catalog()

# ===================================================================
# PAGE TITLE
# ===================================================================
st.title("PLAXIS – Structural Parameters Generator")

tabs = st.tabs(["Diaphragm Wall", "Micropiles (CHS)", "Anchors (Strands EA)"])

# ===================================================================
# TAB 1 — DIAPHRAGM WALL
# ===================================================================
with tabs[0]:
    st.header("Diaphragm Wall")

    material_Ec = {
        'C25/30': 31e6,
        'C30/37': 33e6,
        'C35/45': 34e6,
        'C40/50': 35e6,
        'C45/55': 36e6,
        'C50/60': 37e6
    }

    material = st.selectbox("Concrete class:", list(material_Ec.keys()))
    Ec = material_Ec[material]

    thickness = st.number_input("Thickness [m]:", min_value=0.0, value=0.60)

    if thickness > 0:
        weight = thickness * 25
        inertia = thickness**3 / 12
        flexural_rigidity = Ec * inertia
        normal_stiffness = thickness * Ec

        st.subheader("Results")
        st.write(f"**Ec:** {Ec:.0f} kN/m²")
        st.write(f"**EI (flexural rigidity):** {flexural_rigidity:.2e} kNm²/m")
        st.write(f"**EA (normal stiffness):** {normal_stiffness:.2e} kN/m")
        st.write(f"**Self-weight:** {weight:.2f} kN/m²")


# ===================================================================
# TAB 2 — MICROPILES (CHS)
# ===================================================================
with tabs[1]:
    st.header("Micropiles – CHS")

    with st.expander("Micropile catalog"):
        st.dataframe(df_micro, use_container_width=True)

    Es = 210e6     # MPa → kN/m²
    weight_steel = 78.5  # kN/m³ equivalent

    mode = st.radio("Select micropile definition mode:",
                    ["From catalog", "Manual input"],
                    horizontal=True)

    if mode == "From catalog":
        section = st.selectbox("Select CHS section:", df_micro.index)
        D_ext = df_micro.loc[section, "ext_diameter_mm"]
        t = df_micro.loc[section, "thickness_mm"]
        A = df_micro.loc[section, "A_cm2"]
        I = df_micro.loc[section, "I_cm4"]

    else:
        st.subheader("Manual input")
        D_ext = st.number_input("External diameter D [mm]:", min_value=50.0, value=139.7)
        t = st.number_input("Wall thickness t [mm]:", min_value=2.0, value=9.0)

        # Área e inércia para CHS — EXACTAMENTE como no teu módulo de microestacas
        A = (math.pi/4) * (D_ext**2 - (D_ext - 2*t)**2) * 1e-2        # cm²
        I = (math.pi/64) * (D_ext**4 - (D_ext - 2*t)**4) * 1e-4       # cm⁴

        st.write(f"**Calculated area A:** {A:.2f} cm²")
        st.write(f"**Calculated inertia I:** {I:.1f} cm⁴")

        section = f"CHS {D_ext}x{t}"

    spacing = st.number_input("Spacing between micropiles [m]:",
                              min_value=0.10, value=1.00)

    # ---- formulas ----
    def calc_EI(I_cm4, spacing):
        EI = Es * (I_cm4 * 1e-8) / spacing
        return EI

    def calc_EA(A_cm2, spacing):
        EA = (A_cm2 * 1e-4) * Es / spacing
        return EA

    def calc_weight(A_cm2, spacing):
        return A_cm2 * 1e-4 * weight_steel / spacing

    EI = calc_EI(I, spacing)
    EA = calc_EA(A, spacing)
    W = calc_weight(A, spacing)

    st.subheader("Results")
    st.write(f"**Section:** {section}")
    st.write(f"**External diameter:** {D_ext:.1f} mm")
    st.write(f"**Thickness:** {t:.1f} mm")
    st.write(f"**Spacing:** {spacing:.2f} m")
    st.write(f"**Area A:** {A:.2f} cm²")
    st.write(f"**Inertia I:** {I:.1f} cm⁴")
    st.write(f"**EI (flexural rigidity):** {EI:.2e} kNm²/m")
    st.write(f"**EA (normal stiffness):** {EA:.2e} kN/m")
    st.write(f"**Weight per metre:** {W:.3f} kN/m/m")



# ===================================================================
# TAB 3 — ANCHORS (Prestressing Strands)
# ===================================================================
with tabs[2]:
    st.header("Anchors – Prestressing Strands")

    st.markdown("Axial stiffness EA for PLAXIS Embedded Anchor (2D).")

    # Área A em mm2 (editável, valor típico 140 mm2)
    A_mm2 = st.number_input(
        "Strand area A [mm²]:",
        min_value=10.0,
        value=140.0,
        step=1.0
    )
    A_strand = A_mm2 * 1e-6  # m²

    # Nº de cordões
    number_prestressing_strands = st.number_input(
        "Number of strands:",
        min_value=1,
        value=3,
        step=1
    )

    # Módulo de elasticidade dos cordões (kN/m²)
    E_strand = 2.10e8  # 210 GPa

    def calc_EA(n, E, A):
        # EA de UM tirante (sem dividir por espaçamento, PLAXIS pergunta spacing à parte)
        return n * E * A  # kN

    EA_anchor = calc_EA(number_prestressing_strands, E_strand, A_strand)

    st.subheader("Results – Anchor stiffness (single anchor)")
    st.write(f"**E (steel):** {E_strand:.2e} kN/m²")
    st.write(f"**Area A (per strand):** {A_mm2:.1f} mm²  ({A_strand:.6f} m²)")
    st.write(f"**Number of strands:** {number_prestressing_strands}")
    st.write("")
    st.write(f"**EA = n · E · A:** {EA_anchor:.2e} kN")

    st.info("Insert this EA value directly in PLAXIS (Normal stiffness for the Embedded Anchor). "
            "The spacing is defined separately in the PLAXIS interface.")
