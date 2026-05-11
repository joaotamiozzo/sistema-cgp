import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CONEXÃO ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

ID_PLANILHA_NOVA = "1CZYDTUfgBhSbJqd4Rvsnb38G7rfE4LuQKdbE4Do-krw"

try:
    spreadsheet = client.open_by_key(ID_PLANILHA_NOVA)
    sheet = spreadsheet.get_worksheet(0) # Log Geral
    sheet_manifesto = spreadsheet.worksheet("manifesto") # Manifesto
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

st.set_page_config(page_title="CGP AirOps", layout="wide")

# --- FUNÇÕES DE CACHE ---
@st.cache_data(ttl=15)
def carregar_log_cache():
    return pd.DataFrame(sheet.get_all_records())

@st.cache_data(ttl=60)
def carregar_manifesto_cache():
    lista = sheet_manifesto.col_values(1)
    return sorted(lista) if lista else []

def reset_cache():
    st.cache_data.clear()

# --- NAVEGAÇÃO ---
st.sidebar.title("🪂 CGP AirOps")
if st.sidebar.button("🔄 Sincronizar Agora"):
    reset_cache()
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
                reset_cache()
                st.success(f"{novo_atleta} adicionado ao manifesto!")
                st.rerun()

    st.subheader("Atletas presentes no CGP")
    lista_p = carregar_manifesto_cache()
    if lista_p:
        st.write(", ".join(lista_p))
    else:
        st.info("Nenhum atleta registrado no manifesto ainda.")
    
    # BOTÃO RESTAURADO: LIMPAR MANIFESTO
    if st.button("Limpar Manifesto (Novo FDS)"):
        sheet_manifesto.clear()
        reset_cache()
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
            reset_cache()
            st.success(f"{atleta} lançado na Dec {num_dec}!")
            st.rerun()

    st.divider()
    df_dia = carregar_log_cache()
    if not df_dia.empty:
        df_dia = df_dia[df_dia['Dia'] == dia_operacao]
        if not df_dia.empty:
            for d in sorted(df_dia['Decolagem'].unique()):
                with st.expander(f"📦 DECOLAGEM {d}", expanded=True):
                    vagas = df_dia[df_dia['Decolagem'] == d]
                    for _, v in vagas.iterrows():
                        status = "🟢" if v['Dobrador'] else "🟡"
                        dobrador_info = f" | Dobrador: {v['Dobrador']}" if v['Dobrador'] else " | Pendente"
                        st.write(f"{status} **{v['Atleta']}** ({v['Equipamento']}){dobrador_info}")

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
                    col2.write(f"**{vaga['Atleta']}**\n\n({vaga['Equipamento']})")
                    if col3.button("Assinar", key=f"job_{index}"):
                        sheet.update_cell(index + 2, 7, meu_nome)
                        reset_cache()
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
            resumo_pag = esc.groupby('Dobrador').agg(Quantidade=('Valor', 'count'), Total_Reais=('Valor', 'sum')).reset_index()
            st.table(resumo_pag)
        
        st.divider()
        st.subheader("👤 Extrato Individual (Agrupado por Atleta)")
        user = st.selectbox("Consultar Dobrador:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
        meu_extrato = df_ok[df_ok['Dobrador'] == user]
        if not meu_extrato.empty:
            col_a, col_b = st.columns(2)
            col_a.metric("Total Acumulado", f"R$ {meu_extrato['Valor'].sum()},00")
            col_b.metric("Total Peças", len(meu_extrato))
            resumo_atleta = meu_extrato.groupby(['Atleta', 'Equipamento']).agg(Dobragens=('Valor', 'count'), Total_a_Receber=('Valor', 'sum')).reset_index()
            st.dataframe(resumo_atleta, use_container_width=True)

if st.sidebar.button("🚨 RESET LOG (DOMINGO)"):
    sheet.delete_rows(2, sheet.row_count)
    reset_cache()
    st.rerun()
