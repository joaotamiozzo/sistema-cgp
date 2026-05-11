import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CONEXÃO COM A NOVA PLANILHA ---
# Certifique-se de que o e-mail do robô está compartilhado nesta nova planilha!
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# ⚠️ AJUSTE AQUI: Coloque o nome exato da sua planilha nova
Manifest_OPS = "Manifest_OPS" 

try:
    spreadsheet = client.open(Manifest_OPS)
    sheet = spreadsheet.get_worksheet(0) # Pega a primeira aba da planilha
except Exception as e:
    st.error(f"Erro ao conectar na planilha: {e}")
    st.stop()

st.set_page_config(page_title="CGP Ops - Real Time", layout="wide")

# --- FUNÇÕES DE SINCRONIZAÇÃO ---
def carregar_dados():
    dados = sheet.get_all_records()
    return pd.DataFrame(dados)

def salvar_no_google(nova_vaga):
    sheet.append_row(list(nova_vaga.values()))

def assinar_no_google(linha_index, nome_dobrador):
    # Coluna G (Dobrador) é a 7. No gspread, a linha 1 é o cabeçalho, então usamos index + 2
    sheet.update_cell(linha_index + 2, 7, nome_dobrador)

# --- INTERFACE ---
st.sidebar.title("🪂 CGP AirOps")
dia_operacao = st.sidebar.selectbox("📅 Dia da Operação", ["Sexta", "Sábado", "Domingo"])
aba = st.sidebar.radio("Navegação", ["Manifesto/Decolagem", "Área de Dobragem", "Dashboard Escola", "Extrato Dobrador"])

# Carrega os dados da nuvem a cada ação
df_db = carregar_dados()

# 1. MANIFESTO E DECOLAGEM (PAOLA)
if aba == "Manifesto/Decolagem":
    st.header(f"✈️ Montar Voo - {dia_operacao}")
    with st.form("form_voo"):
        c1, c2, c3 = st.columns(3)
        num_dec = c1.number_input("Nº Decolagem", min_value=1, step=1)
        atleta = c2.text_input("Nome do Atleta")
        equip = c3.selectbox("Equipamento", ["Student", "Tandem", "Atleta"])
        
        if st.form_submit_button("Lançar no Sistema"):
            valor = 30 if equip == "Tandem" else 25
            pagador = "Escola" if equip != "Atleta" else "Particular"
            vaga = {
                "Dia": dia_operacao, "Decolagem": num_dec, "Atleta": atleta,
                "Equipamento": equip, "Valor": valor, "Pagador": pagador, "Dobrador": ""
            }
            salvar_no_google(vaga)
            st.success("Lançado com sucesso!")
            st.rerun()

# 2. ÁREA DE DOBRAGEM (GURIS)
elif aba == "Área de Dobragem":
    st.header(f"🔧 Dobragem - {dia_operacao}")
    meu_nome = st.selectbox("Selecione seu nome:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    
    if not df_db.empty:
        # Filtra apenas o que é do dia e que o campo Dobrador está vazio
        pendentes = df_db[(df_db['Dia'] == dia_operacao) & (df_db['Dobrador'] == "")]
        
        if pendentes.empty:
            st.info("Tudo dobrado por aqui!")
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
    st.header("🏫 Fechamento Escola (Student/Tandem)")
    if not df_db.empty:
        # Apenas o que já foi dobrado e é pago pela escola
        df_esc = df_db[(df_db['Dobrador'] != "") & (df_db['Pagador'] == "Escola")]
        
        if not df_esc.empty:
            c1, c2 = st.columns(2)
            c1.metric("Total Students", len(df_esc[df_esc['Equipamento'] == "Student"]))
            c2.metric("Total Tandems", len(df_esc[df_esc['Equipamento'] == "Tandem"]))
            
            resumo = df_esc.groupby('Dobrador').agg(Qtd=('Valor','count'), Total=('Valor','sum')).reset_index()
            st.table(resumo)
        else:
            st.info("Nenhum registro da escola ainda.")

# 4. EXTRATO DOBRADOR
elif aba == "Extrato Dobrador":
    st.header("👤 Meu Extrato Individual")
    nome_consulta = st.selectbox("Ver meu resumo:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    
    if not df_db.empty:
        meus_trabalhos = df_db[df_db['Dobrador'] == nome_consulta]
        if not meus_trabalhos.empty:
            st.metric("Total a Receber (Geral)", f"R$ {meus_trabalhos['Valor'].sum()},00")
            st.dataframe(meus_trabalhos)
        else:
            st.info("Você ainda não assinou nenhuma dobragem.")

# RESET GERAL (SÓ APARECE NO FINAL DO FINANCEIRO)
if st.sidebar.button("🚨 RESET TOTAL (LIMPAR TUDO)"):
    # Limpa a planilha a partir da segunda linha
    sheet.delete_rows(2, sheet.row_count)
    st.rerun()
