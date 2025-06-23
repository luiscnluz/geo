import streamlit as st
import math

def calcula_area_armadura(diametro):
    return (math.pi * (diametro ** 2)) / 400

def interpretar_expressao(expr):
    try:
        nova_expr = ""
        i = 0
        while i < len(expr):
            if expr[i] == 'f':
                i += 1
                num_str = ""
                while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                    num_str += expr[i]
                    i += 1
                if num_str:
                    area = calcula_area_armadura(float(num_str))
                    nova_expr += str(area)
            else:
                nova_expr += expr[i]
                i += 1
        resultado = eval(nova_expr)
        return resultado
    except Exception as e:
        return f"Erro: {e}"

st.set_page_config(page_title="RBAT 2025.04.00", layout="centered")
st.markdown("<h2 style='text-align:center'>RBAT - Reinforcement Bar Area Tool</h2>", unsafe_allow_html=True)

st.info("Insere os diâmetros das armaduras no formato: `f12/0.20+f16/0.20` **ou** `2*f16+3*f10`")

expr = st.text_input(
    "Expressão da armadura", 
    placeholder="Ex: f12/0.20+f16/0.20 ou 2*f16+3*f10"
)

st.caption(
    "Se pretenderes calcular a área de várias barras, usa sempre o * para multiplicação. Exemplo: `2*f12` em vez de `2f12`."
)

if st.button("Calcular área") or expr:
    if expr.strip() and expr != "":
        resultado = interpretar_expressao(expr)
        if isinstance(resultado, str) and resultado.startswith("Erro"):
            st.error(resultado)
        else:
            unidade = "cm²/m" if "/" in expr else "cm²"
            st.success(f"Área = {resultado:.4f} {unidade}")

st.markdown("---")
st.caption("RBAT_2025.04.00 | 2025")
