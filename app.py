import streamlit as st
import pandas as pd
from datetime import datetime

# Configurações de Página
st.set_page_config(page_title="CGP Ops - Login", layout="wide")

# --- BANCO DE DADOS TEMPORÁRIO ---
if 'historico_geral' not in st.session_state:
    st.session_state.historico_geral = []
if 'atletas_area' not in st.session_state:
    st.session_state.atletas_area = []
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'usuario_atual' not in st.session_state:
    st.session_state.usuario_atual = None

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .decolagem-header { background-color: #1E3A8A; color: white; padding: 10px; border-radius: 5px; margin-top: 20px; }
    .vaga-card { border-left: 5px solid #3B82F6; background-color: #f1f5f9; padding: 10px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TELA DE LOGIN
# ---------------------------------------------------------
def tela_login():
    st.title("🪂 CGP - Acesso ao Sistema")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("Identifique-se")
            perfil = st.selectbox("Perfil:", ["PAOLA", "TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
            senha = st.text_input("Senha:", type="password")
            
            if st.button("Entrar"):
                # Senha única para todos ou você pode definir uma por nome
                # Exemplo: Senha padrão 'cgp123'
                if senha == "cgp123": 
                    st.session_state.logado = True
                    st.session_state.usuario_atual = perfil
                    st.rerun()
                else:
                    st.error("Senha incorreta!")

# ---------------------------------------------------------
# SISTEMA PRINCIPAL (SÓ APARECE SE LOGADO)
# ---------------------------------------------------------
if not st.session_state.logado:
    tela_login()
else:
    # Sidebar com Logout e Info
    st.sidebar.title(f"👤 {st.session_state.usuario_atual}")
    if st.sidebar.button("Sair / Logout"):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.rerun()

    dia_operacao = st.sidebar.selectbox("📅 Dia da Operação", ["Sexta", "Sábado", "Domingo"])
    
    # Restrição de Abas conforme Perfil
    opcoes_menu = ["Área de Dobragem", "Financeiro"]
    if st.session_state.usuario_atual == "PAOLA" or st.session_state.usuario_atual == "TAMIOZZO":
        opcoes_menu = ["Manifesto", "Lançar Decolagem"] + opcoes_menu
    
    aba = st.sidebar.radio("Navegação", opcoes_menu)

    # 1. MANIFESTO
    if aba == "Manifesto":
        st.header(f"📝 Registro de Atletas - {dia_operacao}")
        with st.form("chegada"):
            nome = st.text_input("Nome do Paraquedista")
            if st.form_submit_button("Registrar na Área"):
                if nome and nome not in st.session_state.atletas_area:
                    st.session_state.atletas_area.append(nome)
                    st.success(f"{nome} pronto para saltar!")
        st.write(", ".join(st.session_state.atletas_area))

    # 2. LANÇAR DECOLAGEM
    elif aba == "Lançar Decolagem":
        st.header(f"✈️ Montar Voo - {dia_operacao}")
        with st.expander("➕ Lançar Nova Vaga", expanded=True):
            c1, c2, c3 = st.columns(3)
            num_dec = c1.number_input("Nº Decolagem", min_value=1, step=1)
            atleta = c2.selectbox("Atleta", st.session_state.atletas_area) if st.session_state.atletas_area else c2.text_input("Nome")
            equip = c3.selectbox("Equipamento", ["Student", "Tandem", "Atleta"])
            
            if st.button("Lançar no Sistema"):
                valor = 30 if equip == "Tandem" else 25
                pagador = "Escola" if equip in ["Student", "Tandem"] else "Particular"
                st.session_state.historico_geral.append({
                    "id": len(st.session_state.historico_geral),
                    "Dia": dia_operacao, "Decolagem": num_dec, "Atleta": atleta,
                    "Equipamento": equip, "Valor": valor, "Pagador": pagador, "Dobrador": None
                })
                st.rerun()

    # 3. ÁREA DE DOBRAGEM
    elif aba == "Área de Dobragem":
        st.header(f"🔧 Dobragem - {dia_operacao}")
        st.info(f"Logado como: {st.session_state.usuario_atual}")
        
        pendentes = [v for v in st.session_state.historico_geral if v['Dia'] == dia_operacao and v['Dobrador'] is None]
        
        for vaga in pendentes:
            with st.container():
                c1, c2, c3 = st.columns([1, 3, 2])
                c1.subheader(f"D{vaga['Decolagem']}")
                c2.write(f"**{vaga['Atleta']}** ({vaga['Equipamento']})")
                if c3.button(f"Assinar", key=f"job_{vaga['id']}"):
                    vaga['Dobrador'] = st.session_state.usuario_atual
                    st.success("Assinado!")
                    st.rerun()
            st.divider()

    # 4. FINANCEIRO
    elif aba == "Financeiro":
        st.header("💰 Fechamento")
        df_tudo = pd.DataFrame(st.session_state.historico_geral)
        if not df_tudo.empty:
            df_dobrado = df_tudo[df_tudo['Dobrador'].notna()]
            
            # Se for dobrador, mostra só o dele. Se for Paola/Tamiozzo, mostra tudo.
            if st.session_state.usuario_atual in ["PAOLA", "TAMIOZZO"]:
                st.subheader("🏫 Resumo Escola")
                st.table(df_dobrado[df_dobrado['Pagador'] == "Escola"].groupby('Dobrador')['Valor'].sum().reset_index())
            
            st.subheader(f"👤 Seu Extrato: {st.session_state.usuario_atual}")
            meu_df = df_dobrado[df_dobrado['Dobrador'] == st.session_state.usuario_atual]
            if not meu_df.empty:
                st.metric("Total a Receber", f"R$ {meu_df['Valor'].sum()}")
                st.dataframe(meu_df)
