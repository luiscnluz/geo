import streamlit as st
import math

st.title("Minimum Pile Length Calculation")

# User inputs
E = 2000
nsk = st.number_input("Service load (Nsk) [kN]", value=1000.0)
tskin = st.number_input("Allowable shaft resistance (tskin) [kPa]", value=300.0)
FS = st.number_input("FS", value=2.0)
a = st.number_input("Friction coefficient (a)", value=1.2)
borehole_diameter = st.number_input("Borehole diameter [mm]", value=150.0)

# Calculations
diameter_m = borehole_diameter * 1e-3  # mm to m
area = math.pi * diameter_m**2 / 4
EA = E * area
Lmin = nsk * FS / (math.pi * diameter_m * a * tskin)

# Results
st.subheader("Results")
st.write(f"Borehole cross-sectional area: {area:.6f} m²")
st.write(f"Axial stiffness EA: {EA:.2f} kN")
st.write(f"Minimum required pile length (Lmin): {Lmin:.2f} m")
