import streamlit as st
import pandas as pd
import math

def carregar_microestacas():
    microestacas = {
        "diam_ext_mm": [88.9, 88.9, 88.9, 101.6, 114.3, 114.3, 127.0, 139.7, 177.8, 177.8, 177.8],
        "esp_mm":      [6.5, 7.5, 9.5, 9.0, 7.0, 9.0, 9.0, 9.0, 9.0, 10.0, 11.5],
        "A_cm2":       [16.83, 19.18, 23.70, 26.18, 23.60, 29.77, 33.36, 36.95, 47.73, 52.72, 60.08],
        "I_cm4":       [144, 160, 189, 283, 341, 416, 584, 793, 1710, 1860, 2090],
        "i_cm":        [2.92, 2.89, 2.83, 3.29, 3.80, 3.74, 4.18, 4.63, 5.98, 5.94, 5.89],
        "w_cm3":       [32.31, 36.02, 42.59, 55.74, 59.64, 72.70, 91.83, 113.45, 191.66, 209.34, 234.63],
    }

    df = pd.DataFrame(microestacas)
    df["secao"] = "CHS " + df["diam_ext_mm"].astype(str) + "x" + df["esp_mm"].astype(str)
    df.set_index("secao", inplace=True)
    return df

def resistencia(secao, L_crit, df, fyd, E_aco, fyk):
    area = df.loc[secao, "A_cm2"]
    inercia = df.loc[secao, "I_cm4"]
    diametro_ext = df.loc[secao, "diam_ext_mm"]

    mrd = ((2*inercia*1e-8*fyd*1e3)/(diametro_ext*1e-3))
    vrd = (2*area*1e-4/math.pi)*fyk*1e3/math.sqrt(3)
    nrd = area * 1e-4 * fyd * 1e3

    i = math.sqrt(inercia / area) * 1e-2
    lamb = L_crit / (i * math.pi * math.sqrt(E_aco * 1e3 / fyd))
    a = 0.21
    fi = 0.5 * (1 + a * (lamb - 0.2) + lamb**2)
    x = 1 / (fi + math.sqrt(fi**2 - lamb**2))
    nbrd = nrd * x
    ntd_unioes_ext = nrd * 0.75
    ntd_macho_femea = nrd * 0.4

    return mrd, vrd, i, lamb, a, fi, x, nrd, nbrd, ntd_unioes_ext, ntd_macho_femea

# -------------- STREAMLIT APP --------------
st.set_page_config(page_title="Verificação Microestacas", layout="centered")
st.title("Verificação de Segurança de Microestacas")

# Dados
df = carregar_microestacas()

# Materiais
gamma_m0 = 1.0
fyk = 560  # MPa
fyd = fyk / gamma_m0
gamma_aco = 78  # kN/m³
E_aco = 210  # GPa

# Escolha do utilizador
st.subheader("Seleciona os parâmetros:")

micro = st.selectbox("Seção de microestaca", df.index.tolist(), index=7)
L_crit = st.number_input("Comprimento de encurvadura [m]", min_value=1.0, max_value=20.0, value=6.0, step=0.1)
Ned = st.number_input("Esforço axial de cálculo Ned [kN]", min_value=1.0, max_value=2000.0, value=400.0, step=1.0)

# Cálculo
mrd, vrd, i, lamb, a, fi, x, nrd, nbrd, ntd_unioes_ext, ntd_macho_femea = resistencia(
    micro, L_crit, df, fyd, E_aco, fyk
)
check_axial = nbrd >= Ned

# Resultados
st.markdown("### Resultados:")

st.write(f'**Ned instalado:** {Ned:.2f} kN')
st.write(f'**Nbrd (resistência à encurvadura):** {nbrd:.2f} kN')

if check_axial:
    st.success("✅ Verificação de segurança à encurvadura: OK")
else:
    st.error("❌ Não verifica segurança à encurvadura.")

with st.expander("Ver detalhes da resistência"):
    st.write(f"**MRd** = {mrd:.2f} kNm")
    st.write(f"**VRd** = {vrd:.2f} kN")
    st.write(f"**i** = {i:.2f} m")
    st.write(f"**λ** = {lamb:.3f}")
    st.write(f"**φ** = {fi:.3f}")
    st.write(f"**χ** = {x:.3f}")
    st.write(f"**Nrd (resistência de secção)** = {nrd:.2f} kN")
    st.write(f"**Nrd (uniões exteriores)** = {ntd_unioes_ext:.2f} kN")
    st.write(f"**Nrd (macho-fêmea)** = {ntd_macho_femea:.2f} kN")

st.markdown("---")
st.dataframe(df)

st.markdown("---")
st.caption("Microestacas | Designed for civil engineering applications by Luís Luz")
