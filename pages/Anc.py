import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Ancoragens", layout="centered")
st.title("Cálculo Dinâmico de Ancoragens")

# ---------- PARÂMETROS GERAIS ----------
st.subheader("Configuração")
n = st.number_input("Número de ancoragens", min_value=1, max_value=20, value=2, step=1)
limite_x = st.number_input("Coordenada X do limite (linha vertical)", value=20.0)
fundo_esc = st.number_input("Coordenada y do fundo de escavação (linha horizontal)", value=0.00)

# ---------- DADOS DAS ANCORAGENS ----------
st.subheader("📥 Dados das Ancoragens")
dados = []
for i in range(n):
    with st.expander(f"Ancoragem {i+1}"):
        x1 = st.number_input(f"X inicial - Ancoragem {i+1}", key=f"x_{i}", value=0.0)
        y1 = st.number_input(f"Y inicial - Ancoragem {i+1}", key=f"y_{i}", value=0.0)
        ang = st.number_input(f"Ângulo (graus) - Ancoragem {i+1}", key=f"ang_{i}", value=-45.0)
        L_livre = st.number_input(f"Comprimento livre (m) - Ancoragem {i+1}", key=f"livre_{i}", value=10.0)
        L_bolbo = st.number_input(f"Comprimento do bolbo (m) - Ancoragem {i+1}", key=f"bolbo_{i}", value=10.0)
        preesforco = st.number_input(f"Pré-esforço (kN) - Ancoragem {i+1}", key=f"preesforco_{i}", value=0.0)
        dados.append({"x1": x1, "y1": y1, "angulo": ang, "livre": L_livre, "bolbo": L_bolbo, "preesforco": preesforco})

# ---------- CÁLCULOS ----------
def calcula(x1, y1, ang, L1, L2):
    rad = math.radians(ang)
    x2 = x1 + L1 * math.cos(rad)
    y2 = y1 + L1 * math.sin(rad)
    x3 = x2 + L2 * math.cos(rad)
    y3 = y2 + L2 * math.sin(rad)
    return x2, y2, x3, y3

# ---------- DESENHO ----------
fig, ax = plt.subplots()
tabela = []

for i, d in enumerate(dados):
    x1, y1 = d["x1"], d["y1"]
    ang, L1, L2 = d["angulo"], d["livre"], d["bolbo"]
    x2, y2, x3, y3 = calcula(x1, y1, ang, L1, L2)

    # Linhas
    ax.plot([x1, x2], [y1, y2], 'o-', label=f"Compr. Livre {i+1}")
    ax.plot([x2, x3], [y2, y3], 'o--', label=f"Bolbo {i+1}")

    # Anotações
    ax.annotate(f"P1 ({x1:.1f}, {y1:.1f})", (x1, y1), fontsize=8, xytext=(0,8), textcoords="offset points", ha='center')
    ax.annotate(f"P2 ({x2:.1f}, {y2:.1f})", (x2, y2), fontsize=8, xytext=(0,8), textcoords="offset points", ha='center')
    ax.annotate(f"P3 ({x3:.1f}, {y3:.1f})", (x3, y3), fontsize=8, xytext=(0,8), textcoords="offset points", ha='center')
    ax.annotate(f"{L1:.1f} m", ((x1+x2)/2, (y1+y2)/2), fontsize=8, xytext=(0,-10), textcoords="offset points", ha='center')
    ax.annotate(f"{L2:.1f} m", ((x2+x3)/2, (y2+y3)/2), fontsize=8, xytext=(0,-10), textcoords="offset points", ha='center')

    # Dados para tabela
    tabela.extend([
        {"Ancoragem": i+1, "Ponto": "P1", "X": x1, "Y": y1, "Ângulo": ang, "Comp_Livre": L1, "Comp_Bolbo": L2, "PreEsforco_kN": d["preesforco"]},
        {"Ancoragem": i+1, "Ponto": "P2", "X": x2, "Y": y2, "Ângulo": ang, "Comp_Livre": L1, "Comp_Bolbo": L2, "PreEsforco_kN": d["preesforco"]},
        {"Ancoragem": i+1, "Ponto": "P3", "X": x3, "Y": y3, "Ângulo": ang, "Comp_Livre": L1, "Comp_Bolbo": L2, "PreEsforco_kN": d["preesforco"]},
    ])

# Linha do limite
ax.axvline(x=limite_x, color='gray', linestyle='--')
ax.annotate(f"Limite X = {limite_x:.2f}", (limite_x, ax.get_ylim()[1]), xytext=(5, -20),
            textcoords="offset points", fontsize=8, color='gray')
   
# Linha do fundo de escavação
ax.axhline(y=fundo_esc, color='purple', linestyle='--')
ax.annotate(f"Fundo escavação = {fundo_esc:.2f}", (ax.get_xlim()[1], fundo_esc), xytext=(-60, 10),
        textcoords="offset points", fontsize=8, color='purple')

# Aspeto do gráfico
ax.set_aspect('equal', adjustable='datalim')
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.grid(True)
ax.legend()
st.pyplot(fig)

# ---------- TABELA DE RESULTADOS ----------
df = pd.DataFrame(tabela)
st.subheader("📄 Tabela de Coordenadas e Parâmetros")
st.dataframe(df)


st.markdown("---")
st.caption("Cálculo Dinâmico de Ancoragens | 2025")
