import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Sistema CGP - Manifesto e Dobragem", layout="wide")

# --- SIMULAÇÃO DE BANCO DE DADOS ---
# Em um app real, essas listas viriam da sua planilha "MASTER DOBRAGENS"
if 'banco_atletas' not in st.session_state:
    st.session_state.banco_atletas = ["João Silva", "Pedro Amado", "Ricardo M.", "Ana Souza", "Carlos D."]

if 'decolagens' not in st.session_state:
    st.session_state.decolagens = [] # Lista de decolagens criadas pela Paola

# --- INTERFACE ---
st.title("🪂 Gestão de Saltos e Dobragem - CGP")

aba_usuario = st.sidebar.radio("Acessar como:", ["Paola (Manifesto)", "Dobrador (Área de Dobragem)", "Relatórios (Financeiro)"])

# ---------------------------------------------------------
# MODO PAOLA: CRIAÇÃO DE DECOLAGENS
# ---------------------------------------------------------
if aba_usuario == "Paola (Manifesto)":
    st.header("📋 Montar Decolagem")
    with st.form("nova_decolagem"):
        col1, col2 = st.columns(2)
        with col1:
            num_decolagem = st.number_input("Número da Decolagem", min_value=1, step=1)
            dia = st.selectbox("Dia", ["Sexta", "Sábado", "Domingo"])
        with col2:
            atletas_na_vaga = st.multiselect("Selecionar Atletas/Alunos (Banco de Dados)", st.session_state.banco_atletas)
            tipo_equip = st.selectbox("Tipo de Equipamento Padrão", ["Student", "Tandem", "Atleta"])
        
        btn_criar = st.form_submit_button("Lançar Decolagem para Dobragem")
        
        if btn_criar:
            for nome in atletas_na_vaga:
                st.session_state.decolagens.append({
                    "Decolagem": num_decolagem,
                    "Atleta": nome,
                    "Equipamento": tipo_equip,
                    "Dobrador": "Pendente",
                    "Status": "Em voo",
                    "Valor": 30 if tipo_equip == "Tandem" else 25,
                    "Pagador": "Escola" if tipo_equip in ["Student", "Tandem"] else "Particular"
                })
            st.success(f"Decolagem {num_decolagem} enviada para a área de dobragem!")

# ---------------------------------------------------------
# MODO DOBRADOR: REGISTRAR QUEM DOBROU
# ---------------------------------------------------------
elif aba_usuario == "Dobrador (Área de Dobragem)":
    st.header("🔧 Área de Dobragem")
    meu_nome = st.selectbox("Selecione seu nome:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    
    if not st.session_state.decolagens:
        st.info("Aguardando a Paola lançar decolagens...")
    else:
        df_dec = pd.DataFrame(st.session_state.decolagens)
        # Mostrar apenas o que ainda não foi dobrado
        pendentes = df_dec[df_dec['Dobrador'] == "Pendente"]
        
        if pendentes.empty:
            st.success("Tudo dobrado por aqui! 🍻")
        else:
            for i, row in pendentes.iterrows():
                with st.expander(f"Vaga: {row['Atleta']} | Decolagem: {row['Decolagem']} ({row['Equipamento']})"):
                    if st.button(f"Eu dobrei este ({row['Equipamento']})", key=f"btn_{i}"):
                        st.session_state.decolagens[i]['Dobrador'] = meu_nome
                        st.session_state.decolagens[i]['Status'] = "Dobrado"
                        st.rerun()

# ---------------------------------------------------------
# MODO FINANCEIRO: FECHAMENTO DA PAOLA
# ---------------------------------------------------------
elif aba_usuario == "Relatórios (Financeiro)":
    st.header("📊 Fechamento para Pagamento")
    
    if st.session_state.db or st.session_state.decolagens:
        df_final = pd.DataFrame(st.session_state.decolagens)
        df_final = df_final[df_final['Dobrador'] != "Pendente"]
        
        if not df_final.empty:
            # Filtro para a Paola: O que a Escola Deve
            st.subheader("Dívida da Escola (Student & Tandem)")
            escola_df = df_final[df_final['Pagador'] == "Escola"]
            resumo_escola = escola_df.groupby('Dobrador')['Valor'].sum().reset_index()
            st.table(resumo_escola)
            
            # Filtro para Atletas: O que o dobrador recebe por fora
            st.subheader("Particular (Atleta paga direto ao dobrador)")
            particular_df = df_final[df_final['Pagador'] == "Particular"]
            st.table(particular_df[['Atleta', 'Dobrador', 'Valor']])
        else:
            st.warning("Nenhuma dobragem concluída ainda.")
