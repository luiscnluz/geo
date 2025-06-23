import streamlit as st
import math
import pdfkit
import os

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

# Results
st.subheader("Results")
st.write(f"Cross-sectional area: {area:.6f} m²")
st.write(f"Axial stiffness EA: {EA:.2f} kN")
st.write(f"Minimum required length (Lmin): {Lmin:.2f} m")

# Generate PDF content
html = f"""
<h2>Micropile Borehole Report</h2>
<hr>
<h3>Input Data</h3>
<ul>
  <li>Elastic modulus (E): {E} kPa</li>
  <li>Service load (Nsk): {nsk} kN</li>
  <li>Allowable shaft resistance (tskin): {tskin} kPa</li>
  <li>Safety factor (FS): {FS}</li>
  <li>Friction coefficient (a): {a}</li>
  <li>Borehole diameter: {borehole_diameter} mm</li>
</ul>
<h3>Results</h3>
<ul>
  <li>Cross-sectional area: {area:.6f} m²</li>
  <li>Axial stiffness (EA): {EA:.2f} kN</li>
  <li>Minimum required pile length (Lmin): {Lmin:.2f} m</li>
</ul>
"""

# Generate and download PDF
if st.button("Generate PDF Report"):
    with open("micropile_report.html", "w") as f:
        f.write(html)

    pdfkit.from_file("micropile_report.html", "micropile_report.pdf")

    with open("micropile_report.pdf", "rb") as f:
        st.download_button("📄 Download PDF", f, file_name="micropile_report.pdf")
