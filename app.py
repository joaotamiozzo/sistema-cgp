import streamlit as st
import pandas as pd
from datetime import datetime

# Configurações de Página
st.set_page_config(page_title="CGP Ops - Final de Semana", layout="wide")

# --- BANCO DE DADOS TEMPORÁRIO ---
if 'historico_geral' not in st.session_state:
    st.session_state.historico_geral = []
if 'atletas_area' not in st.session_state:
    st.session_state.atletas_area = []

# --- ESTILO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; }
    .decolagem-header { 
        background-color: #1E3A8A; 
        color: white; 
        padding: 10px; 
        border-radius: 5px; 
        margin-top: 20px;
        font-weight: bold;
    }
    .vaga-card {
        border-left: 5px solid #3B82F6;
        background-color: #f1f5f9;
        padding: 10px;
        margin-bottom: 5px;
        border-radius: 0 5px 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
st.sidebar.title("🪂 CGP AirOps")
dia_operacao = st.sidebar.selectbox("📅 Dia da Operação", ["Sexta", "Sábado", "Domingo"])
aba = st.sidebar.radio("Navegação", ["Manifesto", "Lançar Decolagem", "Área de Dobragem", "Financeiro"])

# 1. MANIFESTO
if aba == "Manifesto":
    st.header(f"📝 Registro de Atletas - {dia_operacao}")
    with st.form("chegada"):
        nome = st.text_input("Nome do Paraquedista")
        add = st.form_submit_button("Registrar na Área")
        if add and nome:
            if nome not in st.session_state.atletas_area:
                st.session_state.atletas_area.append(nome)
                st.success(f"{nome} pronto para saltar!")
    st.subheader("Atletas presentes no CGP")
    st.write(", ".join(st.session_state.atletas_area) if st.session_state.atletas_area else "Ninguém registrado.")

# 2. LANÇAR DECOLAGEM (COM VISUALIZAÇÃO DOS REGISTROS)
elif aba == "Lançar Decolagem":
    st.header(f"✈️ Montar Voo - {dia_operacao}")
    
    # Formulário de Lançamento
    with st.expander("➕ Lançar Nova Vaga", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            num_dec = st.number_input("Nº Decolagem", min_value=1, step=1)
        with col2:
            atleta = st.selectbox("Atleta", st.session_state.atletas_area) if st.session_state.atletas_area else st.text_input("Nome (Atleta não listado)")
        with col3:
            equip = st.selectbox("Equipamento", ["Student", "Tandem", "Atleta (Próprio)"])
        
        if st.button("Lançar no Sistema"):
            valor = 30 if equip == "Tandem" else 25
            pagador = "Escola" if equip in ["Student", "Tandem"] else "Particular"
            
            st.session_state.historico_geral.append({
                "id": len(st.session_state.historico_geral),
                "Dia": dia_operacao,
                "Decolagem": num_dec,
                "Atleta": atleta,
                "Equipamento": equip,
                "Valor": valor,
                "Pagador": pagador,
                "Dobrador": None
            })
            st.rerun()

    st.divider()
    
    # --- VISUALIZAÇÃO DAS DECOLAGENS (O QUE VOCÊ PEDIU) ---
    st.subheader(f"📋 Registros de {dia_operacao}")
    
    df_dia = pd.DataFrame(st.session_state.historico_geral)
    if not df_dia.empty:
        df_dia = df_dia[df_dia['Dia'] == dia_operacao]
        
        if df_dia.empty:
            st.info("Nenhuma decolagem lançada para hoje.")
        else:
            # Pegamos os números das decolagens lançadas e ordenamos
            decolagens_lista = sorted(df_dia['Decolagem'].unique())
            
            for d in decolagens_lista:
                st.markdown(f'<div class="decolagem-header">DECOLAGEM {d}</div>', unsafe_allow_html=True)
                
                # Filtra os atletas apenas desta decolagem
                vagas = df_dia[df_dia['Decolagem'] == d]
                
                for _, vaga in vagas.iterrows():
                    status_cor = "🟢" if vaga['Dobrador'] else "🟡"
                    dobrador_txt = f" | Dobrador: {vaga['Dobrador']}" if vaga['Dobrador'] else " | Aguardando Dobragem"
                    
                    st.markdown(f"""
                        <div class="vaga-card">
                            {status_cor} <b>{vaga['Atleta']}</b> - {vaga['Equipamento']} {dobrador_txt}
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("Nenhum voo registrado no final de semana.")

# 3. ÁREA DE DOBRAGEM
elif aba == "Área de Dobragem":
    st.header(f"🔧 Dobragem - {dia_operacao}")
    meu_nome = st.selectbox("Selecionar Dobrador:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
    
    pendentes = [v for v in st.session_state.historico_geral if v['Dia'] == dia_operacao and v['Dobrador'] is None]
    
    if not pendentes:
        st.info(f"Sem paraquedas pendentes para {dia_operacao}.")
    else:
        for vaga in pendentes:
            with st.container():
                c1, c2, c3 = st.columns([1, 3, 2])
                with c1: st.subheader(f"D{vaga['Decolagem']}")
                with c2: 
                    st.write(f"**{vaga['Atleta']}**")
                    st.caption(f"{vaga['Equipamento']}")
                with c3:
                    if st.button(f"Dobrei", key=f"job_{vaga['id']}"):
                        vaga['Dobrador'] = meu_nome
                        st.rerun()
                st.divider()

# 4. FINANCEIRO
elif aba == "Financeiro":
    st.header("💰 Fechamento do Final de Semana")
    df_tudo = pd.DataFrame(st.session_state.historico_geral)
    
    if not df_tudo.empty:
        df_dobrado = df_tudo[df_tudo['Dobrador'].notna()]
        
        st.subheader("🏫 Total Escola (Student/Tandem)")
        escola = df_dobrado[df_dobrado['Pagador'] == "Escola"]
        if not escola.empty:
            st.table(escola.groupby('Dobrador')['Valor'].sum().reset_index())
        
        st.divider()
        st.subheader("👤 Extrato Individual")
        consulta = st.selectbox("Verificar nome:", ["TAMIOZZO", "PORTELLA", "SAUL", "GABRIEL", "VINICIUS"])
        meus_dados = df_dobrado[df_dobrado['Dobrador'] == consulta]
        
        if not meus_dados.empty:
            col_a, col_b = st.columns(2)
            col_a.metric("Total Acumulado", f"R$ {meus_dados['Valor'].sum()}")
            col_b.metric("Total Dobragens", len(meus_dados))
            st.dataframe(meus_dados[["Dia", "Decolagem", "Atleta", "Equipamento", "Valor"]])
