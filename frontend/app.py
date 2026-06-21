import streamlit as st
import boto3
import requests
import os
import uuid
import time
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da Página
st.set_page_config(
    page_title="DocuSmart Seguros",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos Customizados (Light SaaS Premium Mode)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  html, body, .stApp { font-family: 'Inter', sans-serif; background: #F1F5F9; }
  h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; }
  code, .mono { font-family: 'JetBrains Mono', monospace; }
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  .main .block-container { max-width: 860px; margin: 3rem auto; padding: 3rem; background: #FFFFFF; border-radius: 16px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.02); border: 1px solid #E2E8F0; }
  @keyframes pulse-ring { 0% { box-shadow: 0 0 0 0 rgba(37,99,235,0.3); } 70% { box-shadow: 0 0 0 15px rgba(37,99,235,0); } 100% { box-shadow: 0 0 0 0 rgba(37,99,235,0); } }
  .logo-container { display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; border-radius: 50%; background: #EFF6FF; border: 2px solid #2563EB; animation: pulse-ring 2.5s ease-out infinite; font-size: 2rem; margin-bottom: 1.5rem; color: #2563EB; }
  .hero-block { text-align: center; margin-bottom: 3rem; }
  .hero-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 2.8rem; color: #0F172A; margin-bottom: 0.5rem; line-height: 1.1; letter-spacing: -0.03em; }
  .hero-subtitle { font-family: 'Inter', sans-serif; font-size: 1.05rem; color: #64748B; font-weight: 500; }
  .hero-divider { height: 1px; background-color: #E2E8F0; margin: 2rem auto 0 auto; width: 100%; }
  .stTabs [data-baseweb="tab-list"] { gap: 15px; background-color: transparent; padding: 0; border-bottom: 1px solid #E2E8F0; }
  .stTabs [data-baseweb="tab"] { font-family: 'Inter', sans-serif; color: #64748B; background-color: transparent !important; border: none !important; border-bottom: 3px solid transparent !important; padding: 12px 15px; font-weight: 600; }
  .stTabs [data-baseweb="tab"]:hover { color: #0F172A; }
  .stTabs [aria-selected="true"] { color: #2563EB !important; border-bottom: 3px solid #2563EB !important; }
  .upload-wrapper { background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 12px; padding: 3rem 2rem; text-align: center; margin-bottom: 1.5rem; transition: border-color 0.3s, background-color 0.3s; }
  .upload-wrapper:hover { border-color: #94A3B8; background: #F1F5F9; }
  .upload-label { font-family: 'Inter', sans-serif; font-weight: 600; color: #334155; font-size: 1.15rem; margin-bottom: 8px; }
  .upload-hint { color: #64748B; font-size: 0.9rem; }
  div.stButton > button[kind="primary"] { background: #2563EB !important; color: white !important; border-radius: 8px !important; font-size: 1.05rem !important; font-weight: 600 !important; padding: 0.75rem 2rem !important; border: none !important; transition: all 0.2s ease; width: 100%; box-shadow: 0 4px 6px -1px rgba(37,99,235,0.2); }
  div.stButton > button[kind="primary"]:hover { background: #1D4ED8 !important; box-shadow: 0 10px 15px -3px rgba(37,99,235,0.3); transform: translateY(-1px); }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
  .success-banner { background-color: #ECFDF5; border: 1px solid #A7F3D0; border-left: 4px solid #10B981; color: #065F46; padding: 1.2rem 1.5rem; border-radius: 6px; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 2rem; animation: fadeIn 0.6s ease-out; display: flex; align-items: center; gap: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
  .section-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.4rem; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 0.8rem; margin-bottom: 1.5rem; }
  .section-title span { border-bottom: 2px solid #2563EB; padding-bottom: 0.8rem; }
  .light-card { background: #FFFFFF; border-radius: 12px; padding: 1.5rem; border: 1px solid #E2E8F0; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
  .light-card-right { background: #FFFFFF; border-radius: 12px; padding: 1.5rem; border: 1px solid #E2E8F0; border-left: 3px solid #2563EB; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
  .badge-bo { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; border-radius: 999px; font-size: 0.75rem; font-weight: 700; padding: 4px 12px; display: inline-block; margin-bottom: 1.2rem; text-transform: uppercase; letter-spacing: 0.05em; }
  .label-muted { color: #64748B; font-size: 0.75rem; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
  .value-mono { color: #0F172A; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; font-weight: 500; margin-bottom: 1.2rem; word-break: break-all; }
  .summary-text { font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #334155; line-height: 1.6; }
  table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 1rem; border-radius: 8px; overflow: hidden; border: 1px solid #E2E8F0; }
  th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid #E2E8F0; }
  th { background-color: #F8FAFC; color: #475569; font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #E2E8F0; }
  tr:nth-child(even) { background-color: #F8FAFC; }
  tr:nth-child(odd) { background-color: #FFFFFF; }
  tr:last-child td { border-bottom: none; }
  td:first-child { font-weight: 600; color: #0F172A; }
  td:last-child { color: #334155; font-family: 'JetBrains Mono', monospace; }
  .hack-footer { text-align: center; background: transparent; padding: 20px 0; margin-top: 40px; font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #64748B; }
</style>
""", unsafe_allow_html=True)

# Lógica de variáveis
api_url = os.getenv("DOCUSMART_API_URL", "")
s3_bucket = os.getenv("DOCUSMART_S3_BUCKET", "")

# 🔷 HERO HEADER
st.markdown("""
<div class="hero-block">
<div class="logo-container">🛡️</div>
<div class="hero-title">DocuSmart Seguros</div>
<div class="hero-subtitle">Portal do Analista &middot; Triagem Automatizada com IA Generativa</div>
<div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)

# Abas focadas no negócio
tab1, tab2 = st.tabs(["📤 Painel de Triagem", "🔎 Auditoria e Consultas"])

# ==========================================
# ABA 1: PAINEL DE TRIAGEM
# ==========================================
with tab1:
    
    st.markdown("""
<div class="upload-wrapper">
<div class="upload-label">📎 Envie o documento do sinistro</div>
<div class="upload-hint">Formatos aceitos: PNG, PDF, JPG</div>
</div>
""", unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(" ", type=['pdf', 'png', 'jpg', 'jpeg'], accept_multiple_files=True, label_visibility="collapsed")
    
    if uploaded_files:
        btn_label = "Iniciar Análise de Lote" if len(uploaded_files) > 1 else "Iniciar Análise de IA"
        if st.button(btn_label, type="primary"):
            if not api_url or not s3_bucket:
                st.error("Erro de sistema: Credenciais de API não configuradas.")
            else:
                global_start_time = time.time()
                for idx, uploaded_file in enumerate(uploaded_files):
                    st.markdown(f"<div class='section-title'><span>📄 Arquivo {idx+1}:</span> {uploaded_file.name}</div>", unsafe_allow_html=True)
                    
                    upload_success = False
                    s3_key = ""
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.markdown(f"*Carregando de forma segura no cofre digital...*")
                    s3_client = boto3.client('s3')
                    file_extension = uploaded_file.name.split('.')[-1]
                    s3_key = f"uploads/{uuid.uuid4()}.{file_extension}"
                    
                    try:
                        s3_client.upload_fileobj(uploaded_file, s3_bucket, s3_key)
                        upload_success = True
                        progress_bar.progress(30)
                    except Exception as e:
                        st.error(f"Erro de comunicação com o servidor seguro: {str(e)}")

                    if upload_success:
                        status_text.markdown("*Acionando Agentes de IA para leitura e extração (OCR)...*")
                        try:
                            start_time = time.time()
                            payload = {"bucket": s3_bucket, "key": s3_key}
                            
                            response = requests.post(f"{api_url.rstrip('/')}/analisar-sinistro", json=payload, timeout=90)
                            
                            end_time = time.time()
                            tempo_execucao = round(end_time - start_time, 1)
                            progress_bar.progress(100)
                            status_text.empty()
                            progress_bar.empty()
                            
                            if response.status_code == 200:
                                resultado = response.json()
                                
                                # ✅ SUCCESS BANNER
                                st.markdown("""
<div class="success-banner">
<span style="font-size:1.3rem;">✅</span> Documento processado e validado pelas regras de negócio!
</div>
""", unsafe_allow_html=True)
                                
                                col1, col2 = st.columns([1, 1.8])
                                
                                with col1:
                                    tipo = resultado.get('tipo_documento', 'Não Identificado').upper()
                                    prot = resultado.get('id', 'N/A')
                                    dta = resultado.get('processado_em', 'N/A')
                                    
                                    st.markdown(f"""
<div class="light-card">
<div class="label-muted">Classificação Automática</div>
<div class="badge-bo">{tipo}</div>
<div class="label-muted">Protocolo de Auditoria</div>
<div class="value-mono">{prot}</div>
<div class="label-muted">Data da Automação</div>
<div class="value-mono">{dta}</div>
</div>
""", unsafe_allow_html=True)
                                
                                with col2:
                                    resumo = resultado.get('resumo', 'Resumo indisponível.')
                                    st.markdown(f"""
<div class="light-card-right">
<div class="label-muted" style="margin-bottom:8px;">Resumo do Caso (Gerado por IA)</div>
<div class="summary-text">{resumo}</div>
</div>
""", unsafe_allow_html=True)
                                    
                                    st.markdown('<div class="section-title" style="margin-top:2rem; font-size:1.2rem;"><span>🔍 Dados Estru</span>turados Extraídos</div>', unsafe_allow_html=True)
                                    
                                    campos = resultado.get('campos_extraidos', {})
                                    if campos:
                                        md_table = "<table><thead><tr><th>Campo</th><th>Valor Identificado</th></tr></thead><tbody>"
                                        for key, value in campos.items():
                                            if isinstance(value, list):
                                                value = ", ".join(value)
                                            md_table += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
                                        md_table += "</tbody></table>"
                                        st.markdown(md_table, unsafe_allow_html=True)
                                    else:
                                        st.markdown("<p style='color: #64748B; font-style: italic; font-size: 0.9rem;'>Nenhum dado estruturado localizado.</p>", unsafe_allow_html=True)
                                    
                            else:
                                st.error(f"Ocorreu uma falha no processamento. Status: {response.status_code}")
                        except Exception as e:
                            st.error(f"Erro de conexão com os Agentes: {str(e)}")
                    st.divider()
                
                global_end_time = time.time()
                lote_time = round(global_end_time - global_start_time, 1)
                num_docs = len(uploaded_files)
                st.toast(f"✅ {num_docs} documento(s) analisado(s) em {lote_time} segundos!", icon="🚀")
                st.success(f"**Análise em lote concluída:** {num_docs} documento(s) processado(s) com sucesso em {lote_time} segundos.")

# ==========================================
# ABA 2: CONSULTAR HISTÓRICO
# ==========================================
with tab2:
    st.markdown("<p style='color:#64748B; font-family:Inter;'>Recupere pareceres automatizados anteriores fornecendo o número do protocolo.</p>", unsafe_allow_html=True)
    search_id = st.text_input("Número do Protocolo (ID):")
    
    if st.button("Recuperar Parecer", type="primary"):
        if not api_url:
            st.error("Erro: API não configurada.")
        elif not search_id:
            st.warning("Por favor, informe o protocolo.")
        else:
            with st.spinner("Localizando registro seguro..."):
                try:
                    response = requests.get(f"{api_url.rstrip('/')}/sinistro/{search_id}", timeout=15)
                    if response.status_code == 200:
                        resultado = response.json()
                        st.markdown("""
<div class="success-banner" style="margin-bottom: 1rem;">
<span style="font-size:1.3rem;">✅</span> Registro localizado com sucesso!
</div>
""", unsafe_allow_html=True)
                        
                        st.info(f"**Documento:** {resultado.get('tipo_documento', 'N/A')}")
                        st.write(f"**Resumo:** {resultado.get('resumo', 'N/A')}")
                        st.write(f"**Data do Processamento:** {resultado.get('processado_em', 'N/A')}")
                    elif response.status_code == 404:
                        st.error("Nenhum parecer encontrado para este protocolo.")
                    else:
                        st.error(f"Falha ao consultar. (Status {response.status_code})")
                except Exception as e:
                    st.error(f"Erro na requisição: {str(e)}")

# ==========================================
# RODAPÉ (FOOTER)
# ==========================================
st.markdown("""
<div class="hack-footer">
Desenvolvido pela Equipe 8 &middot; Hackathon 2026
</div>
""", unsafe_allow_html=True)
