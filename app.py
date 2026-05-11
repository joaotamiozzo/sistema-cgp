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
def buscar_nomes_manifesto():
    try:
        # Busca a aba 'manifesto' (ajusta para maiúscula se necessário)
        try:
            sheet = spreadsheet.worksheet("manifesto")
        except:
            sheet = spreadsheet.worksheet("Manifesto")
            
        # Puxa apenas os valores da Coluna A
        # col_values(1) pega a primeira coluna inteira
        nomes = sheet.col_values(1)
        
        # Remove o primeiro item se ele for o cabeçalho (ex: "Nome" ou "Atleta")
        if nomes:
            return nomes[1:] 
        return []
    except Exception as e:
        st.error(f"Erro ao buscar coluna A: {e}")
        return []

# --- NA INTERFACE DO APP ---
if usuario == "Paola (Manifesto)":
    st.header("📋 Atletas no Manifesto")
    
    lista_atletas = buscar_nomes_manifesto()
    
    if lista_atletas:
        # Exibe os nomes em uma lista limpa ou em um selectbox
        st.write(f"Existem **{len(lista_atletas)}** atletas registrados hoje:")
        
        # Criando uma tabela simples apenas com os nomes
        df_nomes = pd.DataFrame(lista_atletas, columns=["Nome do Atleta"])
        st.table(df_nomes) 
    else:
        st.warning("Nenhum nome encontrado na Coluna A da aba Manifesto.")

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
