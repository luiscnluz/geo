import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Verificação Ancoragens", layout="wide")
st.title("Verificação de Segurança das Ancoragens")

# Número de ancoragens
n = st.number_input("Número de ancoragens", min_value=1, max_value=10, value=2, step=1)

# Entrada dos dados das ancoragens
dados = []
for i in range(n):
    with st.expander(f"Ancoragem {i+1}"):
        x1 = st.number_input(f"X1 (m) - Ancoragem {i+1}", value=2.0)
        y1 = st.number_input(f"Y1 (m) - Ancoragem {i+1}", value=8.0)
        ang = st.number_input(f"Ângulo (°) - Ancoragem {i+1}", value=-45.0)
        Llivre = st.number_input(f"Comprimento livre L (m) - Ancoragem {i+1}", value=10.0)
        Lbolbo = st.number_input(f"Comprimento bolbo L (m) - Ancoragem {i+1}", value=10.0)
        preesforco = st.number_input(f"Pré-esforço (kN) - Ancoragem {i+1}", value=100.0)
        cordoes = st.number_input(f"Nº de cordões - Ancoragem {i+1}", min_value=1, value=3)
        diam_furo = st.number_input(f"Diâmetro do furo (mm) - Ancoragem {i+1}", value=100)
        alfa = st.number_input(f"Alfa (coef. aderência) - Ancoragem {i+1}", value=0.6, format="%.2f")
        tau = st.number_input(f"Tensão tangencial (kN/m²) - Ancoragem {i+1}", value=150.0)
        FS = st.number_input(f"Fator de Segurança (FS) - Ancoragem {i+1}", value=1.5)

        dados.append({
            "x1": x1, "y1": y1, "angulo": ang, "livre": Llivre, "bolbo": Lbolbo,
            "preesforco": preesforco, "cordoes": cordoes,
            "diam_furo_mm": diam_furo, "alfa": alfa, "tensao_tangencial": tau, "FS": FS,
        })

# Função cálculo coordenadas
def calcula(x1, y1, ang, L1, L2):
    rad = math.radians(ang)
    x2 = x1 + L1 * math.cos(rad)
    y2 = y1 + L1 * math.sin(rad)
    x3 = x2 + L2 * math.cos(rad)
    y3 = y2 + L2 * math.sin(rad)
    return x2, y2, x3, y3

# Cálculos e gráfico
fig, ax = plt.subplots()
tabela = []

for i, d in enumerate(dados):
    x1, y1 = d["x1"], d["y1"]
    ang, L1, L2 = d["angulo"], d["livre"], d["bolbo"]
    cordoes = d["cordoes"]
    preesforco = d["preesforco"]
    d_furo = d["diam_furo_mm"]
    alfa = d["alfa"]
    tau = d["tensao_tangencial"]
    FS = d["FS"]

    x2, y2, x3, y3 = calcula(x1, y1, ang, L1, L2)

    E = 210_000  # MPa
    A = cordoes * 140  # mm²
    L_livre_mm = L1 * 1000
    delta_L = 6  # mm
    perdas_kN = (E * A / L_livre_mm) * delta_L / 1000  # kN

    P_blocagem = preesforco + perdas_kN  # kN
    P_max = A * 0.8 * 1440 / 1000  # kN
    seguranca_blocagem = "OK" if P_blocagem < P_max else "NÃO VERIFICA"

    R_bolbo = L2 * math.pi * d_furo * 1e-3 * alfa * tau / FS  # kN
    seguranca_bolbo = "OK" if R_bolbo > P_blocagem else "NÃO VERIFICA"

    ax.plot([x1, x2], [y1, y2], 'o-', label=f"Compr. Livre {i+1}")
    ax.plot([x2, x3], [y2, y3], 'o--', label=f"Bolbo {i+1}")
    ax.annotate(f"{L1:.1f} m", ((x1+x2)/2, (y1+y2)/2), fontsize=8, xytext=(0,-10), textcoords="offset points", ha='center')
    ax.annotate(f"{L2:.1f} m", ((x2+x3)/2, (y2+y3)/2), fontsize=8, xytext=(0,-10), textcoords="offset points", ha='center')

    tabela.append({
        "Ancoragem": i+1,
        "X1": x1, "Y1": y1,
        "X2": x2, "Y2": y2,
        "X3": x3, "Y3": y3,
        "L_livre (m)": L1,
        "L_bolbo (m)": L2,
        "Cordões": cordoes,
        "Área_Preesf. (mm²)": A,
        "Pré-Esf. (kN)": preesforco,
        "Perdas por Cunhas (kN)": round(perdas_kN, 2),
        "Pblocagem (kN)": round(P_blocagem, 2),
        "Pmax (kN)": round(P_max, 2),
        "Segurança Blocagem": seguranca_blocagem,
        "R_bolbo (kN)": round(R_bolbo, 2),
        "Segurança Bolbo": seguranca_bolbo,
    })

ax.set_aspect('equal', adjustable='datalim')
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.grid(True)
ax.legend()
plt.title("Geometria das Ancoragens")

st.pyplot(fig)

df = pd.DataFrame(tabela)
st.dataframe(df)
