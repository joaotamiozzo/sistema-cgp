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

st.set_page_config(page_title="CGP AirOps - Turbo", layout="wide")

# --- FUNÇÕES DE CACHE ---

@st.cache_data(ttl=15) # O app consulta o Google no máximo a cada 15 segundos
def carregar_log_cache():
    return pd.DataFrame(sheet.get_all_records())

@st.cache_data(ttl=60) # O manifesto muda pouco, cache de 1 minuto
def carregar_manifesto_cache():
    lista = sheet_manifesto.col_values(1)
    return sorted(lista) if lista else []

def reset_cache():
    st.cache_data.clear()

# --- NAVEGAÇÃO ---
st.sidebar.title("🪂 CGP AirOps")
# Botão de emergência para forçar atualização se alguém estiver ansioso
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
        if st.form_submit_button("Registrar"):
            if novo_atleta:
                sheet_manifesto.append_row([novo_atleta])
                reset_cache() # Limpa cache para o nome aparecer na decolagem
                st.success(f"{novo_atleta} registrado!")
                st.rerun()

    st.subheader("Atletas no CGP")
    lista_p = carregar_manifesto_cache()
    st.write(", ".join(lista_p) if lista_p else "Ninguém no manifesto.")

# 2. LANÇAR DECOLAGEM
elif aba == "Lançar Decolagem":
    st.header(f"✈️ Montar Voo - {dia_operacao}")
    opcoes = carregar_manifesto_cache()
    
    with st.expander("➕ Nova Vaga", expanded=True):
        c1, c2, c3 = st.columns(3)
        num_dec = c1.number_input("Nº Dec", min_value=1, step=1)
        atleta = c2.selectbox("Atleta", opcoes) if opcoes else c2.text_input("Nome")
        equip = c3.selectbox("Equipamento", ["Student", "Tandem", "Atleta"])
        
        if st.button("Confirmar"):
            valor = 30 if equip == "Tandem" else 25
            pag = "Escola" if equip != "Atleta" else "Particular"
            sheet.append_row([dia_operacao, int(num_dec), atleta, equip, valor, pag, ""])
            reset_cache() # Limpa cache para o dobrador ver o novo paraquedas
            st.success(f"Voo {num_dec} atualizado!")
            st.rerun()

    st.divider()
    df = carregar_log_cache()
    if not df.empty:
        df = df[df['Dia'] == dia_operacao]
        for d in sorted(df['Decolagem'].unique()):
            with st.expander(f"📦 DECOLAGEM {d}", expanded=True):
                vagas = df[df['Decolagem'] == d]
                for _, v in vagas.iterrows():
                    status = "🟢" if v['Dobrador'] else "🟡"
                    st.write(f"{status} **{v['Atleta']}** ({v['Equipamento']}) {v['Dobrador']}")

# 3. ÁREA DE DOBRAGEM
elif aba == "Área de Dobragem":
    st.header(f"🔧 Dobragem - {dia_operacao}")
    meu_nome = st.selectbox("Quem é você?", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    df = carregar_log_cache()
    
    if not df.empty:
        pendentes = df[(df['Dia'] == dia_operacao) & (df['Dobrador'] == "")]
        if pendentes.empty:
            st.info("Tudo dobrado!")
        else:
            for idx, vaga in pendentes.iterrows():
                col1, col2, col3 = st.columns([1, 3, 2])
                col1.write(f"D{vaga['Decolagem']}")
                col2.write(f"**{vaga['Atleta']}** ({vaga['Equipamento']})")
                if col3.button("Dobrei", key=f"btn_{idx}"):
                    sheet.update_cell(idx + 2, 7, meu_nome)
                    reset_cache() # Limpa cache para o financeiro atualizar
                    st.rerun()
                st.divider()

# 4. FINANCEIRO
elif aba == "Financeiro":
    st.header("💰 Fechamento")
    df = carregar_log_cache()
    if not df.empty:
        df_ok = df[df['Dobrador'] != ""].copy()
        
        # RESUMO ESCOLA
        st.subheader("🏫 Resumo Escola")
        esc = df_ok[df_ok['Pagador'] == "Escola"]
        if not esc.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Students", len(esc[esc['Equipamento'] == "Student"]))
            c2.metric("Tandems", len(esc[esc['Equipamento'] == "Tandem"]))
            c3.metric("Total Escola", f"R$ {esc['Valor'].sum()},00")
            st.table(esc.groupby('Dobrador').agg(Qtd=('Valor','count'), Total=('Valor','sum')).reset_index())
        
        # EXTRATO INDIVIDUAL (AGRUPADO POR ATLETA)
        st.divider()
        u = st.selectbox("Consultar Dobrador:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
        meu = df_ok[df_ok['Dobrador'] == u]
        if not meu.empty:
            col_a, col_b = st.columns(2)
            col_a.metric(f"Total Acumulado", f"R$ {meu['Valor'].sum()},00")
            col_b.metric("Total Peças", len(meu))
            
            st.write(f"**Resumo de cobrança por Atleta/Equipamento:**")
            resumo_atleta = meu.groupby(['Atleta', 'Equipamento']).agg(
                Dobragens=('Valor', 'count'),
                Total_a_Receber=('Valor', 'sum')
            ).reset_index()
            st.dataframe(resumo_atleta, use_container_width=True)

if st.sidebar.button("🚨 RESET TOTAL (DOMINGO)"):
    sheet.delete_rows(2, sheet.row_count)
    reset_cache()
    st.rerun()
