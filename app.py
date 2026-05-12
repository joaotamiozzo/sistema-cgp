import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image

# --- 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira linha de UI) ---
try:
    img_logo = Image.open("airops_logo.png")
    st.set_page_config(page_title="AirOps - Sistema de Paraquedismo", layout="wide", page_icon=img_logo)
except:
    st.set_page_config(page_title="AirOps - Sistema de Paraquedismo", layout="wide", page_icon="🪂")

# --- 2. EXIBIÇÃO DO LOGOTIPO NO TOPO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("airops_logo.png", use_container_width=True)
    except:
        st.header("AirOps")

# --- CONEXÃO ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

ID_PLANILHA_NOVA = "1CZYDTUfgBhSbJqd4Rvsnb38G7rfE4LuQKdbE4Do-krw"

@st.cache_resource
def conectar_google():
    spreadsheet = client.open_by_key(ID_PLANILHA_NOVA)
    return spreadsheet, spreadsheet.get_worksheet(0), spreadsheet.worksheet("manifesto")

spreadsheet, sheet, sheet_manifesto = conectar_google()

st.set_page_config(page_title="CGP AirOps", layout="wide")

# --- FUNÇÕES DE DADOS COM CACHE OTIMIZADO ---
@st.cache_data(ttl=20) # Aumentado para 20s para dar fôlego ao API
def carregar_log_cache():
    return pd.DataFrame(sheet.get_all_records())

@st.cache_data(ttl=60)
def carregar_manifesto_cache():
    lista = sheet_manifesto.col_values(1)
    return sorted(lista) if lista else []

# --- NAVEGAÇÃO ---
st.sidebar.title("🪂 CGP AirOps")
if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dia_operacao = st.sidebar.selectbox("📅 Dia da Operação", ["Sexta", "Sábado", "Domingo"])
aba = st.sidebar.radio("Navegação", ["Manifesto", "Lançar Decolagem", "Área de Dobragem", "Financeiro"])

# 1. MANIFESTO
if aba == "Manifesto":
    st.header(f"📝 Registro de Chegada - {dia_operacao}")
    with st.form("add_atleta", clear_on_submit=True):
        novo_atleta = st.text_input("Nome do Paraquedista").upper()
        if st.form_submit_button("Registrar na Área"):
            if novo_atleta:
                sheet_manifesto.append_row([novo_atleta])
                st.cache_data.clear() # Limpa para atualizar a lista abaixo
                st.success(f"{novo_atleta} adicionado!")
                st.rerun()

    st.subheader("Atletas presentes no CGP")
    lista_p = carregar_manifesto_cache()
    st.write(", ".join(lista_p) if lista_p else "Manifesto vazio.")
    
    if st.button("Limpar Manifesto (Novo FDS)"):
        sheet_manifesto.clear()
        st.cache_data.clear()
        st.rerun()

# 2. LANÇAR DECOLAGEM
elif aba == "Lançar Decolagem":
    st.header(f"✈️ Montar Voo - {dia_operacao}")
    atletas_opcoes = carregar_manifesto_cache()
    
    with st.expander("➕ Lançar Nova Vaga", expanded=True):
        c1, c2, c3 = st.columns(3)
        num_dec = c1.number_input("Nº Decolagem", min_value=1, step=1)
        atleta = c2.selectbox("Atleta", atletas_opcoes) if atletas_opcoes else c2.text_input("Nome")
        equip = c3.selectbox("Equipamento", ["Student", "Tandem", "Atleta"])
        
        if st.button("Confirmar no Voo"):
            valor = 30 if equip == "Tandem" else 25
            pagador = "Escola" if equip != "Atleta" else "Particular"
            sheet.append_row([dia_operacao, int(num_dec), atleta, equip, valor, pagador, ""])
            st.cache_data.clear()
            st.success(f"Lançado!")
            st.rerun()

    st.divider()
    df_dia = carregar_log_cache()
    if not df_dia.empty:
        df_dia = df_dia[df_dia['Dia'] == dia_operacao]
        for d in sorted(df_dia['Decolagem'].unique()):
            with st.expander(f"📦 DECOLAGEM {d}", expanded=True):
                vagas = df_dia[df_dia['Decolagem'] == d]
                for _, v in vagas.iterrows():
                    status = "🟢" if v['Dobrador'] else "🟡"
                    st.write(f"{status} **{v['Atleta']}** ({v['Equipamento']}) {v['Dobrador']}")

# 3. ÁREA DE DOBRAGEM
elif aba == "Área de Dobragem":
    st.header(f"🔧 Área de Dobragem - {dia_operacao}")
    meu_nome = st.selectbox("Quem está dobrando?", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    df_dobra = carregar_log_cache()
    if not df_dobra.empty:
        pendentes = df_dobra[(df_dobra['Dia'] == dia_operacao) & (df_dobra['Dobrador'] == "")]
        if pendentes.empty:
            st.info("Tudo dobrado!")
        else:
            for index, vaga in pendentes.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 2])
                    col1.subheader(f"D{vaga['Decolagem']}")
                    col2.write(f"**{vaga['Atleta']}** ({vaga['Equipamento']})")
                    if col3.button("Assinar", key=f"job_{index}"):
                        # O segredo da velocidade: atualiza primeiro a célula, depois limpa o cache
                        sheet.update_cell(index + 2, 7, meu_nome)
                        st.cache_data.clear()
                        st.rerun()
                st.divider()

# 4. FINANCEIRO
elif aba == "Financeiro":
    st.header("💰 Fechamento Gerencial")
    df_fin = carregar_log_cache()
    if not df_fin.empty:
        df_ok = df_fin[df_fin['Dobrador'] != ""].copy()
        
        st.subheader("🏫 Conta da Escola")
        esc = df_ok[df_ok['Pagador'] == "Escola"]
        if not esc.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Students", len(esc[esc['Equipamento'] == "Student"]))
            c2.metric("Tandems", len(esc[esc['Equipamento'] == "Tandem"]))
            c3.metric("Total Escola", f"R$ {esc['Valor'].sum()},00")
            st.table(esc.groupby('Dobrador').agg(Quantidade=('Valor', 'count'), Total_Reais=('Valor', 'sum')).reset_index())
        
        st.divider()
        st.subheader("👤 Extrato Individual")
        user = st.selectbox("Dobrador:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
        meu_extrato = df_ok[df_ok['Dobrador'] == user]
        if not meu_extrato.empty:
            resumo_atleta = meu_extrato.groupby(['Atleta', 'Equipamento']).agg(Dobragens=('Valor', 'count'), Total_a_Receber=('Valor', 'sum')).reset_index()
            st.dataframe(resumo_atleta, use_container_width=True)

if st.sidebar.button("🚨 RESET LOG (DOMINGO)"):
    sheet.delete_rows(2, sheet.row_count)
    st.cache_data.clear()
    st.rerun()
