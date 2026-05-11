import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CONEXÃO COM GOOGLE SHEETS ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# Nome da sua planilha
NOME_PLANILHA = "MASTER DOBRAGENS" 
spreadsheet = client.open(NOME_PLANILHA)

st.set_page_config(page_title="Sistema CGP - Dobragem", layout="wide")

# --- FUNÇÃO PARA CARREGAR OS DADOS DO DIA ---
def carregar_dados_dia(nome_aba):
    try:
        # Tenta carregar a aba (Sexta, Sábado ou Domingo)
        aba = spreadsheet.worksheet(nome_aba)
        # Puxa todos os dados. O head=1 assume que a primeira linha é o cabeçalho
        dados = aba.get_all_records()
        return pd.DataFrame(dados), aba
    except Exception as e:
        st.error(f"Erro ao acessar a aba '{nome_aba}': {e}")
        return pd.DataFrame(), None

# --- INTERFACE ---
st.title("🪂 Operação de Dobragem CGP")

# Sidebar para configurações
st.sidebar.header("Configurações")
dia_selecionado = st.sidebar.selectbox("Selecione o Dia:", ["Sexta", "Sábado", "Domingo"])
dobrador_atual = st.sidebar.selectbox("Seu Nome (Dobrador):", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])

df, aba_sheet = carregar_dados_dia(dia_selecionado)

if not df.empty:
    st.subheader(f"Lista de Decolagens - {dia_selecionado}")
    
    # Criamos os cards para cada linha da planilha
    for index, row in df.iterrows():
        # Verificamos o que está na Coluna C (que no Python é o nome da coluna no cabeçalho)
        # IMPORTANTE: No seu Excel/Sheets, o título da Coluna C deve ser exatamente "Dobrador"
        # Se o título for outro, mude 'Dobrador' abaixo para o nome que está na sua planilha.
        status_dobrador = str(row.get('Dobrador', '')).strip()

        # Se a coluna C estiver vazia, mostra o botão para assinar
        if status_dobrador == "" or status_dobrador == "0" or pd.isna(row.get('Dobrador')):
            with st.container():
                c1, c2, c3 = st.columns([1, 3, 2])
                
                with c1:
                    st.write(f"**Dec:** {row.get('Decolagem', 'S/N')}")
                with c2:
                    st.write(f"**Atleta:** {row.get('Atleta', 'Vazio')} \n\n ({row.get('Equipamento', '-')})")
                with c3:
                    if st.button(f"Assinar Dobragem", key=f"btn_{index}"):
                        # Coluna C = Número 3
                        # Linha = index + 2 (1 para o cabeçalho e +1 porque o Pandas começa em 0)
                        aba_sheet.update_cell(index + 2, 3, dobrador_atual)
                        st.success(f"Registrado para {dobrador_atual}!")
                        st.rerun()
            st.divider()
        else:
            # Se já houver alguém na Coluna C, apenas mostra quem foi
            st.info(f"✅ Dec {row.get('Decolagem')} - {row.get('Atleta')} | Dobrado por: {status_dobrador}")

else:
    st.info(f"Aguardando lançamentos na aba de {dia_selecionado}...")

# Botão de atualizar manual
if st.sidebar.button("🔄 Atualizar Lista"):
    st.rerun()
