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
    min_value=1,
    max_value=50,
    value=2,
    step=1
)

E = 210000  # MPa

A_strand = st.sidebar.number_input(
    "Area per strand (mm²)",
    min_value=50.0,
    max_value=500.0,
    value=140.0,
    step=5.0
)

delta_L = st.sidebar.number_input(
    "Wedge slip δ (mm)",
    min_value=0.0,
    max_value=20.0,
    value=6.0,
    step=0.5
)

st.sidebar.markdown("---")
st.sidebar.write(f"E = {E} MPa")

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
def create_pdf(df, graph_path, section_name, df_bh,
               C_bolbo, carga_parede, V_total, V_metro,
               borehole_id, borehole_x, esp, afast, A_inf):
    """
    Gera o PDF do relatório de verificação dos tirantes.

    df      -> dataframe com resultados por ancoragem
    graph_path -> caminho do PNG com a geometria
    df_bh   -> dataframe com componentes verticais (bulbo)
    Restantes -> parâmetros globais
    """

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
    pdf.multi_cell(
        0,
        6,
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
        0,
        5,
        f"E = {E} MPa\n"
        f"As = {A_strand} mm2 per strand\n"
        f"Wedge slip = {delta_L} mm\n"
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
        0,
        5,
        "Slip loss:\n"
        "  DP_slip = (E * A / L_free) * delta_L / 1000\n\n"
        "Block head force:\n"
        "  P_block = P_prestress + DP_slip\n\n"
        "Steel capacity:\n"
        "  P_max = A * 1440 / 1000\n\n"
        "Bond resistance:\n"
        "  R_bond = L_bond * pi * d * alpha * tau / FS\n\n"
        "Vertical component:\n"
        "  V = P_prestress * sin( abs(angle) )\n"
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
            0,
            5,
            "Coordinates:\n"
            f"  X1 = {row['X1']:.2f}, Y1 = {row['Y1']:.2f}\n"
            f"  X2 = {row['X2']:.2f}, Y2 = {row['Y2']:.2f}\n"
            f"  X3 = {row['X3']:.2f}, Y3 = {row['Y3']:.2f}\n\n"
            "Lengths:\n"
            f"  Free length = {row['L_free (m)']:.2f} m\n"
            f"  Bond length = {row['L_bond (m)']:.2f} m\n\n"
        )

        pdf.multi_cell(
            0,
            5,
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
    # OUTPUT (COMPATÍVEL COM WINPYTHON, ANACONDA, STREAMLIT)
    # ---------------------------------------------------------
    raw = pdf.output(dest="S")  # fpdf2 devolve normalmente str
    if isinstance(raw, str):
        raw = raw.encode("latin-1", "ignore")

    return raw

    # ---------------------------------------------------------
    # OUTPUT
    # ---------------------------------------------------------
    raw = pdf.output(dest="S")
    return bytes(raw)

# =============================================================
# IMPORT CSV (ROBUSTO PARA STREAMLIT CLOUD)
# =============================================================
import io

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

def safe_json_load(s):
    if not isinstance(s, str):
        return {}
    s = s.strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except:
        try:
            return json.loads(s.replace("'", '"'))
        except:
            return {}

if upload is not None:
    try:
        raw = upload.read()

        # tenta UTF-8, se falhar usa Latin-1
        try:
            text = raw.decode("utf-8")
        except:
            text = raw.decode("latin-1")

        # autodetecta separador
        df_import = pd.read_csv(io.StringIO(text), sep=None, engine="python")

        # normalizar nomes de colunas
        df_import.columns = (
            df_import.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        cols_anchor = [
            "x1","y1","angle","free","bond","prestress",
            "strands","drill_mm","alpha","shear_stress","fs"
        ]

        anchors_imported = []

        for _, row in df_import.iterrows():
            anchor = {}
            for c in cols_anchor:
                if c in row and not pd.isna(row[c]):
                    anchor[c] = float(row[c])
            # só aceita anchors válidos
            if all(k in anchor for k in ("x1","y1","angle","free","bond")):
                anchors_imported.append(anchor)

        # importa dados globais do geo_json
        if "geo_json" in df_import.columns:
            g = safe_json_load(df_import["geo_json"].iloc[0])
            if g:
                y_excav_default = g.get("y_excav", y_excav_default)
                L_excav_default = g.get("l_excav", L_excav_default)
                y_wall_default = g.get("y_wall", y_wall_default)
                strat_default = g.get("stratigraphy", strat_default)
                borehole_id_default = g.get("borehole_id", borehole_id_default)
                borehole_x_default = g.get("borehole_x", borehole_x_default)
                esp_default = g.get("esp", esp_default)
                afast_default = g.get("afast", afast_default)
                A_inf_default = g.get("a_inf", A_inf_default)

        st.success("Data imported successfully.")

    except Exception as e:
        st.error(f"CSV read error: {e}")

st.markdown("---")


# =============================================================
# DXF EXPORT FUNCTION (FINAL + CLEAN)
# =============================================================
def export_dxf(filepath, data, stratigraphy, x_ref, y_excav, y_wall, L_excav,
               borehole_x, borehole_id):

    import ezdxf
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # ---------------------------------------------------------
    # LAYERS
    # ---------------------------------------------------------
    layers = {
        "ANCHOR_FREE": {"color": 5},
        "ANCHOR_BOND": {"color": 3},
        "ANCHOR_LABEL": {"color": 7},
        "WALL": {"color": 1},
        "EXCAVATION": {"color": 2},
        "STRATIGRAPHY": {"color": 4},
        "BOREHOLE": {"color": 6},
    }

    for name, spec in layers.items():
        if name not in doc.layers:
            doc.layers.add(name, dxfattribs={"color": spec["color"]})

    # ---------------------------------------------------------
    # ANCHORS
    # ---------------------------------------------------------
    for i, d in enumerate(data):

        x1, y1 = d["x1"], d["y1"]
        ang = d["angle"]
        L1, L2 = d["free"], d["bond"]

        # Compute geometry
        x2 = x1 + L1 * math.cos(math.radians(ang))
        y2 = y1 + L1 * math.sin(math.radians(ang))
        x3 = x2 + L2 * math.cos(math.radians(ang))
        y3 = y2 + L2 * math.sin(math.radians(ang))

        # Free length
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "ANCHOR_FREE"})

        # Bond length
        msp.add_line((x2, y2), (x3, y3), dxfattribs={"layer": "ANCHOR_BOND"})

        # Label
        txt = msp.add_text(
            f"A{i+1}",
            dxfattribs={"height": 0.30, "layer": "ANCHOR_LABEL"}
        )
        txt.dxf.insert = (x1 + 0.20, y1 + 0.20)

    # ---------------------------------------------------------
    # WALL
    # ---------------------------------------------------------
    msp.add_line(
        (x_ref, y_excav),
        (x_ref, y_wall),
        dxfattribs={"layer": "WALL"}
    )

    # ---------------------------------------------------------
    # EXCAVATION
    # ---------------------------------------------------------
    msp.add_line(
        (x_ref, y_excav),
        (x_ref - L_excav, y_excav),
        dxfattribs={"layer": "EXCAVATION"}
    )

    # ---------------------------------------------------------
    # STRATIGRAPHY
    # ---------------------------------------------------------
    for layer in stratigraphy:

        yL = layer["y"]
        Lr = layer["L"]
        name = layer["name"]

        # Horizontal line
        msp.add_line(
            (x_ref, yL),
            (x_ref + Lr, yL),
            dxfattribs={"layer": "STRATIGRAPHY"}
        )

        # Label
        txt = msp.add_text(
            name,
            dxfattribs={"height": 0.25, "layer": "STRATIGRAPHY"}
        )
        txt.dxf.insert = (x_ref + Lr + 0.20, yL + 0.10)

    # ---------------------------------------------------------
    # BOREHOLE
    # ---------------------------------------------------------
    msp.add_line(
        (borehole_x, y_excav - 3),
        (borehole_x, y_wall),
        dxfattribs={"layer": "BOREHOLE"}
    )

    txt2 = msp.add_text(
        borehole_id,
        dxfattribs={"height": 0.30, "layer": "BOREHOLE"}
    )
    txt2.dxf.insert = (borehole_x, y_wall + 0.30)

    # ---------------------------------------------------------
    # SAVE DXF
    # ---------------------------------------------------------
    doc.saveas(filepath)

# =============================================================
# GLOBAL DEFAULTS
# =============================================================
esp = esp_default
afast = afast_default
A_inf = A_inf_default

# =============================================================
# TABS
# =============================================================
tab_anchors, tab_geo, tab_res, tab_bolbo, tab_export, tab_calc = st.tabs(
    ["Anchors", "Excavation / Stratigraphy / Wall", "Results",
     "Bulb Load", "Export", "Calculation Method"]
)

# =============================================================
# TAB 1 – ANCHORS
# =============================================================
with tab_anchors:
    st.subheader("Anchor Definition")

    data = []

    if anchors_imported:
        n = len(anchors_imported)

    for i in range(n):
        preset = anchors_imported[i] if anchors_imported else {}

        with st.expander(f"Anchor {i+1}", expanded=(i == 0)):
            col1, col2, col3 = st.columns(3)

            with col1:
                x1 = st.number_input(
                    "X1 (m)",
                    value=preset.get("x1", 0.0),
                    key=f"x1_{i}"
                )
                y1 = st.number_input(
                    "Y1 (m)",
                    value=preset.get("y1", 8.0),
                    key=f"y1_{i}"
                )
                angle = st.number_input(
                    "Angle (deg)",
                    value=preset.get("angle", -25.0),
                    key=f"ang_{i}"
                )

            with col2:
                Lfree = st.number_input(
                    "Free length (m)",
                    value=preset.get("free", 10.0),
                    key=f"free_{i}"
                )
                Lbond = st.number_input(
                    "Bond length (m)",
                    value=preset.get("bond", 10.0),
                    key=f"bond_{i}"
                )
                drill = st.number_input(
                    "Drill diameter (mm)",
                    value=preset.get("drill_mm", 150),
                    key=f"drill_{i}"
                )

            with col3:
                prestress = st.number_input(
                    "Prestress (kN)",
                    value=preset.get("prestress", 100.0),
                    key=f"pre_{i}"
                )
                strands = st.number_input(
                    "Strands",
                    min_value=1,
                    value=preset.get("strands", 3),
                    key=f"str_{i}"
                )
                alpha = st.number_input(
                    "Alpha",
                    value=preset.get("alpha", 1.4),
                    key=f"alpha_{i}"
                )
                tau = st.number_input(
                    "Shear stress (kN/m2)",
                    value=preset.get("shear_stress", 150),
                    key=f"tau_{i}"
                )
                FS = st.number_input(
                    "Safety factor FS",
                    value=preset.get("FS", 1.8),
                    key=f"FS_{i}"
                )

            data.append(
                {
                    "x1": x1,
                    "y1": y1,
                    "angle": angle,
                    "free": Lfree,
                    "bond": Lbond,
                    "prestress": prestress,
                    "strands": strands,
                    "drill_mm": drill,
                    "alpha": alpha,
                    "shear_stress": tau,
                    "FS": FS,
                }
            )

# =============================================================
# TAB 2 – GEOMETRY
# =============================================================
with tab_geo:
    st.subheader("Excavation, Stratigraphy, Wall and Borehole")

    col1, col2 = st.columns(2)

    with col1:
        y_excav = st.number_input(
            "Excavation bottom (m)",
            value=y_excav_default,
            format="%.2f"
        )
        L_excav = st.number_input(
            "Left extension (m)",
            value=L_excav_default,
            min_value=0.0
        )
        y_wall = st.number_input(
            "Wall top (m)",
            value=y_wall_default,
            format="%.2f"
        )

    with col2:
        borehole_id = st.text_input(
            "Borehole ID",
            value=borehole_id_default
        )
        borehole_x = st.number_input(
            "Borehole X position (m)",
            value=borehole_x_default
        )

    st.markdown("### Stratigraphy")

    n_layers = st.number_input(
        "Number of layers",
        min_value=0,
        max_value=20,
        value=len(strat_default)
    )

    stratigraphy = []

    for j in range(n_layers):
        preset = strat_default[j] if j < len(strat_default) else {}

        with st.expander(f"Layer {j+1}"):
            name = st.text_input(
                "Name",
                value=preset.get("name", f"Layer{j+1}"),
                key=f"name_{j}"
            )
            y = st.number_input(
                "Y level",
                value=float(preset.get("y", -2 * (j + 1))),
                step=0.1,
                format="%.2f",
                key=f"yl_{j}"
            )
            Lr = st.number_input(
                "Right extension (m)",
                value=float(preset.get("L", 5.0)),
                step=0.1,
                format="%.2f",
                key=f"lr_{j}"
            )

            stratigraphy.append({"name": name, "y": y, "L": Lr})

# =============================================================
# COMPUTATIONS
# =============================================================
table = []

fig, ax = plt.subplots(figsize=(10, 6))

# Reference x coordinate for wall
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

    R_bond = (
        L2
        * math.pi
        * (drill * 1e-3)
        * alpha
        * tau
        / FS_val
    )
    bond_check = "OK" if R_bond > P_block else "FAIL"

    # DRAW FREE LENGTH
    ax.plot(
        [x1, x2],
        [y1, y2],
        "o-",
        label="Free Length" if i == 0 else "_nolegend_",
    )

    xm_free = (x1 + x2) / 2
    ym_free = (y1 + y2) / 2

    ax.annotate(
        f"{L1:.2f} m",
        xy=(xm_free, ym_free),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=8,
        rotation=ang,
        rotation_mode="anchor",
        color="blue",
    )

    # Prestress annotation near anchor head
    ax.annotate(
        f"P = {prestress:.0f} kN\nP_block = {P_block:.0f} kN",
        xy=(x1, y1),
        xytext=(-80, 0),
        textcoords="offset points",
        fontsize=8,
        color="black",
        ha="left",
        va="center",
        bbox=dict(
            boxstyle="round,pad=0.2",
            fc="white",
            ec="black",
            lw=0.5
        ),
    )

    # DRAW BOND LENGTH
    ax.plot(
        [x2, x3],
        [y2, y3],
        "o--",
        label="Bond Length" if i == 0 else "_nolegend_",
    )

    ax.annotate(
        f"R = {R_bond:.0f} kN",
        xy=(x2, y2),
        xytext=(10, 0),
        textcoords="offset points",
        fontsize=8,
        color="darkgreen",
        ha="left",
        va="center",
        bbox=dict(
            boxstyle="round,pad=0.2",
            fc="white",
            ec="darkgreen",
            lw=0.5
        ),
    )

    xm_bond = (x2 + x3) / 2
    ym_bond = (y2 + y3) / 2

    ax.annotate(
        f"{L2:.2f} m",
        xy=(xm_bond, ym_bond),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=8,
        rotation=ang,
        rotation_mode="anchor",
        color="green",
    )

    table.append(
        {
            "Anchor": i + 1,
            "X1": x1,
            "Y1": y1,
            "X2": x2,
            "Y2": y2,
            "X3": x3,
            "Y3": y3,
            "L_free (m)": L1,
            "L_bond (m)": L2,
            "Strands": strands,
            "Steel Area (mm2)": A,
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
            "FS": FS_val,
        }
    )

# DRAW WALL
ax.plot([x_ref, x_ref], [y_excav, y_wall], "k-", linewidth=3)

# Excavation
ax.plot([x_ref, x_ref - L_excav], [y_excav, y_excav], "k-", linewidth=2)

# STRATIGRAPHY
for layer in stratigraphy:
    y_layer = layer["y"]
    L_layer = layer["L"]
    name = layer["name"]

    ax.plot(
        [x_ref, x_ref + L_layer],
        [y_layer, y_layer],
        "k:",
        linewidth=1.5
    )

    x_label = x_ref + L_layer

    ax.text(
        x_label,
        y_layer + 0.1,
        f"{name}",
        fontsize=8,
        va="bottom",
        ha="left",
    )

    ax.text(
        x_label,
        y_layer - 0.1,
        f"{y_layer:.2f} m",
        fontsize=8,
        va="top",
        ha="left",
        color="gray",
    )

# BOREHOLE
ax.plot(
    [borehole_x, borehole_x],
    [y_excav - 3, y_wall],
    color="red",
    linestyle="--",
    linewidth=2,
)

ax.text(
    borehole_x,
    y_wall + 0.2,
    borehole_id,
    fontsize=10,
    va="bottom",
    ha="center",
    color="red",
)

ax.set_aspect("equal", adjustable="datalim")
ax.set_xlabel("Horizontal coordinate (m)")
ax.set_ylabel("Elevation (m)")
ax.grid(True)
ax.legend()

df_res = pd.DataFrame(table)

# Save graph
tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
plt.savefig(tmpfile.name, dpi=300, bbox_inches="tight")
graph_path = tmpfile.name


# =============================================================
# TAB 3 – RESULTS (SEM EXPORT)
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
        return (
            "background-color:#c8f7c5" if v == "OK" else "background-color:#f7c5c5"
        )

    st.table(
        df_check.style.applymap(
            color_check,
            subset=["Block Check", "Bond Check"],
        )
    )


# =============================================================
# TAB 4 – BULB LOAD (SEM EXPORT PDF)
# =============================================================
with tab_bolbo:
    st.subheader("Bulb Load Calculation (using Prestress and ABS(angle))")

    colA, colB, colC, colD = st.columns(4)

    with colA:
        H = y_wall - y_excav
        st.number_input("Wall height (m)", value=H, disabled=True)

    with colB:
        esp = st.number_input("Wall thickness (m)", value=esp)
    with colC:
        afast = st.number_input("Anchor spacing (m)", value=afast)
    with colD:
        A_inf = st.number_input("Influence area (m)", value=A_inf)

    carga_parede = H * esp * 25

    bulb_rows = []
    V_total = 0

    for idx, row in df_res.iterrows():
        P = row["Prestress (kN)"]
        ang = data[idx]["angle"]
        V = P * math.sin(math.radians(abs(ang)))
        V_total += V

        bulb_rows.append(
            {"Anchor": row["Anchor"], "Prestress": P, "Angle": ang, "V": V}
        )

    df_bh = pd.DataFrame(bulb_rows)

    V_metro = V_total / afast
    C_bolbo = V_metro * A_inf + carga_parede * A_inf

    st.dataframe(df_bh, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Sum V (kN)", f"{V_total:.2f}")
    col2.metric("V per meter (kN/m)", f"{V_metro:.2f}")
    col3.metric("Bulb load (kN)", f"{C_bolbo:.2f}")

# =============================================================
# TAB 5 – EXPORT (FINAL)
# =============================================================
with tab_export:
    st.header("Export Data and Reports")

    # ---------------------------------------------------------
    # BUILD CSV EXPORT PAYLOAD
    # ---------------------------------------------------------
    geo_payload = {
        "section_name": section_name,
        "y_excav": y_excav,
        "L_excav": L_excav,
        "y_wall": y_wall,
        "stratigraphy": stratigraphy,
        "borehole_id": borehole_id,
        "borehole_x": borehole_x,
        "esp": esp,
        "afast": afast,
        "A_inf": A_inf,
        "A_strand": A_strand,
        "delta_L": delta_L,
    }

    df_export = pd.DataFrame(
        [{**d, **geo_payload, "geo_json": json.dumps(geo_payload)} for d in data]
    )

    # ---------------------------------------------------------
    # EXPORT CSV
    # ---------------------------------------------------------
    st.subheader("Export CSV")

    st.download_button(
        "Download ALL (CSV)",
        df_export.to_csv(index=False).encode("utf-8"),
        "anchors_export.csv",
        mime="text/csv",
    )

    st.markdown("---")

# ---------------------------------------------------------
# EXPORT PDF
# ---------------------------------------------------------
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
        A_inf,
    )

    st.download_button(
        "Download PDF Report",
        data=pdf_bytes,
        file_name="anchor_report.pdf",
        mime="application/pdf",
)


    st.markdown("---")

    # ---------------------------------------------------------
    # EXPORT DXF
    # ---------------------------------------------------------
    st.subheader("Export DXF")

    if st.button("Download DXF"):
        dxf_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".dxf")
        dxf_path = dxf_tmp.name

        export_dxf(
            filepath=dxf_path,
            data=data,
            stratigraphy=stratigraphy,
            x_ref=x_ref,
            y_excav=y_excav,
            y_wall=y_wall,
            L_excav=L_excav,
            borehole_x=borehole_x,
            borehole_id=borehole_id
        )

        with open(dxf_path, "rb") as f:
            st.download_button(
                "Download DXF File",
                data=f.read(),
                file_name=f"{section_name}_anchors.dxf",
                mime="application/dxf"
            )

        try:
            os.unlink(dxf_path)
        except Exception:
            pass

# =============================================================
# TAB – CALCULATION METHOD
# =============================================================
with tab_calc:
    st.header("Calculation Methodology")

    st.write(
        f"""
This section documents all equations and assumptions used in the program.

## 1. Geometry

Each anchor is defined by:
- Head coordinates (X1, Y1)
- Inclination angle θ (degrees)
- Free length L_free
- Bond length L_bond

Coordinates:

    X2 = X1 + L_free * cos(θ)
    Y2 = Y1 + L_free * sin(θ)
    X3 = X2 + L_bond * cos(θ)
    Y3 = Y2 + L_bond * sin(θ)

## 2. Steel Area

    A = n_strands * {A_strand} mm²

User-defined parameter (default = 140 mm²).

## 3. Wedge Slip Loss

Slip δ = {delta_L} mm (user-editable)

    ΔP_slip = (E * A / L_free_mm) * δ / 1000

## 4. Block Force

    P_block = P_prestress + ΔP_slip

## 5. Steel Ultimate Capacity

    P_max = A * f_steel / 1000

where f_steel = 1440 MPa.

Check: OK if P_block < P_max.

## 6. Bond Resistance

    R_bond = L_bond * π * d * α * τ / FS

All parameters user-controlled.

## 7. Vertical Component

    V = P_prestress * sin(|θ|)

## 8. Wall Load

    carga_parede = H * esp * 25

## 9. Bulb Load

    V_total = Σ V
    V_m = V_total / spacing
    C_bolbo = V_m * A_inf + carga_parede * A_inf

## 10. Exports

You can export:
- Full CSV including section name and design parameters
- Full PDF report
- Full DXF geometry with layers:
  ANCHOR_FREE, ANCHOR_BOND, ANCHOR_LABEL, WALL, EXCAVATION, STRATIGRAPHY, BOREHOLE
"""
    )


