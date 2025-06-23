import streamlit as st
import math
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Micropile Borehole Calculator")

st.title("Minimum Micropile Borehole Calculation")


# User inputs
E = 20000  # Fixed elastic modulus [kPa]
nsk = st.number_input("Service load (Nsk) [kN]", value=1000.0)
tskin = st.number_input("Allowable shaft resistance (tskin) [kPa]", value=300.0)
FS = st.number_input("Safety Factor (FS)", value=2.0)
a = st.number_input("Friction coefficient (a)", value=1.2)
borehole_diameter = st.number_input("Borehole diameter [mm]", value=150.0)

# Calculations
diameter_m = borehole_diameter * 1e-3
area = math.pi * diameter_m**2 / 4
EA = E * area
Lmin = nsk * FS / (math.pi * diameter_m * a * tskin)

# Results on screen
st.subheader("Results")
st.write(f"Cross-sectional area: {area:.6f} m²")
st.write(f"Axial stiffness EA: {EA:.2f} kN")
st.write(f"Minimum required length (Lmin): {Lmin:.2f} m")

st.header("Reference Charts")
st.image("images/abacos.png", caption="Resitance", use_container_width=True) 


# PDF generation using reportlab
def create_pdf():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Micropile Borehole Report")

    y -= 40
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Elastic modulus (E): {E} kPa")
    y -= 20
    p.drawString(50, y, f"Service load (Nsk): {nsk} kN")
    y -= 20
    p.drawString(50, y, f"Allowable shaft resistance (tskin): {tskin} kPa")
    y -= 20
    p.drawString(50, y, f"Safety factor (FS): {FS}")
    y -= 20
    p.drawString(50, y, f"Friction coefficient (a): {a}")
    y -= 20
    p.drawString(50, y, f"Borehole diameter: {borehole_diameter} mm")

    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Results:")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Cross-sectional area: {area:.6f} m²")
    y -= 20
    p.drawString(50, y, f"Axial stiffness EA: {EA:.2f} kN")
    y -= 20
    p.drawString(50, y, f"Minimum required pile length (Lmin): {Lmin:.2f} m")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# Download button
if st.button("Generate PDF Report"):
    pdf_bytes = create_pdf()
    st.download_button("📄 Download PDF", data=pdf_bytes, file_name="micropile_report.pdf", mime="application/pdf")
