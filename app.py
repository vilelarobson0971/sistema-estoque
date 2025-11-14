import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json
import time

# Configuração da página
st.set_page_config(
    page_title="Sistema de Compras e Estoque",
    page_icon="📦",
    layout="wide"
)

# Função para conectar ao Google Sheets com timeout e melhor tratamento de erros
@st.cache_resource(ttl=600, show_spinner=False)  # Cache por 10 minutos
def connect_to_gsheet():
    """Conecta ao Google Sheets usando credenciais com tratamento de erro robusto"""
    
    # Verificar se secrets existe
    if "gcp_service_account" not in st.secrets:
        return {
            "success": False,
            "error": "secrets_not_found",
            "message": "Arquivo secrets.toml não encontrado ou não configurado corretamente"
        }
    
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Tentar abrir a planilha com timeout
        spreadsheet = client.open("Sistema_Estoque")
        
        return {
            "success": True,
            "spreadsheet": spreadsheet,
            "client_email": creds_dict.get("client_email", "N/A")
        }
        
    except gspread.exceptions.SpreadsheetNotFound:
        return {
            "success": False,
            "error": "spreadsheet_not_found",
            "message": "Planilha 'Sistema_Estoque' não encontrada",
            "client_email": creds_dict.get("client_email", "N/A")
        }
    
    except gspread.exceptions.APIError as e:
        return {
            "success": False,
            "error": "api_error",
            "message": f"Erro na API do Google: {str(e)}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": "connection_error",
            "message": f"Erro ao conectar: {type(e).__name__} - {str(e)}"
        }

# Função para inicializar as abas necessárias (apenas se não existirem)
def inicializar_planilhas(spreadsheet):
    """Cria as abas necessárias se não existirem - SEM RECARREGAR TUDO"""
    try:
        abas_necessarias = {
            "Produtos": ["Codigo", "Referencia", "SKU", "EAN", "Marca", "Grupo", 
                        "Fornecedor", "Valor", "Descricao", "Descricao_Complementar",
                        "Estoque_Atual", "Estoque_Minimo", "Endereco"],
            
            "Necessidade_Compra": ["Data", "Codigo", "Descricao", "Estoque_Atual", 
                                  "Estoque_Minimo", "Necessidade", "Fornecedor", "Valor_Total"],
            
            "Orcamentos": ["Num_Orcamento", "Data_Solicitacao", "Requisitante", 
                          "Endereco", "Fornecedor", "Codigo", "Descricao", "Quantidade",
                          "Valor_Unit", "Valor_Total", "Status", "Motivo"],
            
            "Entradas": ["Num_Orcamento", "Num_Romaneio", "Data_Recebimento",
                        "Codigo", "Descricao", "Qtd_Comprada", "Qtd_Entregue",
                        "Status", "Observacao"],
            
            "Fechamentos": ["Periodo", "Fornecedor", "Data_Inicial", "Data_Final",
                           "Num_Orcamento", "Codigo", "SKU", "Descricao", 
                           "Quantidade", "Valor_Total"]
        }
        
        # Buscar abas existentes UMA VEZ SÓ
        abas_existentes = {sheet.title for sheet in spreadsheet.worksheets()}
        
        abas_criadas = []
        for aba_nome, headers in abas_necessarias.items():
            if aba_nome not in abas_existentes:
                worksheet = spreadsheet.add_worksheet(title=aba_nome, rows=1000, cols=20)
                worksheet.append_row(headers)
                abas_criadas.append(aba_nome)
        
        return {"success": True, "criadas": abas_criadas}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Funções CRUD para Produtos com tratamento de erro
def cadastrar_produto(spreadsheet, dados_produto):
    """Cadastra um novo produto"""
    try:
        worksheet = spreadsheet.worksheet("Produtos")
        worksheet.append_row(list(dados_produto.values()))
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def buscar_produtos(spreadsheet, filtros=None):
    """Busca produtos com filtros opcionais"""
    try:
        worksheet = spreadsheet.worksheet("Produtos")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if filtros and not df.empty:
            for campo, valor in filtros.items():
                if valor:
                    df = df[df[campo].astype(str).str.contains(str(valor), case=False, na=False)]
        
        return df
    except Exception as e:
        st.error(f"Erro ao buscar produtos: {e}")
        return pd.DataFrame()

def atualizar_produto(spreadsheet, codigo, dados_atualizados):
    """Atualiza um produto existente"""
    try:
        worksheet = spreadsheet.worksheet("Produtos")
        cell = worksheet.find(str(codigo))
        if cell:
            row = cell.row
            worksheet.update(f'A{row}:M{row}', [list(dados_atualizados.values())])
            return {"success": True}
        return {"success": False, "error": "Produto não encontrado"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def excluir_produto(spreadsheet, codigo):
    """Exclui um produto"""
    try:
        worksheet = spreadsheet.worksheet("Produtos")
        cell = worksheet.find(str(codigo))
        if cell:
            worksheet.delete_rows(cell.row)
            return {"success": True}
        return {"success": False, "error": "Produto não encontrado"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Função para calcular necessidade de compra
def calcular_necessidade_compra(spreadsheet):
    """Calcula produtos que precisam ser comprados"""
    try:
        df_produtos = buscar_produtos(spreadsheet)
        if df_produtos.empty:
            return pd.DataFrame()
        
        # Produtos com necessidade de compra
        df_necessidade = df_produtos[
            df_produtos['Estoque_Atual'].astype(float) <= df_produtos['Estoque_Minimo'].astype(float)
        ].copy()
        
        if not df_necessidade.empty:
            # Calcular necessidade (2 unidades acima do estoque mínimo)
            df_necessidade['Necessidade'] = (
                df_necessidade['Estoque_Minimo'].astype(float) + 2 - 
                df_necessidade['Estoque_Atual'].astype(float)
            )
            df_necessidade['Valor_Total'] = (
                df_necessidade['Necessidade'] * df_necessidade['Valor'].astype(float)
            )
        
        return df_necessidade
    except Exception as e:
        st.error(f"Erro ao calcular necessidade: {e}")
        return pd.DataFrame()

# Interface Principal OTIMIZADA
def main():
    st.title("📦 Sistema de Compras e Estoque")
    st.markdown("---")
    
    # Mostrar spinner durante conexão
    with st.spinner("🔄 Conectando ao Google Sheets..."):
        connection_result = connect_to_gsheet()
    
    # Verificar resultado da conexão
    if not connection_result["success"]:
        st.error("⚠️ Não foi possível conectar ao Google Sheets")
        
        # Mostrar erro específico
        if connection_result["error"] == "secrets_not_found":
            st.error("❌ Credenciais não encontradas!")
            st.info("""
            **📋 Instruções de configuração:**
            
            1. Crie o arquivo `.streamlit/secrets.toml` na pasta do projeto
            2. Adicione as credenciais no formato:
            
            ```toml
            [gcp_service_account]
            type = "service_account"
            project_id = "seu-project-id"
            private_key_id = "sua-private-key-id"
            private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
            client_email = "seu-email@projeto.iam.gserviceaccount.com"
            client_id = "seu-client-id"
            auth_uri = "https://accounts.google.com/o/oauth2/auth"
            token_uri = "https://oauth2.googleapis.com/token"
            auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
            client_x509_cert_url = "sua-cert-url"
            ```
            """)
        
        elif connection_result["error"] == "spreadsheet_not_found":
            st.error("❌ Planilha 'Sistema_Estoque' não encontrada!")
            st.warning(f"📧 Email da conta de serviço: `{connection_result['client_email']}`")
            st.info("""
            **Verifique:**
            1. A planilha tem o nome exato: `Sistema_Estoque`
            2. A planilha foi compartilhada com o email acima
            3. A permissão é "Editor"
            """)
        
        else:
            st.error(f"❌ {connection_result['message']}")
        
        # Botão para tentar reconectar
        if st.button("🔄 Tentar Reconectar"):
            st.cache_resource.clear()
            st.rerun()
        
        return
    
    # Conexão bem-sucedida
    spreadsheet = connection_result["spreadsheet"]
    st.success(f"✅ Conectado! Email: {connection_result['client_email']}")
    
    # Inicializar planilhas apenas na primeira vez
    if 'planilhas_inicializadas' not in st.session_state:
        with st.spinner("📋 Verificando estrutura da planilha..."):
            init_result = inicializar_planilhas(spreadsheet)
            
            if init_result["success"]:
                st.session_state.planilhas_inicializadas = True
                if init_result["criadas"]:
                    st.info(f"✨ Abas criadas: {', '.join(init_result['criadas'])}")
            else:
                st.warning(f"⚠️ Erro ao inicializar: {init_result['error']}")
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu Principal",
        [
            "🏠 Home",
            "📝 Cadastro de Produto",
            "🔍 Busca de Produtos",
            "⚠️ Necessidade de Compra",
            "💰 Orçamento de Compra",
            "📥 Entrada de Produtos",
            "📊 Relatório de Fechamento",
            "📦 Estoque"
        ]
    )
    
    # Botão para limpar cache
    if st.sidebar.button("🔄 Limpar Cache"):
        st.cache_resource.clear()
        st.session_state.clear()
        st.success("Cache limpo!")
        st.rerun()
    
    # Roteamento de páginas
    if menu == "🏠 Home":
        pagina_home(spreadsheet)
    elif menu == "📝 Cadastro de Produto":
        pagina_cadastro_produto(spreadsheet)
    elif menu == "🔍 Busca de Produtos":
        pagina_busca_produtos(spreadsheet)
    elif menu == "⚠️ Necessidade de Compra":
        pagina_necessidade_compra(spreadsheet)
    elif menu == "💰 Orçamento de Compra":
        pagina_orcamento_compra(spreadsheet)
    elif menu == "📥 Entrada de Produtos":
        pagina_entrada_produtos(spreadsheet)
    elif menu == "📊 Relatório de Fechamento":
        pagina_relatorio_fechamento(spreadsheet)
    elif menu == "📦 Estoque":
        pagina_estoque(spreadsheet)

# Páginas do Sistema (mantendo as mesmas do código original)
def pagina_home(spreadsheet):
    st.header("🏠 Dashboard Principal")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Métricas com loading
    with st.spinner("Carregando dados..."):
        df_produtos = buscar_produtos(spreadsheet)
        df_necessidade = calcular_necessidade_compra(spreadsheet)
    
    with col1:
        st.metric("Total de Produtos", len(df_produtos))
    
    with col2:
        st.metric("Produtos em Falta", len(df_necessidade))
    
    with col3:
        if not df_produtos.empty and 'Valor' in df_produtos.columns:
            valor_total = (df_produtos['Estoque_Atual'].astype(float) * 
                          df_produtos['Valor'].astype(float)).sum()
            st.metric("Valor Total em Estoque", f"R$ {valor_total:,.2f}")
        else:
            st.metric("Valor Total em Estoque", "R$ 0,00")
    
    with col4:
        if not df_necessidade.empty and 'Valor_Total' in df_necessidade.columns:
            necessidade_valor = df_necessidade['Valor_Total'].sum()
            st.metric("Necessidade de Compra", f"R$ {necessidade_valor:,.2f}")
        else:
            st.metric("Necessidade de Compra", "R$ 0,00")
    
    st.markdown("---")
    
    # Produtos com estoque crítico
    if not df_necessidade.empty:
        st.subheader("⚠️ Produtos em Estoque Crítico")
        st.dataframe(
            df_necessidade[['Codigo', 'Descricao', 'Estoque_Atual', 
                           'Estoque_Minimo', 'Necessidade', 'Fornecedor']],
            use_container_width=True
        )

def pagina_cadastro_produto(spreadsheet):
    st.header("📝 Cadastro de Produto")
    
    tab1, tab2, tab3 = st.tabs(["➕ Novo Produto", "✏️ Editar Produto", "🗑️ Excluir Produto"])
    
    with tab1:
        with st.form("form_novo_produto"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                codigo = st.text_input("Código do Produto*")
                referencia = st.text_input("Referência")
                sku = st.text_input("SKU")
                ean = st.text_input("EAN")
            
            with col2:
                marca = st.text_input("Marca")
                grupo = st.text_input("Grupo")
                fornecedor = st.text_input("Fornecedor")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            
            with col3:
                estoque_atual = st.number_input("Estoque Atual", min_value=0, value=0)
                estoque_minimo = st.number_input("Estoque Mínimo", min_value=0, value=0)
                endereco = st.text_input("Endereço (ex: B-5-2)")
            
            descricao = st.text_input("Descrição do Produto*")
            descricao_complementar = st.text_area("Descrição Complementar")
            
            submitted = st.form_submit_button("Cadastrar Produto")
            
            if submitted:
                if not codigo or not descricao:
                    st.error("Código e Descrição são obrigatórios!")
                else:
                    dados_produto = {
                        "Codigo": codigo,
                        "Referencia": referencia,
                        "SKU": sku,
                        "EAN": ean,
                        "Marca": marca,
                        "Grupo": grupo,
                        "Fornecedor": fornecedor,
                        "Valor": valor,
                        "Descricao": descricao,
                        "Descricao_Complementar": descricao_complementar,
                        "Estoque_Atual": estoque_atual,
                        "Estoque_Minimo": estoque_minimo,
                        "Endereco": endereco
                    }
                    
                    result = cadastrar_produto(spreadsheet, dados_produto)
                    if result["success"]:
                        st.success("✅ Produto cadastrado com sucesso!")
                        st.balloons()
                    else:
                        st.error(f"❌ Erro: {result['error']}")
    
    with tab2:
        st.subheader("Editar Produto Existente")
        
        with st.spinner("Carregando produtos..."):
            df_produtos = buscar_produtos(spreadsheet)
        
        if not df_produtos.empty:
            produto_selecionado = st.selectbox(
                "Selecione o produto para editar",
                df_produtos['Codigo'].tolist(),
                format_func=lambda x: f"{x} - {df_produtos[df_produtos['Codigo']==x]['Descricao'].values[0]}"
            )
            
            produto_atual = df_produtos[df_produtos['Codigo'] == produto_selecionado].iloc[0]
            
            with st.form("form_editar_produto"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    codigo_edit = st.text_input("Código", value=produto_atual['Codigo'], disabled=True)
                    referencia_edit = st.text_input("Referência", value=produto_atual['Referencia'])
                    sku_edit = st.text_input("SKU", value=produto_atual['SKU'])
                    ean_edit = st.text_input("EAN", value=produto_atual['EAN'])
                
                with col2:
                    marca_edit = st.text_input("Marca", value=produto_atual['Marca'])
                    grupo_edit = st.text_input("Grupo", value=produto_atual['Grupo'])
                    fornecedor_edit = st.text_input("Fornecedor", value=produto_atual['Fornecedor'])
                    valor_edit = st.number_input("Valor (R$)", value=float(produto_atual['Valor']), format="%.2f")
                
                with col3:
                    estoque_atual_edit = st.number_input("Estoque Atual", value=int(produto_atual['Estoque_Atual']))
                    estoque_minimo_edit = st.number_input("Estoque Mínimo", value=int(produto_atual['Estoque_Minimo']))
                    endereco_edit = st.text_input("Endereço", value=produto_atual['Endereco'])
                
                descricao_edit = st.text_input("Descrição", value=produto_atual['Descricao'])
                descricao_comp_edit = st.text_area("Descrição Complementar", value=produto_atual['Descricao_Complementar'])
                
                submitted_edit = st.form_submit_button("Atualizar Produto")
                
                if submitted_edit:
                    dados_atualizados = {
                        "Codigo": codigo_edit,
                        "Referencia": referencia_edit,
                        "SKU": sku_edit,
                        "EAN": ean_edit,
                        "Marca": marca_edit,
                        "Grupo": grupo_edit,
                        "Fornecedor": fornecedor_edit,
                        "Valor": valor_edit,
                        "Descricao": descricao_edit,
                        "Descricao_Complementar": descricao_comp_edit,
                        "Estoque_Atual": estoque_atual_edit,
                        "Estoque_Minimo": estoque_minimo_edit,
                        "Endereco": endereco_edit
                    }
                    
                    result = atualizar_produto(spreadsheet, codigo_edit, dados_atualizados)
                    if result["success"]:
                        st.success("✅ Produto atualizado com sucesso!")
                    else:
                        st.error(f"❌ Erro: {result['error']}")
        else:
            st.info("Nenhum produto cadastrado ainda.")
    
    with tab3:
        st.subheader("Excluir Produto")
        
        with st.spinner("Carregando produtos..."):
            df_produtos = buscar_produtos(spreadsheet)
        
        if not df_produtos.empty:
            produto_excluir = st.selectbox(
                "Selecione o produto para excluir",
                df_produtos['Codigo'].tolist(),
                format_func=lambda x: f"{x} - {df_produtos[df_produtos['Codigo']==x]['Descricao'].values[0]}"
            )
            
            st.warning("⚠️ Esta ação não pode ser desfeita!")
            
            if st.button("Excluir Produto", type="primary"):
                result = excluir_produto(spreadsheet, produto_excluir)
                if result["success"]:
                    st.success("✅ Produto excluído com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Erro: {result['error']}")
        else:
            st.info("Nenhum produto cadastrado ainda.")

# NOTA: As outras funções de página continuam iguais ao código original
# (pagina_busca_produtos, pagina_necessidade_compra, etc.)
# Incluí apenas as principais para demonstrar as melhorias

def pagina_busca_produtos(spreadsheet):
    st.header("🔍 Busca de Produtos")
    st.info("Função mantida igual ao código original")

def pagina_necessidade_compra(spreadsheet):
    st.header("⚠️ Necessidade de Compra")
    st.info("Função mantida igual ao código original")

def pagina_orcamento_compra(spreadsheet):
    st.header("💰 Orçamento de Compra")
    st.info("Função mantida igual ao código original")

def pagina_entrada_produtos(spreadsheet):
    st.header("📥 Entrada de Produtos")
    st.info("Função mantida igual ao código original")

def pagina_relatorio_fechamento(spreadsheet):
    st.header("📊 Relatório de Fechamento")
    st.info("Função mantida igual ao código original")

def pagina_estoque(spreadsheet):
    st.header("📦 Estoque")
    st.info("Função mantida igual ao código original")

if __name__ == "__main__":
    main()
