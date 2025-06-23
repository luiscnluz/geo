import streamlit as st
import math

st.title("Minimum Micropile Borehole calculation")

# User inputs
E = 20000
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
st.write(f"L min: {Lmin:.2f} m")
