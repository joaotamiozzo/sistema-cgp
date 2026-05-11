import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CONEXÃO COM A NOVA PLANILHA ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# ⚠️ COLOQUE O ID DA PLANILHA AQUI (Aquele código longo da URL)
1CZYDTUfgBhSbJqd4Rvsnb38G7rfE4LuQKdbE4Do-krw = "1CZYDTUfgBhSbJqd4Rvsnb38G7rfE4LuQKdbE4Do-krw" 

try:
    # Conectar pelo ID é muito mais seguro que pelo nome
    spreadsheet = client.open_by_key(1CZYDTUfgBhSbJqd4Rvsnb38G7rfE4LuQKdbE4Do-krw)
    sheet = spreadsheet.get_worksheet(0) 
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# --- O RESTO DO CÓDIGO SEGUE IGUAL ---
st.set_page_config(page_title="CGP Ops - Real Time", layout="wide")

def carregar_dados():
    try:
        dados = sheet.get_all_records()
        return pd.DataFrame(dados)
    except:
        # Caso a planilha esteja totalmente vazia (sem cabeçalho)
        return pd.DataFrame()

def salvar_no_google(nova_vaga):
    sheet.append_row(list(nova_vaga.values()))

def assinar_no_google(linha_index, nome_dobrador):
    # Coluna G é a 7ª. 
    sheet.update_cell(linha_index + 2, 7, nome_dobrador)

# --- INTERFACE ---
st.sidebar.title("🪂 CGP AirOps")
dia_operacao = st.sidebar.selectbox("📅 Dia da Operação", ["Sexta", "Sábado", "Domingo"])
aba = st.sidebar.radio("Navegação", ["Manifesto/Decolagem", "Área de Dobragem", "Dashboard Escola", "Extrato Dobrador"])

df_db = carregar_dados()

# 1. MANIFESTO E DECOLAGEM
if aba == "Manifesto/Decolagem":
    st.header(f"✈️ Montar Voo - {dia_operacao}")
    with st.form("form_voo"):
        c1, c2, c3 = st.columns(3)
        num_dec = c1.number_input("Nº Decolagem", min_value=1, step=1)
        atleta = c2.text_input("Nome do Atleta")
        equip = c3.selectbox("Equipamento", ["Student", "Tandem", "Atleta"])
        
        if st.form_submit_button("Lançar no Sistema"):
            if atleta:
                valor = 30 if equip == "Tandem" else 25
                pagador = "Escola" if equip != "Atleta" else "Particular"
                vaga = {
                    "Dia": dia_operacao, "Decolagem": num_dec, "Atleta": atleta,
                    "Equipamento": equip, "Valor": valor, "Pagador": pagador, "Dobrador": ""
                }
                salvar_no_google(vaga)
                st.success("Lançado!")
                st.rerun()
            else:
                st.warning("Coloque o nome do atleta!")

# 2. ÁREA DE DOBRAGEM
elif aba == "Área de Dobragem":
    st.header(f"🔧 Dobragem - {dia_operacao}")
    meu_nome = st.selectbox("Selecione seu nome:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    
    if not df_db.empty:
        # Garante que as colunas Dia e Dobrador existem antes de filtrar
        if 'Dia' in df_db.columns and 'Dobrador' in df_db.columns:
            pendentes = df_db[(df_db['Dia'] == dia_operacao) & (df_db['Dobrador'] == "")]
            
            if pendentes.empty:
                st.info("Nada para dobrar agora.")
            else:
                for index, vaga in pendentes.iterrows():
                    with st.container():
                        c1, c2, c3 = st.columns([1, 3, 2])
                        c1.subheader(f"D{vaga['Decolagem']}")
                        c2.write(f"**{vaga['Atleta']}** ({vaga['Equipamento']})")
                        if c3.button("Assinar", key=f"btn_{index}"):
                            assinar_no_google(index, meu_nome)
                            st.rerun()
                    st.divider()

# 3. DASHBOARD ESCOLA
elif aba == "Dashboard Escola":
    st.header("🏫 Fechamento Escola")
    if not df_db.empty:
        df_esc = df_db[(df_db['Dobrador'] != "") & (df_db['Pagador'] == "Escola")]
        if not df_esc.empty:
            c1, c2 = st.columns(2)
            c1.metric("Students", len(df_esc[df_esc['Equipamento'] == "Student"]))
            c2.metric("Tandems", len(df_esc[df_esc['Equipamento'] == "Tandem"]))
            resumo = df_esc.groupby('Dobrador').agg(Qtd=('Valor','count'), Total=('Valor','sum')).reset_index()
            st.table(resumo)

# 4. EXTRATO DOBRADOR
elif aba == "Extrato Dobrador":
    st.header("👤 Meu Extrato")
    nome_consulta = st.selectbox("Nome:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    if not df_db.empty:
        meus_trabalhos = df_db[df_db['Dobrador'] == nome_consulta]
        if not meus_trabalhos.empty:
            st.metric("Total", f"R$ {meus_trabalhos['Valor'].sum()},00")
            st.dataframe(meus_trabalhos)

# RESET
if st.sidebar.button("🚨 RESET TOTAL"):
    sheet.delete_rows(2, sheet.row_count)
    st.rerun()
