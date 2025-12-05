import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
import json
import tempfile
import os

# =============================================================
# CONFIGURATION
# =============================================================
st.set_page_config(page_title="Anchorage Verification", layout="wide")
st.title("Anchorage Safety Verification")

# =============================================================
# SIDEBAR PARAMETERS
# =============================================================
st.sidebar.header("General Settings")

section_name = st.sidebar.text_input("Section Name", value="Section 1")

n = st.sidebar.number_input(
    "Number of anchors",
    min_value=1, max_value=50, value=2, step=1
)

E = 210000       # MPa
A_strand = 140   # mm2 per strand
delta_L = 6      # mm slip

st.sidebar.markdown("---")
st.sidebar.write(f"E = {E} MPa")
st.sidebar.write(f"Area per strand = {A_strand} mm2")
st.sidebar.write(f"Wedge slip = {delta_L} mm")

# =============================================================
# FUNCTIONS
# =============================================================
def compute_coords(x1, y1, ang, L1, L2):
    rad = math.radians(ang)
    x2 = x1 + L1 * math.cos(rad)
    y2 = y1 + L1 * math.sin(rad)
    x3 = x2 + L2 * math.cos(rad)
    y3 = y2 + L2 * math.sin(rad)
    return x2, y2, x3, y3

# =============================================================
# PDF GENERATION (ASCII-SAFE)
# =============================================================
def create_pdf(df, graph_path, section_name, df_bh, C_bolbo, carga_parede, V_total, V_metro,
               borehole_id, borehole_x, esp, afast, A_inf):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "", 11)

    # ---------------------------------------------------------
    # TITLE PAGE
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Anchorage Safety Verification Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Section: {section_name}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "This report presents the geometry, design parameters, "
        "bond verification and bulb load verification for ground anchors."
    )
    pdf.ln(8)

    # ---------------------------------------------------------
    # GLOBAL PARAMETERS
    # ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Global Parameters", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0, 5,
        f"E = {E} MPa\n"
        f"As = {A_strand} mm2 per strand\n"
        f"Wedge slip delta_L = {delta_L} mm\n"
        f"Allowable steel stress = 1440 MPa\n"
        f"Borehole ID = {borehole_id}\n"
        f"Borehole X position = {borehole_x} m\n"
        f"Wall thickness = {esp} m\n"
        f"Anchor spacing = {afast} m\n"
        f"Influence area = {A_inf} m\n"
    )
    pdf.ln(4)

    # ---------------------------------------------------------
    # FORMULAS (ASCII ONLY)
    # ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Equations Used", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0, 5,
        "Slip loss:\n"
        "  DP_slip = (E * A / L_free) * delta_L / 1000\n\n"
        "Block head force:\n"
        "  P_block = P_prestress + DP_slip\n\n"
        "Steel capacity:\n"
        "  P_max = A * 1440 / 1000\n\n"
        "Bond resistance:\n"
        "  R_bond = L_bond * pi * d * alpha * tau / FS\n\n"
        "Vertical component:\n"
        "  V = P_prestress * sin(abs(angle))\n"
    )
    pdf.ln(8)

    # ---------------------------------------------------------
    # PER-ANCHOR PAGES
    # ---------------------------------------------------------
    for _, row in df.iterrows():

        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, f"Anchor {int(row['Anchor'])}", ln=True)
        pdf.ln(3)

        pdf.set_font("Helvetica", "", 10)

        pdf.multi_cell(
            0, 5,
            f"Coordinates:\n"
            f"  X1={row['X1']:.2f}, Y1={row['Y1']:.2f}\n"
            f"  X2={row['X2']:.2f}, Y2={row['Y2']:.2f}\n"
            f"  X3={row['X3']:.2f}, Y3={row['Y3']:.2f}\n\n"
            f"Lengths:\n"
            f"  Free length  = {row['L_free (m)']:.2f} m\n"
            f"  Bond length  = {row['L_bond (m)']:.2f} m\n\n"
        )

        pdf.multi_cell(
            0, 5,
            f"Steel area A = {row['Steel Area (mm2)']:.0f} mm2\n"
            f"Prestress = {row['Prestress (kN)']:.2f} kN\n"
            f"Slip loss = {row['Slip Loss (kN)']:.2f} kN\n"
            f"P_block = {row['P_block (kN)']:.2f} kN\n"
            f"P_max = {row['Pmax (kN)']:.2f} kN\n"
            f"Block check = {row['Block Check']}\n\n"
            f"Bond resistance = {row['Bond Resistance (kN)']:.2f} kN\n"
            f"Bond check = {row['Bond Check']}\n"
        )

    # ---------------------------------------------------------
    # GEOMETRY PAGE
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Anchorage Geometry", ln=True, align="C")
    pdf.image(graph_path, x=10, y=30, w=190)


    # ---------------------------------------------------------
    # BULB LOAD PAGE
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Bulb Load Verification", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.ln(5)
    pdf.cell(0, 8, f"Wall load = {carga_parede:.2f} kN/m", ln=True)
    pdf.cell(0, 8, f"Sum V = {V_total:.2f} kN", ln=True)
    pdf.cell(0, 8, f"V per meter = {V_metro:.2f} kN/m", ln=True)
    pdf.cell(0, 8, f"Bulb load = {C_bolbo:.2f} kN", ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Anchor vertical components:", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(20, 8, "N", border=1)
    pdf.cell(40, 8, "Prestress", border=1)
    pdf.cell(30, 8, "Angle", border=1)
    pdf.cell(40, 8, "V", border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for _, row in df_bh.iterrows():
        pdf.cell(20, 8, str(int(row["Anchor"])), border=1)
        pdf.cell(40, 8, f"{row['Prestress']:.2f}", border=1)
        pdf.cell(30, 8, f"{row['Angle']:.1f}", border=1)
        pdf.cell(40, 8, f"{row['V']:.2f}", border=1)
        pdf.ln()

    # ---------------------------------------------------------
    # ASCII-SAFE OUTPUT
    # ---------------------------------------------------------
    raw = pdf.output(dest="S")
    safe = raw.encode("latin-1", errors="ignore")
    return safe

# =============================================================
# IMPORT CSV
# =============================================================
st.subheader("Import full data (anchors + excavation + stratigraphy + wall)")
upload = st.file_uploader("Upload CSV file", type="csv")

anchors_imported = None
y_excav_default = 0.0
L_excav_default = 5.0
y_wall_default = 5.0
strat_default = []
borehole_id_default = "S1"
borehole_x_default = 1.0
esp_default = 0.30
afast_default = 3.0
A_inf_default = 1.5

if upload is not None:
    try:
        df_import = pd.read_csv(upload)

        cols_anchor = [
            "x1", "y1", "angle", "free", "bond",
            "prestress", "strands", "drill_mm",
            "alpha", "shear_stress", "FS"
        ]

        anchors_imported = [
            {c: row[c] for c in cols_anchor if c in df_import.columns}
            for _, row in df_import.iterrows()
        ]

        # Read geometry stored
        if "geo_json" in df_import.columns:
            raw = df_import["geo_json"].iloc[0]
            if isinstance(raw, str) and raw.strip():
                geo = json.loads(raw)
                y_excav_default = geo.get("y_excav", 0)
                L_excav_default = geo.get("L_excav", 5)
                y_wall_default = geo.get("y_wall", 5)
                strat_default = geo.get("stratigraphy", [])
                borehole_id_default = geo.get("borehole_id", "S1")
                borehole_x_default = geo.get("borehole_x", 1.0)
                esp_default = geo.get("esp", 0.30)
                afast_default = geo.get("afast", 3.0)
                A_inf_default = geo.get("A_inf", 1.5)

        st.success("Data imported successfully.")

    except Exception as e:
        st.error(f"CSV read error: {e}")

st.markdown("---")

# =============================================================
# GLOBAL DEFAULTS TO AVOID NameError IN OTHER TABS
# =============================================================
esp = esp_default
afast = afast_default
A_inf = A_inf_default

tab_anchors, tab_geo, tab_res, tab_bolbo, tab_export, tab_calc = st.tabs(
    ["Anchors", "Excavation / Stratigraphy / Wall", "Results", "Bulb Load", "Export", "Calculation Method"]
)

# =============================================================
# TAB 1 – ANCHORS
# =============================================================
with tab_anchors:
    st.subheader("Anchor Definition")

    if anchors_imported:
        n = len(anchors_imported)

    data = []

    for i in range(n):
        preset = anchors_imported[i] if anchors_imported else {}

        with st.expander(f"Anchor {i+1}", expanded=(i == 0)):
            col1, col2, col3 = st.columns(3)

            with col1:
                x1 = st.number_input("X1 (m)", value=preset.get("x1", 0.0), key=f"x1_{i}")
                y1 = st.number_input("Y1 (m)", value=preset.get("y1", 8.0), key=f"y1_{i}")
                angle = st.number_input("Angle (deg)", value=preset.get("angle", -25.0), key=f"ang_{i}")

            with col2:
                Lfree = st.number_input("Free length (m)", value=preset.get("free", 10.0), key=f"free_{i}")
                Lbond = st.number_input("Bond length (m)", value=preset.get("bond", 10.0), key=f"bond_{i}")
                drill = st.number_input("Drill diameter (mm)", value=preset.get("drill_mm", 150), key=f"drill_{i}")

            with col3:
                prestress = st.number_input("Prestress (kN)", value=preset.get("prestress", 100.0), key=f"pre_{i}")
                strands = st.number_input("Strands", min_value=1, value=preset.get("strands", 3), key=f"str_{i}")
                alpha = st.number_input("Alpha", value=preset.get("alpha", 1.4), key=f"alpha_{i}")
                tau = st.number_input("Shear stress (kN/m2)", value=preset.get("shear_stress", 150), key=f"tau_{i}")
                FS = st.number_input("Safety factor FS", value=preset.get("FS", 1.8), key=f"FS_{i}")

        data.append({
            "x1": x1, "y1": y1, "angle": angle,
            "free": Lfree, "bond": Lbond,
            "prestress": prestress, "strands": strands,
            "drill_mm": drill, "alpha": alpha,
            "shear_stress": tau, "FS": FS
        })


# =============================================================
# TAB 2 – GEOMETRY
# =============================================================
with tab_geo:

    st.subheader("Excavation, Stratigraphy, Wall and Borehole")

    col1, col2 = st.columns(2)

    with col1:
        y_excav = st.number_input("Excavation bottom (m)", value=y_excav_default, format="%.2f")
        L_excav = st.number_input("Left extension (m)", value=L_excav_default, min_value=0.0)
        y_wall = st.number_input("Wall top (m)", value=y_wall_default, format="%.2f")

    with col2:
        borehole_id = st.text_input("Borehole ID", value=borehole_id_default)
        borehole_x = st.number_input("Borehole X position (m)", value=borehole_x_default)

    st.markdown("### Stratigraphy")

    n_layers = st.number_input("Number of layers", min_value=0, max_value=20, value=len(strat_default))

    stratigraphy = []
    for j in range(n_layers):
        preset = strat_default[j] if j < len(strat_default) else {}
        with st.expander(f"Layer {j+1}"):
            name = st.text_input("Name", value=preset.get("name", f"Layer{j+1}"), key=f"name_{j}")
            y = st.number_input("Y level", value=float(preset.get("y", -2*(j+1))), step=0.1, format="%.2f", key=f"yl_{j}")
            Lr = st.number_input("Right extension (m)", value=float(preset.get("L", 5.0)), step=0.1, format="%.2f", key=f"lr_{j}")
            stratigraphy.append({"name": name, "y": y, "L": Lr})


# =============================================================
# COMPUTATIONS
# =============================================================
table = []
fig, ax = plt.subplots(figsize=(10, 6))

# reference x coordinate for wall
x_ref = min(d["x1"] for d in data)

for i, d in enumerate(data):

    x1, y1 = d["x1"], d["y1"]
    ang = d["angle"]
    L1, L2 = d["free"], d["bond"]
    strands = d["strands"]
    prestress = d["prestress"]
    drill = d["drill_mm"]
    alpha = d["alpha"]
    tau = d["shear_stress"]
    FS_val = d["FS"]

    x2, y2, x3, y3 = compute_coords(x1, y1, ang, L1, L2)

    A = strands * A_strand
    Lfree_mm = L1 * 1000
    slip_loss = (E * A / Lfree_mm) * delta_L / 1000

    P_block = prestress + slip_loss
    Pmax = A * 1440 / 1000
    block_check = "OK" if P_block < Pmax else "FAIL"

    R_bond = L2 * math.pi * (drill * 1e-3) * alpha * tau / FS_val
    bond_check = "OK" if R_bond > P_block else "FAIL"

    # ----------------------------------------------------------
    # DRAW FREE LENGTH
    # ----------------------------------------------------------
    ax.plot([x1, x2], [y1, y2], "o-", label="Free Length" if i == 0 else "_nolegend_")

    xm_free = (x1 + x2) / 2
    ym_free = (y1 + y2) / 2

    ax.annotate(
        f"{L1:.2f} m",
        xy=(xm_free, ym_free),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=8,
        rotation=ang,
        rotation_mode='anchor',
        color="blue"
    )

# Prestress annotation near anchor head
    ax.annotate(
    	f"P = {prestress:.0f} kN\nP_block = {P_block:.0f} kN",
    	xy=(x1, y1),
    	xytext=(-80, 0),        # deslocamento 
    	textcoords="offset points",
    	fontsize=8,
    	color="black",
    	ha="left",
    	va="center",
    	bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", lw=0.5)
)


# ----------------------------------------------------------
# DRAW BOND LENGTH (bolbo)
# ----------------------------------------------------------
    ax.plot([x2, x3], [y2, y3], "o--", label="Bond Length" if i == 0 else "_nolegend_")

# Bond resistance annotation at start of bulb (x2, y2)
    ax.annotate(
    	f"R = {R_bond:.0f} kN",
    	xy=(x2, y2),
    	xytext=(10, 0),
    	textcoords="offset points",
    	fontsize=8,
    	color="darkgreen",
    	ha="left",
    	va="center",
    	bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="darkgreen", lw=0.5)
)


# midpoint
    xm_bond = (x2 + x3) / 2
    ym_bond = (y2 + y3) / 2

# Bond length label (L_bond) — sem caixa, igual ao free
    ax.annotate(
    	f"{L2:.2f} m",
    	xy=((x2 + x3) / 2, (y2 + y3) / 2),
    	xytext=(5, 5),
    	textcoords="offset points",
    	fontsize=8,
    	rotation=ang,
    	rotation_mode='anchor',
    	color="green"
)


    # store table results
    table.append({
        "Anchor": i+1,
        "X1": x1, "Y1": y1, "X2": x2, "Y2": y2, "X3": x3, "Y3": y3,
        "L_free (m)": L1, "L_bond (m)": L2,
        "Strands": strands, "Steel Area (mm2)": A,
        "Prestress (kN)": prestress,
        "Slip Loss (kN)": round(slip_loss, 2),
        "P_block (kN)": round(P_block, 2),
        "Pmax (kN)": round(Pmax, 2),
        "Block Check": block_check,
        "Bond Resistance (kN)": round(R_bond, 2),
        "Bond Check": bond_check,
        "drill_mm": drill,
        "alpha": alpha,
        "shear_stress": tau,
        "FS": FS_val
    })

# ----------------------------------------------------------
# DRAW WALL
# ----------------------------------------------------------
ax.plot([x_ref, x_ref], [y_excav, y_wall], "k-", linewidth=3)

# excavation
ax.plot([x_ref, x_ref - L_excav], [y_excav, y_excav], "k-", linewidth=2)

# ----------------------------------------------------------
# STRATIGRAPHY WITH LABELS (to the right end of each layer)
# ----------------------------------------------------------
for layer in stratigraphy:
    y_layer = layer["y"]
    L_layer = layer["L"]
    name = layer["name"]

    # linha da camada
    ax.plot([x_ref, x_ref + L_layer], [y_layer, y_layer], "k:", linewidth=1.5)

    # POSIÇÃO DESTINO (fim da linha)
    x_label = x_ref + L_layer

    # Nome da camada
    ax.text(
        x_label,
        y_layer + 0.1,         # ligeiramente acima
        f"{name}",
        fontsize=8,
        va="bottom",
        ha="left"
    )

    # Cota da camada (por baixo do nome)
    ax.text(
        x_label,
        y_layer - 0.1,
        f"{y_layer:.2f} m",
        fontsize=8,
        va="top",
        ha="left",
        color="gray"
    )

# ----------------------------------------------------------
# BOREHOLE LINE (red dashed) + label at wall top
# ----------------------------------------------------------
ax.plot(
    [borehole_x, borehole_x],
    [y_excav-3, y_wall],
    color="red",
    linestyle="--",
    linewidth=2
)

# Label at top elevation (y_wall)
ax.text(
    borehole_x,
    y_wall + 0.2,
    borehole_id,
    fontsize=10,
    va="bottom",
    ha="center",
    color="red"
)

# ----------------------------------------------------------
# GRAPH STYLE
# ----------------------------------------------------------
ax.set_aspect("equal", adjustable="datalim")
ax.set_xlabel("Horizontal coordinate (m)")
ax.set_ylabel("Elevation (m)")
ax.grid(True)
ax.legend()

df_res = pd.DataFrame(table)

# save graph
import io

img_buf = io.BytesIO()
plt.savefig(img_buf, format="png", dpi=300, bbox_inches="tight")
img_buf.seek(0)
graph_path = img_buf


# =============================================================
# TAB 3 – RESULTS / EXPORT
# =============================================================
with tab_res:

    st.subheader("Geometry and Results")

    colL, colR = st.columns((1, 1))
    colL.pyplot(fig)
    colR.dataframe(df_res, use_container_width=True)

    df_check = df_res[
        ["Anchor", "P_block (kN)", "Bond Resistance (kN)", "Block Check", "Bond Check"]
    ]

    def color_check(v):
        return "background-color:#c8f7c5" if v == "OK" else "background-color:#f7c5c5"

    st.table(df_check.style.applymap(color_check, subset=["Block Check", "Bond Check"]))

    # export data
    geo_payload = {
        "y_excav": y_excav,
        "L_excav": L_excav,
        "y_wall": y_wall,
        "stratigraphy": stratigraphy,
        "borehole_id": borehole_id,
        "borehole_x": borehole_x,
        "esp": esp,
        "afast": afast,
        "A_inf": A_inf,
        "section_name": section_name
    }

    df_export = pd.DataFrame(
        [{**d, **geo_payload, "geo_json": json.dumps(geo_payload)} for d in data]
    )

    st.download_button(
        "Export ALL (CSV)",
        df_export.to_csv(index=False).encode("utf-8"),
        "anchors_export.csv"
    )

# =============================================================
# TAB 4 – BULB LOAD
# =============================================================
with tab_bolbo:

    st.subheader("Bulb Load Calculation (using Prestress and ABS(angle))")

    colA, colB, colC, colD = st.columns(4)

    with colA:
        H = y_wall - y_excav
        st.number_input("Wall height (m)", value=H, disabled=True)

    with colB:
        esp = st.number_input(
            "Wall thickness (m)",
            value=st.session_state.get("esp", esp_default)
        )
        st.session_state["esp"] = esp

    with colC:
        afast = st.number_input(
            "Anchor spacing (m)",
            value=st.session_state.get("afast", afast_default)
        )
        st.session_state["afast"] = afast

    with colD:
        A_inf = st.number_input(
            "Influence area (m)",
            value=st.session_state.get("A_inf", A_inf_default)
        )
        st.session_state["A_inf"] = A_inf


    # Store values globally
    st.session_state["esp"] = esp
    st.session_state["afast"] = afast
    st.session_state["A_inf"] = A_inf

    # Wall load
    carga_parede = H * esp * 25

    # Initialize list for bulb load calculations
    bulb_rows = []
    V_total = 0

    for idx, row in df_res.iterrows():

        P = row["Prestress (kN)"]

        # Correct angle source
        ang = data[idx]["angle"]

        V = P * math.sin(math.radians(abs(ang)))
        V_total += V

        bulb_rows.append({
            "Anchor": row["Anchor"],
            "Prestress": P,
            "Angle": ang,
            "V": V
        })

    df_bh = pd.DataFrame(bulb_rows)

    V_metro = V_total / afast
    C_bolbo = V_metro * A_inf + carga_parede * A_inf

    st.dataframe(df_bh, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Sum V (kN)", f"{V_total:.2f}")
    col2.metric("V per meter (kN/m)", f"{V_metro:.2f}")
    col3.metric("Bulb load (kN)", f"{C_bolbo:.2f}")

    if st.button("Download PDF Report"):
        pdf_bytes = create_pdf(
            df_res,
            graph_path,
            section_name,
            df_bh,
            C_bolbo,
            carga_parede,
            V_total,
            V_metro,
            borehole_id,
            borehole_x,
            esp,
            afast,
            A_inf
        )

        st.download_button(
            "Download PDF",
            pdf_bytes,
            "anchor_report.pdf",
            mime="application/pdf"
        )

# cleanup image
try:
    os.unlink(graph_path)
except:
    pass


# =============================================================
# TAB 5 – EXPORT
# =============================================================
with tab_export:

    st.header("Export Data and Reports")

    st.subheader("Export CSV")
    st.download_button(
        "Download ALL (CSV)",
        df_export.to_csv(index=False).encode("utf-8"),
        "anchors_export.csv",
        mime="text/csv"
    )

    st.markdown("---")

    st.subheader("Export PDF Report")
    pdf_bytes = create_pdf(
        df_res,
        graph_path,
        section_name,
        df_bh,
        C_bolbo,
        carga_parede,
        V_total,
        V_metro,
        borehole_id,
        borehole_x,
        esp,
        afast,
        A_inf
    )

    st.download_button(
        "Download PDF Report",
        pdf_bytes,
        "anchor_report.pdf",
        mime="application/pdf"
    )

# =============================================================
# TAB – CALCULATION METHOD
# =============================================================
with tab_calc:

    st.header("Calculation Methodology")
    st.write("""
    This section describes all equations and assumptions used in the program.

    ## 1. Geometrical Model
    Each anchor is defined by:
    - Head coordinates (X1, Y1)
    - Inclination angle θ (degrees)
    - Free length L_free
    - Bond length L_bond

    Coordinates are computed as:
    ```
    X2 = X1 + L_free * cos(θ)
    Y2 = Y1 + L_free * sin(θ)
    X3 = X2 + L_bond * cos(θ)
    Y3 = Y2 + L_bond * sin(θ)
    ```

    ## 2. Steel Area
    Total steel area:
    ```
    A = n_strands * 140 mm²
    ```

    ## 3. Slip Loss (Wedge Seating Loss)
    Wedge slip = 6 mm.

    Loss of force:
    ```
    ΔP_slip = (E * A / L_free_mm) * δ / 1000
    ```

    where:
    - E = 210000 MPa
    - δ = 6 mm slip
    - L_free_mm = L_free * 1000

    ## 4. Block Force (Head Load)
    ```
    P_block = P_prestress + ΔP_slip
    ```

    ## 5. Steel Ultimate Capacity
    ```
    P_max = A * f_steel / 1000
    ```

    Using:
    - f_steel = 1440 MPa

    Check:
    ```
    OK if P_block < P_max
    ```

    ## 6. Bond Resistance of the Bulb
    ```
    R_bond = L_bond * π * d_borehole * α * τ / FS
    ```

    Parameters:
    - L_bond in m  
    - d_borehole in meters  
    - α = bond efficiency  
    - τ = skin friction (kN/m²)  
    - FS = safety factor  

    Check:
    ```
    OK if R_bond > P_block
    ```

    ## 7. Vertical Component of Prestress
    ```
    V = P_prestress * sin(|θ|)
    ```

    ## 8. Wall Load
    Assuming γ = 25 kN/m³:
    ```
    carga_parede = H * esp * 25
    ```

    ## 9. Bulb Load Verification
    Sum of vertical components:
    ```
    V_total = Σ V_i
    ```

    Load per meter:
    ```
    V_m = V_total / spacing
    ```

    Bulb load:
    ```
    C_bolbo = V_m * A_inf + carga_parede * A_inf
    ```

    ## 10. Output Summary
    The program outputs:
    - Geometry of anchors
    - Prestress and block force
    - Slip losses
    - Bond resistance and check
    - Vertical components
    - Wall load and bulb load
    - Complete PDF report
    - Full CSV export

    This section ensures total transparency of the structural/geotechnical verification process.
    """)

