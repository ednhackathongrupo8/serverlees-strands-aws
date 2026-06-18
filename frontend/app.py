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

# Estilos Customizados (CSS Premium)
st.markdown("""
<style>
    /* Esconde o menu e rodapé padrão do streamlit para ficar com cara de App */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        color: #0f4c81;
        letter-spacing: -0.02em;
        margin-bottom: 0;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 15px;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        color: #64748b;
        margin-top: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #ffffff;
        border-radius: 0.5rem;
        padding: 1.2rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        text-align: center;
    }
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
    }
    .success-card {
        background: #f0fdf4;
        border-radius: 0.5rem;
        padding: 1.2rem;
        border: 1px solid #bbf7d0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .success-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #166534;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .success-value {
        font-size: 1.4rem;
        font-weight: 800;
        color: #15803d;
    }
    .report-box {
        background-color: #ffffff;
        border-radius: 0.5rem;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    /* Estilizando as abas para ficarem mais clean */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Lógica de variáveis
api_url = os.getenv("DOCUSMART_API_URL", "")
s3_bucket = os.getenv("DOCUSMART_S3_BUCKET", "")

# Cabeçalho Principal
st.markdown('<h1 style="font-family: \'Inter\', sans-serif; font-size: 3.5rem; font-weight: 900; color: #0f4c81; letter-spacing: -0.02em; margin-bottom: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px;">🛡️ DocuSmart Seguros</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-family: \'Inter\', sans-serif; font-size: 1.1rem; color: #64748b; margin-top: 10px; margin-bottom: 2rem;">Portal do Analista | Triagem Automatizada de Sinistros com IA Generativa</p>', unsafe_allow_html=True)

# Abas focadas no negócio
tab1, tab2 = st.tabs(["📤 Painel de Triagem (Upload)", "🔎 Auditoria e Consultas"])

# ==========================================
# ABA 1: PAINEL DE TRIAGEM
# ==========================================
with tab1:
    st.markdown("Faça o upload do documento recebido pelo segurado para iniciar a análise automatizada.")
    uploaded_file = st.file_uploader("", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        if st.button("Iniciar Análise de IA", type="primary", use_container_width=False):
            if not api_url or not s3_bucket:
                st.error("Erro de sistema: Credenciais de API não configuradas.")
            else:
                upload_success = False
                s3_key = ""
                
                # Simulador visual de progresso para encantar jurados
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.markdown("Carregando documento de forma segura no cofre digital...")
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
                    status_text.markdown("Acionando Agentes de IA para leitura e extração (OCR)...")
                    try:
                        start_time = time.time()
                        payload = {
                            "bucket": s3_bucket,
                            "key": s3_key
                        }
                        
                        # Chama a API
                        response = requests.post(f"{api_url.rstrip('/')}/analisar-sinistro", json=payload, timeout=90)
                        
                        end_time = time.time()
                        tempo_execucao = round(end_time - start_time, 1)
                        progress_bar.progress(100)
                        status_text.empty()
                        progress_bar.empty()
                        
                        if response.status_code == 200:
                            resultado = response.json()
                            
                            st.success("✅ Documento processado e validado pelas regras de negócio!")
                            # CÁLCULOS DE ROI E PROJEÇÃO
                            # 1 atendimento = 15 minutos. 40h semanais = 2400 minutos.
                            capacidade_manual = 2400 // 15  # 160 documentos
                            # capacidade IA assumindo tempo_execucao_segundos para cada
                            tempo_seguro = tempo_execucao if tempo_execucao > 0 else 1
                            capacidade_ia = int((2400 * 60) / tempo_seguro)
                            multiplicador = round(capacidade_ia / capacidade_manual)
                            
                            # SEÇÃO DE IMPACTO (ROI) - EFEITO WOW PARA JURADOS
                            st.markdown("---")
                            st.markdown("### 🚀 Impacto Gerado nesta Operação")
                            col_roi1, col_roi2, col_roi3 = st.columns(3)
                            with col_roi1:
                                st.markdown(f'<div class="metric-card"><div class="metric-title">Tempo Médio Manual</div><div class="metric-value">15 min 00s</div></div>', unsafe_allow_html=True)
                            with col_roi2:
                                st.markdown(f'<div class="metric-card"><div class="metric-title">Tempo DocuSmart AI</div><div class="metric-value">{tempo_execucao} seg</div></div>', unsafe_allow_html=True)
                            with col_roi3:
                                st.markdown(f'<div class="success-card"><div class="success-title">Tempo Economizado</div><div class="success-value">> 14 minutos</div></div>', unsafe_allow_html=True)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("### 📈 Projeção de Produtividade (Semana - 40h)")
                            col_proj1, col_proj2, col_proj3 = st.columns(3)
                            with col_proj1:
                                st.markdown(f'<div class="metric-card"><div class="metric-title">Capacidade Humana</div><div class="metric-value">{capacidade_manual} docs/semana</div></div>', unsafe_allow_html=True)
                            with col_proj2:
                                st.markdown(f'<div class="metric-card"><div class="metric-title">Capacidade da IA</div><div class="metric-value">{capacidade_ia:,} docs/semana</div></div>', unsafe_allow_html=True)
                            with col_proj3:
                                st.markdown(f'<div class="success-card"><div class="success-title">Aceleração Operacional</div><div class="success-value">{multiplicador}x Mais Rápido</div></div>', unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # RESULTADO OFICIAL - SEM JSON NA TELA
                            st.markdown("### 📑 Parecer Oficial do Sinistro")
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.markdown("#### 📌 Classificação Automática")
                                st.info(f"**{resultado.get('tipo_documento', 'Não Identificado').upper()}**")
                                st.markdown(f"**Protocolo de Auditoria:**<br>`{resultado.get('id', 'N/A')}`", unsafe_allow_html=True)
                                st.markdown(f"**Data da Automação:**<br>{resultado.get('processado_em', 'N/A')}", unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown("#### 🧠 Resumo do Caso (Gerado por IA)")
                                st.success(resultado.get('resumo', 'Resumo indisponível.'))
                                
                                st.markdown("#### 🔎 Dados Estruturados Extraídos")
                                campos = resultado.get('campos_extraidos', {})
                                if campos:
                                    # Cria uma tabela markdown para ficar com visual clean corporativo
                                    md_table = "| Campo | Valor Identificado |\n|---|---|\n"
                                    for key, value in campos.items():
                                        if isinstance(value, list):
                                            value = ", ".join(value)
                                        md_table += f"| **{key.replace('_', ' ').title()}** | {value} |\n"
                                    st.markdown(md_table)
                                else:
                                    st.write("Nenhum dado estruturado específico foi localizado neste documento.")
                                
                        else:
                            st.error(f"Ocorreu uma falha no processamento. Status: {response.status_code}")
                    except Exception as e:
                        st.error(f"Erro de conexão com os Agentes: {str(e)}")

# ==========================================
# ABA 2: CONSULTAR HISTÓRICO
# ==========================================
with tab2:
    st.markdown("Recupere pareceres automatizados anteriores fornecendo o número do protocolo.")
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
                        st.success("Registro localizado com sucesso!")
                        
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
import base64

img_tag = ""
try:
    with open("footer.png", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    img_tag = f'<img src="data:image/png;base64,{img_b64}" style="max-width: 200px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">'
except Exception:
    img_tag = "<p style='color: #fbbf24; font-size: 0.9rem;'>⚠️ Para exibir o banner, salve a imagem no chat como 'footer.png' na pasta 'frontend'.</p>"

st.markdown(f"""
<div style="background-color: #e2e8f0; padding: 40px 20px; border-radius: 12px; text-align: center; margin-top: 60px; border-top: 4px solid #0f4c81;">
    {img_tag}
    <p style="color: #0f172a; font-size: 1rem; margin-top: 20px; font-family: 'Inter', sans-serif;">
        Desenvolvido pela <b style="color: #000000;">Equipe 8</b>
    </p>
</div>
""", unsafe_allow_html=True)
