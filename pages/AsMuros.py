import streamlit as st
import pandas as pd
import math

# =====================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================
st.set_page_config(page_title="Cálculo de Armaduras - Paredes de Munique", layout="wide")
st.title("Cálculo de Armaduras - Paredes de Munique")

st.markdown("### Dados de entrada")

# -------------------------------
# Materiais
# -------------------------------
betoes = {
    "C25/30": 25.0,
    "C30/37": 30.0,
    "C35/45": 35.0,
    "C40/50": 40.0,
    "C45/55": 45.0,
    "C50/60": 50.0,
}

acos = {
    "A400": 400.0,
    "A500": 500.0,
}

col_mat1, col_mat2, col_mat3 = st.columns(3)

with col_mat1:
    classe_betao = st.selectbox("Classe de betão", list(betoes.keys()), index=1)
    fck = betoes[classe_betao]

with col_mat2:
    gamma_c = st.number_input("γc (betão)", value=1.50, min_value=1.0, max_value=2.0, step=0.05)
    alpha_cc = st.number_input("αcc", value=0.85, min_value=0.7, max_value=1.0, step=0.05)
    fcd = alpha_cc * fck / gamma_c     # MPa

with col_mat3:
    tipo_aco = st.selectbox("Tipo de aço", list(acos.keys()), index=1)
    fyk = acos[tipo_aco]
    st.caption(f"**fck = {fck:.1f} MPa**  |  **fcd = {fcd:.2f} MPa**  |  **fyk = {fyk:.0f} MPa**")

st.markdown("---")

# -------------------------------
# Ações / Banda entre ancoragens
# -------------------------------
col_acao1, col_acao2, col_acao3 = st.columns(3)

with col_acao1:
    M_pos = st.number_input("Momento positivo M⁺ [kNm/m]", value=500.0, step=10.0, format="%.2f")
    M_neg = st.number_input("Momento negativo M⁻ [kNm/m]", value=500.0, step=10.0, format="%.2f")

with col_acao2:
    L_banda = st.number_input("L_banda (distância entre ancoragens) [m]", value=6.0, min_value=0.1, step=0.1)
    fator_maj = st.number_input("Fator de majoração de carga γ_F", value=1.35, min_value=1.0, step=0.05)

with col_acao3:
    Lfc = L_banda / 2.0
    Lfl = L_banda / 2.0
    st.write("**Faixas de cálculo**")
    st.write(f"Lfc (faixa central) = **{Lfc:.2f} m**")
    st.write(f"Lfl (faixa lateral) = **{Lfl:.2f} m**")

st.markdown("---")

# -------------------------------
# Cálculo dos momentos nas faixas
# -------------------------------
if Lfc > 0 and Lfl > 0:
    Mpos_fc = M_pos * fator_maj * L_banda * 0.55 / Lfc
    Mpos_fl = M_pos * fator_maj * L_banda * 0.45 / Lfl
    Mneg_fc = M_neg * fator_maj * L_banda * 0.75 / Lfc
    Mneg_fl = M_neg * fator_maj * L_banda * 0.25 / Lfl

    dados_momentos = [
        {"Faixa": "Central", "Tipo mom.": "M⁺", "Coeficiente": 0.55, "Expressão": "M⁺·γF·L·0.55/Lfc", "M_d [kNm/m]": Mpos_fc},
        {"Faixa": "Lateral", "Tipo mom.": "M⁺", "Coeficiente": 0.45, "Expressão": "M⁺·γF·L·0.45/Lfl", "M_d [kNm/m]": Mpos_fl},
        {"Faixa": "Central", "Tipo mom.": "M⁻", "Coeficiente": 0.75, "Expressão": "M⁻·γF·L·0.75/Lfc", "M_d [kNm/m]": Mneg_fc},
        {"Faixa": "Lateral", "Tipo mom.": "M⁻", "Coeficiente": 0.25, "Expressão": "M⁻·γF·L·0.25/Lfl", "M_d [kNm/m]": Mneg_fl},
    ]

    df_mom = pd.DataFrame(dados_momentos)

    st.subheader("Momentos de dimensionamento por faixa")
    st.dataframe(df_mom.style.format({"M_d [kNm/m]": "{:.2f}"}), use_container_width=True)

else:
    st.error("Lfc e Lfl têm de ser maiores que zero.")
    st.stop()

st.markdown("---")

# ===================================================
# DIMENSIONAMENTO DAS ARMADURAS (As)
# ===================================================
st.subheader("Dimensionamento da Armadura Longitudinal (As)")

col_sec1, col_sec2, col_sec3 = st.columns(3)

with col_sec1:
    b = st.number_input("Largura b (m)", value=1.00, min_value=0.10, format="%.2f")

with col_sec2:
    esp = st.number_input("Espessura da parede h (m)", value=0.40, min_value=0.10, format="%.2f")

with col_sec3:
    a = st.number_input("Cobrimento a ao centro da barra (m)", value=0.05, min_value=0.02, format="%.3f")

d = esp - a
st.write(f"**Altura útil d = {d:.3f} m**")

def calc_As(Md_kNm, fcd_MPa, fyk_MPa, b, d):
    # Conversões
    Md = Md_kNm * 1e3                          # kNm/m → Nm/m
    fcd = fcd_MPa * 1e6                        # MPa → Pa
    fyk = fyk_MPa * 1e6                        # MPa → Pa

    # μ adimensional
    mu = Md / (fcd * b * d**2)

    if mu <= 0 or mu >= 0.50:
        return None, None, None

    # ω
    omega = 1 - math.sqrt(1 - 2 * mu)

    # As em m²/m
    As = omega * fcd / fyk * b * d

    # Converter para cm²/m
    As_cm2 = As * 1e4

    return mu, omega, As_cm2


# -------------------------------  
# Criar tabela  
# -------------------------------
linhas_As = []
for _, row in df_mom.iterrows():
    faixa = row["Faixa"]
    tipo = row["Tipo mom."]
    Md = row["M_d [kNm/m]"]

    mu, omega, As_cm2 = calc_As(Md, fcd, fyk, b, d)

    linhas_As.append({
        "Faixa": faixa,
        "Tipo M": tipo,
        "M_d (kNm/m)": Md,
        "μ": mu,
        "ω": omega,
        "As (cm²/m)": As_cm2,
    })

df_As = pd.DataFrame(linhas_As)

st.subheader("Armadura Necessária por Faixa")
st.dataframe(df_As.style.format({
    "M_d (kNm/m)": "{:.2f}",
    "μ": "{:.4f}",
    "ω": "{:.4f}",
    "As (cm²/m)": "{:.2f}",
}), use_container_width=True)
