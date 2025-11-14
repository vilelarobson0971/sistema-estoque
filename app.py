import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json
import time

# Configuração da página - DEVE SER A PRIMEIRA COISA
st.set_page_config(
    page_title="Sistema de Compras e Estoque",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adicionar CSS para melhorar performance
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }
    div[data-testid="stSidebar"] {
        min-width: 300px;
        max-width: 300px;
    }
</style>
""", unsafe_allow_html=True)

# Função para conectar ao Google Sheets COM MAIS TRATAMENTO DE ERRO
@st.cache_resource(show_spinner=False)
def connect_to_gsheet():
    """Conecta ao Google Sheets usando credenciais"""
    try:
        # Verificar se secrets existe
        if 'gcp_service_account' not in st.secrets:
            st.error("❌ Credenciais não encontradas nos secrets")
            return None
            
        # Configurar scope
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Carregar credenciais
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Tentar abrir a planilha
        try:
            spreadsheet = client.open("Sistema_Estoque")
            st.success("✅ Conectado ao Google Sheets com sucesso!")
            return spreadsheet
        except gspread.SpreadsheetNotFound:
            st.error("❌ Planilha 'Sistema_Estoque' não encontrada")
            return None
        except Exception as e:
            st.error(f"❌ Erro ao acessar planilha: {e}")
            return None
            
    except Exception as e:
        st.error(f"❌ Erro crítico na conexão: {e}")
        return None

# Função para inicializar as abas necessárias COM TIMEOUT
def inicializar_planilhas(spreadsheet):
    """Cria as abas necessárias se não existirem"""
    try:
        abas_necessarias = [
            "Produtos",
            "Necessidade_Compra", 
            "Orcamentos",
            "Entradas",
            "Fechamentos"
        ]
        
        # Obter abas existentes com timeout
        abas_existentes = []
        try:
            worksheets = spreadsheet.worksheets()
            abas_existentes = [sheet.title for sheet in worksheets]
        except Exception as e:
            st.warning(f"Aviso ao listar abas: {e}")
            return
        
        for aba in abas_necessarias:
            if aba not in abas_existentes:
                try:
                    worksheet = spreadsheet.add_worksheet(title=aba, rows=100, cols=20)
                    time.sleep(0.5)  # Pequena pausa entre criações
                    
                    # Definir cabeçalhos conforme a aba
                    if aba == "Produtos":
                        headers = ["Codigo", "Referencia", "SKU", "EAN", "Marca", "Grupo", 
                                  "Fornecedor", "Valor", "Descricao", "Descricao_Complementar",
                                  "Estoque_Atual", "Estoque_Minimo", "Endereco"]
                        worksheet.append_row(headers)
                    
                    elif aba == "Necessidade_Compra":
                        headers = ["Data", "Codigo", "Descricao", "Estoque_Atual", 
                                  "Estoque_Minimo", "Necessidade", "Fornecedor", "Valor_Total"]
                        worksheet.append_row(headers)
                    
                    elif aba == "Orcamentos":
                        headers = ["Num_Orcamento", "Data_Solicitacao", "Requisitante", 
                                  "Endereco", "Fornecedor", "Codigo", "Descricao", "Quantidade",
                                  "Valor_Unit", "Valor_Total", "Status", "Motivo"]
                        worksheet.append_row(headers)
                    
                    elif aba == "Entradas":
                        headers = ["Num_Orcamento", "Num_Romaneio", "Data_Recebimento",
                                  "Codigo", "Descricao", "Qtd_Comprada", "Qtd_Entregue",
                                  "Status", "Observacao"]
                        worksheet.append_row(headers)
                    
                    elif aba == "Fechamentos":
                        headers = ["Periodo", "Fornecedor", "Data_Inicial", "Data_Final",
                                  "Num_Orcamento", "Codigo", "SKU", "Descricao", 
                                  "Quantidade", "Valor_Total"]
                        worksheet.append_row(headers)
                        
                    st.success(f"✅ Aba '{aba}' criada com sucesso!")
                    
                except Exception as e:
                    st.warning(f"Não foi possível criar a aba '{aba}': {e}")
                    
    except Exception as e:
        st.error(f"Erro na inicialização: {e}")

# Funções CRUD otimizadas
@st.cache_data(ttl=300, show_spinner=False)
def buscar_produtos(spreadsheet, filtros=None):
    """Busca produtos com filtros opcionais"""
    try:
        worksheet = spreadsheet.worksheet("Produtos")
        data = worksheet.get_all_values()
        
        if len(data) <= 1:  # Apenas cabeçalho ou vazio
            return pd.DataFrame()
            
        headers = data[0]
        rows = data[1:]
        
        df = pd.DataFrame(rows, columns=headers)
        
        if filtros and not df.empty:
            for campo, valor in filtros.items():
                if valor and campo in df.columns:
                    df = df[df[campo].astype(str).str.contains(str(valor), case=False, na=False)]
        
        return df
    except Exception as e:
        st.error(f"Erro ao buscar produtos: {e}")
        return pd.DataFrame()

def cadastrar_produto(spreadsheet, dados_produto):
    """Cadastra um novo produto"""
    try:
        worksheet = spreadsheet.worksheet("Produtos")
        worksheet.append_row(list(dados_produto.values()))
        st.cache_data.clear()  # Limpar cache após modificação
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar produto: {e}")
        return False

# Interface Principal SIMPLIFICADA
def main():
    # Título principal
    st.title("📦 Sistema de Compras e Estoque")
    st.markdown("---")
    
    # Indicador de carregamento
    with st.spinner("Conectando ao Google Sheets..."):
        spreadsheet = connect_to_gsheet()
    
    if spreadsheet is None:
        mostrar_instrucoes_configuracao()
        return
    
    # Inicialização simplificada
    try:
        inicializar_planilhas(spreadsheet)
    except Exception as e:
        st.warning(f"Aviso na inicialização: {e}")
    
    # Menu lateral simplificado
    menu = st.sidebar.selectbox(
        "📋 Menu Principal",
        [
            "🏠 Dashboard",
            "📝 Produtos", 
            "⚠️ Necessidade Compra",
            "💰 Orçamentos",
            "📥 Entradas",
            "⚙️ Configurações"
        ]
    )
    
    # Navegação simplificada
    if menu == "🏠 Dashboard":
        pagina_dashboard(spreadsheet)
    elif menu == "📝 Produtos":
        pagina_produtos(spreadsheet)
    elif menu == "⚠️ Necessidade Compra":
        pagina_necessidade_compra(spreadsheet)
    elif menu == "💰 Orçamentos":
        pagina_orcamentos(spreadsheet)
    elif menu == "📥 Entradas":
        pagina_entradas(spreadsheet)
    elif menu == "⚙️ Configurações":
        pagina_configuracoes()

def mostrar_instrucoes_configuracao():
    """Mostra instruções de configuração quando não consegue conectar"""
    st.error("⚠️ Não foi possível conectar ao Google Sheets.")
    
    with st.expander("🔧 Instruções de Configuração", expanded=True):
        st.markdown("""
        **Siga estes passos para configurar:**
        
        1. **Crie uma conta de serviço no Google Cloud Console**
        2. **Ative as APIs:**
           - Google Sheets API
           - Google Drive API
        
        3. **Baixe o JSON da conta de serviço**
        
        4. **Adicione no Streamlit Secrets (.streamlit/secrets.toml):**
        ```toml
        [gcp_service_account]
        type = "service_account"
        project_id = "seu-project-id"
        private_key_id = "sua-chave"
        private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
        client_email = "email@projeto.iam.gserviceaccount.com"
        client_id = "123456789"
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
        ```
        
        5. **Compartilhe sua planilha com o email da conta de serviço**
        """)

# Páginas simplificadas
def pagina_dashboard(spreadsheet):
    st.header("🏠 Dashboard")
    
    try:
        # Métricas rápidas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            df_produtos = buscar_produtos(spreadsheet)
            st.metric("Total de Produtos", len(df_produtos) if not df_produtos.empty else 0)
        
        with col2:
            if not df_produtos.empty and 'Estoque_Atual' in df_produtos.columns:
                criticos = len(df_produtos[
                    df_produtos['Estoque_Atual'].astype(float) <= 
                    df_produtos['Estoque_Minimo'].astype(float)
                ])
                st.metric("Produtos Críticos", criticos)
            else:
                st.metric("Produtos Críticos", 0)
        
        with col3:
            st.metric("Sistema", "✅ Operacional")
            
    except Exception as e:
        st.error(f"Erro no dashboard: {e}")

def pagina_produtos(spreadsheet):
    st.header("📝 Gerenciar Produtos")
    
    tab1, tab2 = st.tabs(["📋 Lista de Produtos", "➕ Novo Produto"])
    
    with tab1:
        df_produtos = buscar_produtos(spreadsheet)
        if not df_produtos.empty:
            st.dataframe(df_produtos, use_container_width=True)
        else:
            st.info("Nenhum produto cadastrado.")
    
    with tab2:
        with st.form("novo_produto"):
            codigo = st.text_input("Código*")
            descricao = st.text_input("Descrição*")
            fornecedor = st.text_input("Fornecedor")
            valor = st.number_input("Valor R$", min_value=0.0, value=0.0)
            
            if st.form_submit_button("Cadastrar Produto"):
                if codigo and descricao:
                    dados = {
                        "Codigo": codigo,
                        "Descricao": descricao, 
                        "Fornecedor": fornecedor,
                        "Valor": valor,
                        "Estoque_Atual": 0,
                        "Estoque_Minimo": 0
                    }
                    if cadastrar_produto(spreadsheet, dados):
                        st.success("Produto cadastrado!")
                        st.rerun()
                else:
                    st.error("Código e Descrição são obrigatórios!")

def pagina_necessidade_compra(spreadsheet):
    st.header("⚠️ Necessidade de Compra")
    
    df_produtos = buscar_produtos(spreadsheet)
    if not df_produtos.empty:
        # Filtro simples
        necessidade = df_produtos[
            df_produtos['Estoque_Atual'].astype(float) <= 
            df_produtos['Estoque_Minimo'].astype(float)
        ]
        
        if not necessidade.empty:
            st.dataframe(necessidade, use_container_width=True)
        else:
            st.success("✅ Estoque adequado!")
    else:
        st.info("Nenhum produto cadastrado.")

def pagina_orcamentos(spreadsheet):
    st.header("💰 Orçamentos")
    st.info("Funcionalidade em desenvolvimento...")

def pagina_entradas(spreadsheet):
    st.header("📥 Entradas")
    st.info("Funcionalidade em desenvolvimento...")

def pagina_configuracoes():
    st.header("⚙️ Configurações")
    st.info("Verifique a conexão com o Google Sheets acima.")

# Ponto de entrada seguro
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Erro crítico na aplicação: {e}")
        st.info("Recarregue a página ou verifique o console para mais detalhes.")
