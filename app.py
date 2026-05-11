import streamlit as st
import pandas as pd
from datetime import datetime

# Configurações de Página
st.set_page_config(page_title="Sistema CGP - Final de Semana", layout="wide")

# --- INICIALIZAÇÃO DO BANCO DE DADOS TEMPORÁRIO ---
# Nota: Enquanto não conectarmos ao Google Sheets, os dados ficam salvos nesta sessão.
if 'historico_geral' not in st.session_state:
    st.session_state.historico_geral = []
if 'atletas_area' not in st.session_state:
    st.session_state.atletas_area = []

# --- ESTILO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3em; }
    .card { border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🪂 CGP AirOps")
dia_operacao = st.sidebar.selectbox("📅 Dia da Operação", ["Sexta", "Sábado", "Domingo"])
aba = st.sidebar.radio("Navegação", ["Manifesto", "Lançar Decolagem", "Área de Dobragem", "Financeiro (Acumulado)"])

# ---------------------------------------------------------
# 1. MANIFESTO (QUEM CHEGOU NO FINAL DE SEMANA)
# ---------------------------------------------------------
if aba == "Manifesto":
    st.header(f"📝 Registro de Atletas - {dia_operacao}")
    with st.form("chegada"):
        nome = st.text_input("Nome do Paraquedista")
        add = st.form_submit_button("Registrar na Área")
        if add and nome:
            if nome not in st.session_state.atletas_area:
                st.session_state.atletas_area.append(nome)
                st.success(f"{nome} pronto para saltar!")
    
    st.subheader("Atletas presentes no CGP")
    st.write(", ".join(st.session_state.atletas_area) if st.session_state.atletas_area else "Ninguém registrado.")

# ---------------------------------------------------------
# 2. LANÇAR DECOLAGEM (PAOLA)
# ---------------------------------------------------------
elif aba == "Lançar Decolagem":
    st.header(f"✈️ Montar Voo - {dia_operacao}")
    
    if not st.session_state.atletas_area:
        st.warning("Cadastre atletas no Manifesto primeiro.")
    else:
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                num_dec = st.number_input("Nº Decolagem", min_value=1, step=1)
            with col2:
                atleta = st.selectbox("Atleta", st.session_state.atletas_area)
            with col3:
                equip = st.selectbox("Equipamento", ["Student", "Tandem", "Atleta (Próprio)"])
            
            if st.button("Lançar no Sistema"):
                valor = 30 if equip == "Tandem" else 25
                pagador = "Escola" if equip in ["Student", "Tandem"] else "Particular"
                
                st.session_state.historico_geral.append({
                    "id": len(st.session_state.historico_geral),
                    "Dia": dia_operacao,
                    "Decolagem": num_dec,
                    "Atleta": atleta,
                    "Equipamento": equip,
                    "Valor": valor,
                    "Pagador": pagador,
                    "Dobrador": None
                })
                st.toast(f"Vaga de {atleta} lançada!")

# ---------------------------------------------------------
# 3. ÁREA DE DOBRAGEM (GURIS)
# ---------------------------------------------------------
elif aba == "Área de Dobragem":
    st.header(f"🔧 Dobragem - {dia_operacao}")
    meu_nome = st.selectbox("Selecionar Dobrador:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    
    # Filtra apenas o que é do dia e não foi dobrado
    pendentes = [v for v in st.session_state.historico_geral if v['Dia'] == dia_operacao and v['Dobrador'] is None]
    
    if not pendentes:
        st.info(f"Sem paraquedas pendentes para {dia_operacao}.")
    else:
        for vaga in pendentes:
            with st.container():
                c1, c2, c3 = st.columns([1, 3, 2])
                with c1:
                    st.subheader(f"D{vaga['Decolagem']}")
                with c2:
                    st.write(f"**{vaga['Atleta']}**")
                    st.caption(f"{vaga['Equipamento']}")
                with c3:
                    if st.button(f"Dobrei", key=f"job_{vaga['id']}"):
                        vaga['Dobrador'] = meu_nome
                        st.rerun()
                st.divider()

# ---------------------------------------------------------
# 4. FINANCEIRO (ACUMULADO DO FDS)
# ---------------------------------------------------------
elif aba == "Financeiro (Acumulado)":
    st.header("💰 Fechamento do Final de Semana")
    
    df_tudo = pd.DataFrame(st.session_state.historico_geral)
    
    if df_tudo.empty:
        st.info("Aguardando registros para calcular o financeiro.")
    else:
        # Filtra apenas o que já foi assinado pelo dobrador
        df_dobrado = df_tudo[df_tudo['Dobrador'].notna()]
        
        # TABELA GERAL PARA A RECEPÇÃO
        st.subheader("🏫 Total devido pela Escola (Student/Tandem)")
        escola = df_dobrado[df_dobrado['Pagador'] == "Escola"]
        if not escola.empty:
            resumo_escola = escola.groupby('Dobrador')['Valor'].sum().reset_index()
            st.table(resumo_escola)
        
        # CONSULTA INDIVIDUAL
        st.divider()
        st.subheader("👤 Extrato do Dobrador")
        consulta = st.selectbox("Verificar nome:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
        meus_dados = df_dobrado[df_dobrado['Dobrador'] == consulta]
        
        if not meus_dados.empty:
            col_a, col_b = st.columns(2)
            col_a.metric("Total Geral", f"R$ {meus_dados['Valor'].sum()}")
            col_b.metric("Qtd Dobragens", len(meus_dados))
            
            # Detalhamento por dia para facilitar o acerto
            st.write("Detalhamento por dia:")
            resumo_dia = meus_dados.groupby('Dia')['Valor'].sum().reset_index()
            st.dataframe(resumo_dia)
            
            with st.expander("Ver todos os atletas que dobrei"):
                st.dataframe(meus_dados[["Dia", "Decolagem", "Atleta", "Equipamento", "Valor"]])
        else:
            st.write("Nenhum registro encontrado para este dobrador.")
