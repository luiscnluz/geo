import streamlit as st
import math
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

st.set_page_config(page_title="Bolbo de Selagem - Método de Bustamante e Doix")

st.title("Cálculo de Bolbo de Selagem – Método de Bustamante e Doix")

# TABELA FS AUXILIAR
# ===============================================================
# ===============================================================



st.markdown("---")

# ===============================================================
# CONTROLO DE FS AUTOMÁTICO OU MANUAL
# ===============================================================

st.subheader("Parâmetros de verificação")

usar_manual = st.checkbox("Inserir FS manualmente")

if not usar_manual:

    tipo_obra = st.radio("Tipo de obra", ["Provisória", "Definitiva"], horizontal=True)
    tipo_esforco = st.radio("Tipo de esforço", ["Tração", "Compressão"], horizontal=True)

    # FS AUTOMÁTICO
    if tipo_obra == "Provisória":
        FS = 2.0 if tipo_esforco == "Tração" else 1.8
    else:
        FS = 2.2 if tipo_esforco == "Tração" else 2.0

    st.success(f"FS automático selecionado: **{FS}**")

else:
    # FS manual substitui completamente o automático
    FS = st.number_input("Insira o Fator de Segurança (FS)", min_value=0.1, value=2.0, step=0.1)
    st.warning("Atenção: A opção manual substitui a tabela auxiliar.")

# ===============================================================
# INPUTS DO UTILIZADOR
# ===============================================================

E = 20000  # kPa (Bustamante e Doix assume tipicamente 20 MPa)
nsk = st.number_input("Carga de serviço Nsk [kN]", value=1000.0)
tskin = st.number_input("Resistência lateral tskin [kPa]", value=300.0)
a = st.number_input("Coeficiente alfa", value=1.2)
borehole_diameter = st.number_input("Diâmetro do furo [mm]", value=150.0)

# ===============================================================
# CÁLCULOS
# ===============================================================

diameter_m = borehole_diameter * 1e-3
area = math.pi * (diameter_m ** 2) / 4

# tskin equivalente para o PLAXIS
tskin_plaxis = 2 * math.pi * (diameter_m / 2) * a * tskin

# Lmin segundo Bustamante & Doix
Lmin = nsk * FS / (math.pi * diameter_m * a * tskin)

# ===============================================================
# RESULTADOS
# ===============================================================

st.subheader("Resultados")

col1, col2 = st.columns(2)

with col1:
    st.write(f"Área da secção: **{area:.6f} m²**")
    st.write(f"tskin (PLAXIS): **{tskin_plaxis:.2f} kN/m**")
    st.write(f"FS utilizado: **{FS}**")

with col2:
    st.markdown(
        f"""
        <div style="padding:12px; background-color:#003366; color:white; 
                    border-radius:6px; font-size:20px; font-weight:bold;">
            Comprimento mínimo Lmin = {Lmin:.2f} m
        </div>
        """,
        unsafe_allow_html=True
    )

# ===============================================================
# ÁBACOS
# ===============================================================

st.header("Ábacos de Referência")

image_path = os.path.join(os.path.dirname(__file__), "images", "abacos.png")

st.image(image_path, caption="Resistência lateral – Bustamante & Doix", use_container_width=True)

st.markdown("### Tabela Auxiliar – Fatores de Segurança recomendados")

fs_data = {
    "Esforço": ["Tração", "Compressão"],
    "Provisória": [2.0, 1.8],
    "Definitiva": [2.2, 2.0],
}
st.table(fs_data)

# ===============================================================
# PDF
# ===============================================================

def criar_pdf():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Cálculo de Bolbo de Selagem – Bustamante & Doix")

    y -= 35
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"FS utilizado: {FS}")
    y -= 20
    pdf.drawString(50, y, f"Nsk = {nsk} kN")
    y -= 20
    pdf.drawString(50, y, f"tskin = {tskin} kPa")
    y -= 20
    pdf.drawString(50, y, f"alfa = {a}")
    y -= 20
    pdf.drawString(50, y, f"Diâmetro do furo = {borehole_diameter} mm")

    y -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Resultados:")
    y -= 20

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Área da secção = {area:.6f} m²")
    y -= 20
    pdf.drawString(50, y, f"tskin (PLAXIS) = {tskin_plaxis:.2f} kN/m")
    y -= 20

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, f"Lmin = {Lmin:.2f} m")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

if st.button("Gerar PDF"):
    pdf_bytes = criar_pdf()
    st.download_button(
        "Descarregar PDF",
        data=pdf_bytes,
        file_name="bolbo_selagem.pdf",
        mime="application/pdf"
    )
