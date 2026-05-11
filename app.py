import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CONEXÃO COM GOOGLE SHEETS ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

ID_PLANILHA_NOVA = "1CZYDTUfgBhSbJqd4Rvsnb38G7rfE4LuQKdbE4Do-krw"

try:
    spreadsheet = client.open_by_key(ID_PLANILHA_NOVA)
    # Aba 1: Onde ficam os registros de saltos (log_geral)
    sheet = spreadsheet.get_worksheet(0) 
    # Aba 2: Onde ficam os nomes dos atletas presentes (manifesto)
    # Certifique-se de criar uma segunda aba na planilha chamada 'manifesto'
    try:
        sheet_manifesto = spreadsheet.worksheet("manifesto")
    except:
        sheet_manifesto = spreadsheet.add_worksheet(title="manifesto", rows="100", cols="2")
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

st.set_page_config(page_title="CGP Ops - Sistema Oficial", layout="wide")

# --- FUNÇÕES DE DADOS ---
def carregar_log():
    dados = sheet.get_all_records()
    return pd.DataFrame(dados)

def carregar_atletas_manifesto():
    lista = sheet_manifesto.col_values(1)
    return lista if lista else []

# --- INTERFACE ---
st.sidebar.title("🪂 CGP AirOps")
dia_operacao = st.sidebar.selectbox("📅 Dia da Operação", ["Sexta", "Sábado", "Domingo"])
aba = st.sidebar.radio("Navegação", ["Manifesto", "Lançar Decolagem", "Área de Dobragem", "Financeiro"])

# 1. MANIFESTO (CADASTRO DE QUEM CHEGOU)
if aba == "Manifesto":
    st.header(f"📝 Registro de Chegada - {dia_operacao}")
    with st.form("add_atleta"):
        novo_atleta = st.text_input("Nome do Paraquedista")
        if st.form_submit_button("Registrar na Área"):
            if novo_atleta:
                sheet_manifesto.append_row([novo_atleta])
                st.success(f"{novo_atleta} adicionado!")
                st.rerun()

    st.subheader("Atletas presentes no CGP")
    lista_presenca = carregar_atletas_manifesto()
    st.write(", ".join(lista_presenca) if lista_presenca else "Nenhum atleta registrado.")
    
    if st.button("Limpar Manifesto (Novo FDS)"):
        sheet_manifesto.clear()
        st.rerun()

# 2. LANÇAR DECOLAGEM
elif aba == "Lançar Decolagem":
    st.header(f"✈️ Montar Voo - {dia_operacao}")
    atletas_opcoes = carregar_atletas_manifesto()
    
    with st.expander("➕ Lançar Nova Vaga", expanded=True):
        c1, c2, c3 = st.columns(3)
        num_dec = c1.number_input("Nº Decolagem", min_value=1, step=1)
        atleta = c2.selectbox("Atleta", atletas_opcoes) if atletas_opcoes else c2.text_input("Nome (Manifesto Vazio)")
        equip = c3.selectbox("Equipamento", ["Student", "Tandem", "Atleta"])
        
        if st.button("Lançar no Sistema"):
            valor = 30 if equip == "Tandem" else 25
            pagador = "Escola" if equip != "Atleta" else "Particular"
            sheet.append_row([dia_operacao, num_dec, atleta, equip, valor, pagador, ""])
            st.success("Voo atualizado!")
            st.rerun()

    st.divider()
    df_dia = carregar_log()
    if not df_dia.empty:
        df_dia = df_dia[df_dia['Dia'] == dia_operacao]
        for d in sorted(df_dia['Decolagem'].unique()):
            st.markdown(f'**DECOLAGEM {d}**')
            vagas = df_dia[df_dia['Decolagem'] == d]
            for _, v in vagas.iterrows():
                status = "🟢" if v['Dobrador'] else "🟡"
                st.write(f"{status} {v['Atleta']} - {v['Equipamento']} ({v['Dobrador']})")

# 3. ÁREA DE DOBRAGEM
elif aba == "Área de Dobragem":
    st.header(f"🔧 Dobragem - {dia_operacao}")
    meu_nome = st.selectbox("Dobrador:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    df_dobra = carregar_log()
    if not df_dobra.empty:
        pendentes = df_dobra[(df_dobra['Dia'] == dia_operacao) & (df_dobra['Dobrador'] == "")]
        for index, vaga in pendentes.iterrows():
            col1, col2, col3 = st.columns([1, 3, 2])
            col1.write(f"D{vaga['Decolagem']}")
            col2.write(f"**{vaga['Atleta']}**")
            if col3.button("Assinar", key=f"b_{index}"):
                sheet.update_cell(index + 2, 7, meu_nome)
                st.rerun()

# 4. FINANCEIRO (DASHBOARD COMPLETO)
elif aba == "Financeiro":
    st.header("💰 Fechamento Gerencial")
    df_fin = carregar_log()
    if not df_fin.empty:
        df_ok = df_fin[df_fin['Dobrador'] != ""].copy()
        
        # --- DASHBOARD ESCOLA ---
        st.subheader("🏫 Resumo Escola (Student/Tandem)")
        esc = df_ok[df_ok['Pagador'] == "Escola"]
        if not esc.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Students", len(esc[esc['Equipamento'] == "Student"]))
            c2.metric("Tandems", len(esc[esc['Equipamento'] == "Tandem"]))
            c3.metric("Total Escola", f"R$ {esc['Valor'].sum()},00")
            
            resumo_pag = esc.groupby('Dobrador').agg(Qtd=('Valor','count'), Total_Reais=('Valor','sum')).reset_index()
            st.table(resumo_pag)
        
        # --- EXTRATO INDIVIDUAL ---
        st.divider()
        st.subheader("👤 Extrato Individual")
        user = st.selectbox("Consultar:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
        meu_extrato = df_ok[df_ok['Dobrador'] == user]
        if not meu_extrato.empty:
            st.metric(f"Total para {user}", f"R$ {meu_extrato['Valor'].sum()},00")
            st.dataframe(meu_extrato)

if st.sidebar.button("🚨 RESET LOG (DOMINGO)"):
    sheet.delete_rows(2, sheet.row_count)
    st.rerun()
