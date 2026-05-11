import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DE CONEXÃO ---
# O Streamlit busca automaticamente o que você salvou no "Secrets"
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# ⚠️ AJUSTE AQUI: Coloque o nome exato da sua planilha
NOME_PLANILHA = "MASTER DOBRAGENS" 
spreadsheet = client.open(NOME_PLANILHA)

st.set_page_config(page_title="Sistema de Dobragem CGP", layout="wide")

# --- FUNÇÕES DE DADOS ---
def carregar_dados(aba_nome):
    try:
        # Tenta abrir a aba com o nome exato
        aba = spreadsheet.worksheet(aba_nome)
        return pd.DataFrame(aba.get_all_records())
    except:
        try:
            # Tenta abrir com a primeira letra maiúscula (ex: Manifesto)
            aba = spreadsheet.worksheet(aba_nome.capitalize())
            return pd.DataFrame(aba.get_all_records())
        except:
            try:
                # Tenta abrir tudo em maiúsculo (ex: MANIFESTO)
                aba = spreadsheet.worksheet(aba_nome.upper())
                return pd.DataFrame(aba.get_all_records())
            except:
                return pd.DataFrame()

# --- INTERFACE DO APP ---
st.title("🪂 Sistema de Dobragem - CGP")

# Sidebar para navegação
usuario = st.sidebar.radio("Acessar como:", ["Paola (Manifesto)", "Dobrador", "Relatórios"])

if usuario == "Paola (Manifesto)":
    st.header("📋 Manifesto e Decolagens")
    st.write("Dados puxados da aba 'manifesto' da sua planilha.")
    
    df_manifesto = carregar_dados("manifesto")
    if not df_manifesto.empty:
        st.dataframe(df_manifesto)
    else:
        st.warning("Aba 'manifesto' não encontrada ou está vazia.")

elif usuario == "Dobrador":
    st.header("🔧 Área de Dobragem")
    nome_dobrador = st.selectbox("Quem é você?", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    
    # Exemplo: Mostrar decolagens de hoje (Sexta, Sábado ou Domingo)
    dia_atual = st.selectbox("Selecione o Dia:", ["sexta", "sábado", "domingo"])
    df_dia = carregar_dados(dia_atual)
    
    if not df_dia.empty:
        st.write(f"Atletas em {dia_atual}:")
        st.dataframe(df_dia)
        # Aqui podemos adicionar os botões para marcar a dobragem depois
    else:
        st.info(f"Nenhum dado encontrado na aba '{dia_atual}'.")

elif usuario == "Relatórios":
    st.header("📊 Fechamento Financeiro")
    st.write("Resumo baseado na aba 'Dashboard'")
    df_dash = carregar_dados("Dashboard")
    if not df_dash.empty:
        st.table(df_dash)
