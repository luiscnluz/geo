import streamlit as st
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import io
from datetime import datetime

# =========================
# Dados base (catálogo)
# =========================
def carregar_microestacas() -> pd.DataFrame:
    microestacas = {
        "diam_ext_mm": [88.9, 88.9, 88.9, 101.6, 114.3, 114.3, 127.0, 139.7, 177.8, 177.8, 177.8],
        "esp_mm":      [6.5, 7.5, 9.5, 9.0, 7.0, 9.0, 9.0, 9.0, 9.0, 10.0, 11.5],
        "A_cm2":       [16.83, 19.18, 23.70, 26.18, 23.60, 29.77, 33.36, 36.95, 47.73, 52.72, 60.08],
        "I_cm4":       [144, 160, 189, 283, 341, 416, 584, 793, 1710, 1860, 2090],
        "i_cm":        [2.92, 2.89, 2.83, 3.29, 3.80, 3.74, 4.18, 4.63, 5.98, 5.94, 5.89],
        "w_cm3":       [32.31, 36.02, 42.59, 55.74, 59.64, 72.70, 91.83, 113.45, 191.66, 209.34, 234.63],
    }
    df = pd.DataFrame(microestacas)
    df["secao"] = "CHS " + df["diam_ext_mm"].astype(str) + "x" + df["esp_mm"].astype(str)
    df.set_index("secao", inplace=True)
    return df

# =========================
# Cálculo resistente
# =========================
def resistencia(dim_ext, espessura, esp_sacrificio, L_crit, fyd, E_aco, fyk):
    area = (math.pi/4) * ((dim_ext - (2*esp_sacrificio))**2 - (dim_ext - 2*espessura)**2) * 1e-2
    inercia = (math.pi/64) * (dim_ext**4 - (dim_ext - 2*(espessura - esp_sacrificio))**4) * 1e-4

    mrd = ((2 * inercia * 1e-8 * fyd * 1e3) / (dim_ext * 1e-3))
    vrd = (2 * area * 1e-4 / math.pi) * fyk * 1e3 / math.sqrt(3)
    nrd = area * 1e-4 * fyd * 1e3

    i = math.sqrt(inercia / area) * 1e-2
    lamb = L_crit / (i * math.pi * math.sqrt(E_aco * 1e3 / fyd))

    a = 0.21
    fi = 0.5 * (1 + a * (lamb - 0.2) + lamb**2)
    x = 1 / (fi + math.sqrt(fi**2 - lamb**2))

    nbrd = nrd * x
    ntd_unioes_ext = nrd * 0.75
    ntd_macho_femea = nrd * 0.4

    return area, inercia, mrd, vrd, i, lamb, a, fi, x, nrd, nbrd, ntd_unioes_ext, ntd_macho_femea

# =========================
# PDF
# =========================
def _desenho_secao(fig, ax, dim_ext, espessura, titulo):
    R_ext = dim_ext / 2 / 1000
    R_int = (dim_ext - 2 * espessura) / 2 / 1000
    ax.add_artist(plt.Circle((0,0), R_ext, fill=False, lw=2))
    ax.add_artist(plt.Circle((0,0), R_int, fill=False, lw=1.5, ls="--"))
    ax.set_aspect("equal", "box")
    ax.set_xlim(-R_ext*1.2, R_ext*1.2)
    ax.set_ylim(-R_ext*1.2, R_ext*1.2)
    ax.set_title(titulo)

def gerar_pdf_bytes(res: dict) -> bytes:
    simbolo = "✓" if res["verifica"] else "✗"
    estado = "PASSA" if res["verifica"] else "CHUMBA"

    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig1, ax1 = plt.subplots(figsize=(8.27, 11.69))
        ax1.axis("off")

        linhas = [
            "Resultados da Verificação de Microestaca",
            f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Secção: {res['secao']}",
            f"D_ext: {res['dim_ext']:.2f} mm",
            f"Espessura: {res['espessura']:.2f} mm",
            f"Esp. sacrifício: {res['esp_sacrificio']:.2f} mm",
            f"L_crit: {res['L_crit']:.2f} m",
            f"Ned: {res['Ned']:.2f} kN",
            "",
            f"A: {res['area']:.2f} cm²",
            f"I: {res['inercia']:.2f} cm⁴",
            f"Mrd: {res['mrd']:.2f} kNm",
            f"Vrd: {res['vrd']:.2f} kN",
            f"Nrd: {res['nrd']:.2f} kN",
            f"Nbrd: {res['nbrd']:.2f} kN",
            f"λ: {res['lamb']:.3f}",
            f"φ: {res['fi']:.3f}",
            f"χ: {res['x']:.3f}",
            "",
            f"Verificação: {simbolo} {estado}",
        ]

        for i, ln in enumerate(linhas):
            ax1.text(0.05, 0.95 - i * 0.035, ln, fontsize=10, va="top")

        pdf.savefig(fig1, bbox_inches="tight")
        plt.close(fig1)

        fig2, ax2 = plt.subplots(figsize=(6,6))
        _desenho_secao(fig2, ax2, res["dim_ext"], res["espessura"], res["secao"])
        pdf.savefig(fig2, bbox_inches="tight")
        plt.close(fig2)

    buf.seek(0)
    return buf.getvalue()

# =========================
# UI (PÁGINA STREAMLIT)
# =========================
st.title("🔩 Verificação de Microestacas — CHS")

df_micros = carregar_microestacas()
with st.expander("Catálogo de microestacas"):
    st.dataframe(df_micros, use_container_width=True)

colA, colB = st.columns(2)

with colA:
    st.subheader("Geometria")
    modo = st.radio("Como definir a secção?", ["Catálogo", "Manual"], horizontal=True)

    if modo == "Catálogo":
        secao_sel = st.selectbox("Escolhe a secção:", df_micros.index)
        dim_ext = float(df_micros.loc[secao_sel, "diam_ext_mm"])
        espessura = float(df_micros.loc[secao_sel, "esp_mm"])
    else:
        dim_ext = st.number_input("Diâmetro externo [mm]", value=139.7)
        espessura = st.number_input("Espessura [mm]", value=9.0)

    esp_sacrificio = st.number_input("Espessura de sacrifício [mm]", value=1.0)
    L_crit = st.number_input("Comprimento de encurvadura [m]", value=6.0)
    Ned = st.number_input("Ned [kN]", value=1200.0)

with colB:
    st.subheader("Materiais")
    gamma_m0 = st.number_input("γM0", value=1.00)
    fyk = st.number_input("fyk [MPa]", value=560.0)
    E_aco = st.number_input("E aço [GPa]", value=210.0)

fyd = fyk / gamma_m0

if st.button("Calcular"):
    vals = resistencia(dim_ext, espessura, esp_sacrificio, L_crit, fyd, E_aco, fyk)
    (area, inercia, mrd, vrd, i, lamb, a, fi, x, nrd, nbrd,
     ntd_unioes_ext, ntd_macho_femea) = vals

    secao = f"CHS {dim_ext}x{espessura}"
    verifica = nbrd >= Ned

    st.subheader("Resultados")

    simbolo = "✓" if verifica else "✗"
    cor = "green" if verifica else "red"

    st.write(f"**Ned:** {Ned:.2f} kN")
    st.write(f"**Nbrd:** {nbrd:.2f} kN")

    st.markdown(
        f"""
        <div style="font-size:22px; font-weight:bold; color:{cor};">
            Verificação: {simbolo} {"Verifica a segurança!" if verifica else "NÃO Verifica a segurança"}
        </div>
        """,
        unsafe_allow_html=True
    )

    fig, ax = plt.subplots()
    _desenho_secao(fig, ax, dim_ext, espessura, secao)
    st.pyplot(fig)

    dados_pdf = {
        "secao": secao, "dim_ext": dim_ext, "espessura": espessura,
        "esp_sacrificio": esp_sacrificio, "L_crit": L_crit, "Ned": Ned,
        "area": area, "inercia": inercia, "mrd": mrd, "vrd": vrd,
        "nrd": nrd, "nbrd": nbrd, "lamb": lamb, "fi": fi, "x": x,
        "verifica": verifica,
    }

    pdf_bytes = gerar_pdf_bytes(dados_pdf)
    st.download_button("📄 Descarregar PDF", pdf_bytes, file_name="microestaca.pdf")
