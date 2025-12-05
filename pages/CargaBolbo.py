import streamlit as st
import pandas as pd
import math
from fpdf import FPDF

# ==================================================
# STREAMLIT SETUP
# ==================================================
st.set_page_config(page_title="Carga no Bolbo – Microestacas", layout="wide")
st.title("Verificação das Cargas no Bolbo das Microestacas")

# ==================================================
# INPUT – CORTE
# ==================================================
corte_nome = st.text_input("Nome do Corte / Secção", value="Corte A-A")

st.markdown("Esta ferramenta calcula a carga transmitida ao bolbo considerando:")
st.markdown("""
- Peso da parede  
- Carga vertical oriunda das ancoragens  
- Afastamento entre ancoragens  
- Área de influência das microestacas  
""")
st.markdown("---")

# ==================================================
# INPUTS GERAIS
# ==================================================
colA, colB, colC, colD = st.columns(4)

with colA:
    H = st.number_input("Altura da parede [m]", value=10.0)

with colB:
    esp = st.number_input("Espessura da parede [m]", value=0.30)

with colC:
    afast = st.number_input("Afastamento entre ancoragens [m]", value=3.0)

with colD:
    A_inf = st.number_input("Área de influência [m]", value=1.5)

carga_parede = H * esp * 25
st.write(f"**Carga vertical da parede = {carga_parede:.2f} kN/m**")
st.markdown("---")

# ==================================================
# ANCORAGENS
# ==================================================
st.subheader("Definição das Ancoragens")

n = st.number_input("Número de ancoragens", min_value=1, max_value=50, value=2)

anc_list = []
for i in range(n):
    with st.expander(f"Ancoragem {i+1}", expanded=(i == 0)):
        col1, col2 = st.columns(2)

        with col1:
            Pbloc = st.number_input(f"P_bloc {i+1} [kN]", value=500.0, key=f"pb{i}")

        with col2:
            ang = st.number_input(f"Ângulo {i+1} [°]", value=35.0, key=f"ang{i}")

        anc_list.append({"Pbloc": Pbloc, "ang": ang})

st.markdown("---")

# ==================================================
# CÁLCULOS
# ==================================================
dados = []
V_total = 0

for i, a in enumerate(anc_list):
    V = a["Pbloc"] * math.sin(math.radians(a["ang"]))
    V_total += V

    dados.append({
        "Ancoragem": i + 1,
        "P_bloc (kN)": a["Pbloc"],
        "Ang (°)": a["ang"],
        "V (kN)": V
    })

df = pd.DataFrame(dados)

V_metro = V_total / afast
C_bolbo = V_metro * A_inf + carga_parede * A_inf

st.subheader("Resultados por Ancoragem")
st.dataframe(df, use_container_width=True)

st.markdown("---")

# ==================================================
# RESULTADOS GERAIS
# ==================================================
st.subheader("Resumo Geral")

col1, col2, col3 = st.columns(3)
col1.metric("Carga da parede (kN/m)", f"{carga_parede:.2f}")
col2.metric("Σ Componentes verticais (kN)", f"{V_total:.2f}")
col3.metric("Componentes por metro (kN/m)", f"{V_metro:.2f}")

st.success(f"Carga no Bolbo = **{C_bolbo:.2f} kN**")
st.markdown("---")

# ==================================================
# FUNÇÃO PDF — VERSÃO 100% FUNCIONAL
# ==================================================
def gerar_pdf(nome, df, carga_parede, V_total, V_metro, C_bolbo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Carga no Bolbo - {nome}", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.ln(4)
    pdf.cell(0, 8, f"Carga da parede: {carga_parede:.2f} kN/m", ln=True)
    pdf.cell(0, 8, f"Somatorio V ancoragens: {V_total:.2f} kN", ln=True)
    pdf.cell(0, 8, f"Componentes verticais por metro: {V_metro:.2f} kN/m", ln=True)
    pdf.cell(0, 8, f"Carga no bolbo: {C_bolbo:.2f} kN", ln=True)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Tabela das ancoragens:", ln=True)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(20, 8, "N", border=1)
    pdf.cell(40, 8, "P_bloc (kN)", border=1)
    pdf.cell(30, 8, "Ang (°)", border=1)
    pdf.cell(40, 8, "V (kN)", border=1)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(20, 8, str(int(row["Ancoragem"])), border=1)
        pdf.cell(40, 8, f"{row['P_bloc (kN)']:.2f}", border=1)
        pdf.cell(30, 8, f"{row['Ang (°)']:.1f}", border=1)
        pdf.cell(40, 8, f"{row['V (kN)']:.2f}", border=1)
        pdf.ln()

    return bytes(pdf.output(dest="S"))

# ==================================================
# BOTÃO PDF
# ==================================================
if st.button("Gerar PDF"):
    pdf_bytes = gerar_pdf(corte_nome, df, carga_parede, V_total, V_metro, C_bolbo)
    st.download_button(
        "Descarregar PDF",
        pdf_bytes,
        file_name=f"carga_bolbo_{corte_nome}.pdf",
        mime="application/pdf"
    )
