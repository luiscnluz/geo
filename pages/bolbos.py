import streamlit as st
import math
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Bolbo de Selagem - Método de Bustamante e Doix")

st.title("Cálculo de Bolbo de Selagem - Méodo de Bustamante e Doix")

# Entradas do utilizador
E = 20000  # Módulo de elasticidade fixo [kPa]
nsk = st.number_input("Carga de serviço (Nsk) [kN]", value=1000.0)
tskin = st.number_input("Resistência lateral (tskin) [kPa]", value=300.0)
FS = st.number_input("Fator de segurança (FS)", value=2.0)
a = st.number_input("alfa", value=1.2)
borehole_diameter = st.number_input("Diâmetro do furo [mm]", value=150.0)

# Cálculos
diameter_m = borehole_diameter * 1e-3
area = math.pi * diameter_m**2 / 4
EA = E * area
Lmin = nsk * FS / (math.pi * diameter_m * a * tskin)

# Resultados no ecrã
st.subheader("Resultados")
st.write(f"Área da secção: {area:.6f} m²")
st.write(f"Comprimento mínimo necessário (Lmin): {Lmin:.2f} m")

st.header("Ábacos de Referência")
st.image("images/abacos.png", caption="Resistência", use_container_width=True) 

# Geração de PDF com reportlab
def criar_pdf():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Comprimento mínimo de bolbo de selagem")

    y -= 40
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Módulo de elasticidade (E): {E} kPa")
    y -= 20
    p.drawString(50, y, f"Carga de serviço (Nsk): {nsk} kN")
    y -= 20
    p.drawString(50, y, f"Resistência lateral (tskin): {tskin} kPa")
    y -= 20
    p.drawString(50, y, f"Fator de segurança (FS): {FS}")
    y -= 20
    p.drawString(50, y, f"alfa: {a}")
    y -= 20
    p.drawString(50, y, f"Diâmetro do furo: {borehole_diameter} mm")

    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Resultados:")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Área da secção: {area:.6f} m²")
    y -= 20

    p.drawString(50, y, f"Comprimento mínimo do bolbo de selagem (Lmin): {Lmin:.2f} m")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# Botão para gerar PDF
if st.button("Gerar Relatório PDF"):
    pdf_bytes = criar_pdf()
    st.download_button("📄 Descarregar PDF", data=pdf_bytes, file_name="relatorio_micropilar.pdf", mime="application/pdf")