import streamlit as st
import pandas as pd
from datetime import datetime

# Configurações de Design
st.set_page_config(page_title="Sistema CGP - Dobragem", layout="wide")

# --- BANCO DE DADOS (Simulado em Session State para persistência na sessão) ---
# Em um passo futuro, conectaremos com gspread para salvar permanentemente.
if 'atletas_presentes' not in st.session_state:
    st.session_state.atletas_presentes = []
if 'historico_decolagens' not in st.session_state:
    st.session_state.historico_decolagens = []

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .status-badge { padding: 5px; border-radius: 5px; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
st.sidebar.title("🪂 CGP Operacional")
aba = st.sidebar.radio("Navegação", ["Manifesto", "Decolagens", "Área de Dobragem", "Dashboard / Financeiro"])

# ---------------------------------------------------------
# 1. MANIFESTO (PAOLA CADASTRA QUEM CHEGOU)
# ---------------------------------------------------------
if aba == "Manifesto":
    st.header("📝 Atletas na Área")
    with st.form("add_atleta"):
        nome_novo = st.text_input("Nome do Atleta/Aluno")
        btn_add = st.form_submit_button("Registrar Chegada")
        if btn_add and nome_novo:
            if nome_novo not in st.session_state.atletas_presentes:
                st.session_state.atletas_presentes.append(nome_novo)
                st.success(f"{nome_novo} adicionado à lista do dia!")
    
    st.subheader("Lista de Presença")
    st.write(st.session_state.atletas_presentes)
    if st.button("Limpar Lista do Dia"):
        st.session_state.atletas_presentes = []
        st.rerun()

# ---------------------------------------------------------
# 2. DECOLAGENS (PAOLA MONTA OS VOOS)
# ---------------------------------------------------------
elif aba == "Decolagens":
    st.header("✈️ Lançar Decolagem")
    
    if not st.session_state.atletas_presentes:
        st.warning("Cadastre atletas no Manifesto primeiro.")
    else:
        with st.expander("Abrir Painel de Lançamento", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                num_dec = st.number_input("Nº Decolagem", min_value=1, step=1)
            with col2:
                atleta_selecionado = st.selectbox("Atleta", st.session_state.atletas_presentes)
            with col3:
                tipo_equip = st.selectbox("Equipamento", ["Student", "Tandem", "Atleta (Próprio)"])
            
            if st.button("Confirmar Vaga no Voo"):
                # Define valores e quem paga
                valor = 30 if tipo_equip == "Tandem" else 25
                pagador = "Escola" if tipo_equip in ["Student", "Tandem"] else "Particular"
                
                nova_vaga = {
                    "id": len(st.session_state.historico_decolagens),
                    "Decolagem": num_dec,
                    "Atleta": atleta_selecionado,
                    "Equipamento": tipo_equip,
                    "Valor": valor,
                    "Pagador": pagador,
                    "Dobrador": None,
                    "Hora": datetime.now().strftime("%H:%M")
                }
                st.session_state.historico_decolagens.append(nova_vaga)
                st.toast(f"Vaga {atleta_selecionado} lançada!")

        st.divider()
        st.subheader("Voos Lançados (Aguardando Dobragem)")
        df_view = pd.DataFrame(st.session_state.historico_decolagens)
        if not df_view.empty:
            st.dataframe(df_view[df_view['Dobrador'].isna()])

# ---------------------------------------------------------
# 3. ÁREA DE DOBRAGEM (VOCÊ E OS GURIS ASSINAM)
# ---------------------------------------------------------
elif aba == "Área de Dobragem":
    st.header("🔧 Dobragem")
    meu_nome = st.selectbox("Selecione seu nome:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    
    pendentes = [v for v in st.session_state.historico_decolagens if v['Dobrador'] is None]
    
    if not pendentes:
        st.info("Nenhum paraquedas pendente no momento. Bom descanso!")
    else:
        for vaga in pendentes:
            with st.container():
                c1, c2, c3 = st.columns([1, 3, 2])
                with c1:
                    st.subheader(f"D{vaga['Decolagem']}")
                with c2:
                    st.write(f"**{vaga['Atleta']}**")
                    st.caption(f"{vaga['Equipamento']} | Valor: R$ {vaga['Valor']}")
                with c3:
                    if st.button(f"Assinar Dobragem", key=f"vaga_{vaga['id']}"):
                        vaga['Dobrador'] = meu_nome
                        st.success(f"Dobragem registrada para {meu_nome}!")
                        st.rerun()
                st.divider()

# ---------------------------------------------------------
# 4. DASHBOARD / FINANCEIRO
# ---------------------------------------------------------
elif aba == "Dashboard / Financeiro":
    st.header("📊 Fechamento Financeiro")
    
    df_final = pd.DataFrame(st.session_state.historico_decolagens)
    df_final = df_final[df_final['Dobrador'].notna()] # Apenas o que foi dobrado
    
    if df_final.empty:
        st.warning("Nenhum dado financeiro para exibir ainda.")
    else:
        # VISÃO DA PAOLA (Escola)
        st.subheader("🏫 Conta da Escola (Student e Tandem)")
        escola_df = df_final[df_final['Pagador'] == "Escola"]
        if not escola_df.empty:
            resumo_escola = escola_df.groupby('Dobrador')['Valor'].sum().reset_index()
            st.table(resumo_escola)
        
        # VISÃO DO DOBRADOR (Individual)
        st.divider()
        st.subheader("👤 Consulta Individual do Dobrador")
        consulta_nome = st.selectbox("Ver relatório de:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
        meus_registros = df_final[df_final['Dobrador'] == consulta_nome]
        
        if not meus_registros.empty:
            st.write(f"**Total a receber:** R$ {meus_registros['Valor'].sum()},00")
            st.write(f"Quantidade de dobragens: {len(meus_registros)}")
            st.dataframe(meus_registros[["Decolagem", "Atleta", "Equipamento", "Valor", "Pagador"]])
        else:
            st.info("Nenhum registro para este dobrador.")
