import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json

# Configuração da página
st.set_page_config(
    page_title="Sistema de Compras e Estoque",
    page_icon="📦",
    layout="wide"
)

# Função para conectar ao Google Sheets
@st.cache_resource
def connect_to_gsheet():
    """Conecta ao Google Sheets usando credenciais"""
    try:
        # As credenciais devem estar em secrets do Streamlit
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrir a planilha (substitua pelo nome da sua planilha)
        spreadsheet = client.open("Sistema_Estoque")
        return spreadsheet
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return None

# Função para inicializar as abas necessárias
def inicializar_planilhas(spreadsheet):
    """Cria as abas necessárias se não existirem"""
    abas_necessarias = [
        "Produtos",
        "Necessidade_Compra",
        "Orcamentos",
        "Entradas",
        "Fechamentos"
    ]
    
    abas_existentes = [sheet.title for sheet in spreadsheet.worksheets()]
    
    for aba in abas_necessarias:
        if aba not in abas_existentes:
            worksheet = spreadsheet.add_worksheet(title=aba, rows=1000, cols=20)
            
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

# Funções CRUD para Produtos
def cadastrar_produto(spreadsheet, dados_produto):
    """Cadastra um novo produto"""
    try:
        worksheet = spreadsheet.worksheet("Produtos")
        worksheet.append_row(list(dados_produto.values()))
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar produto: {e}")
        return False

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
            col_start = 1
            worksheet.update(f'A{row}:M{row}', [list(dados_atualizados.values())])
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar produto: {e}")
        return False

def excluir_produto(spreadsheet, codigo):
    """Exclui um produto"""
    try:
        worksheet = spreadsheet.worksheet("Produtos")
        cell = worksheet.find(str(codigo))
        if cell:
            worksheet.delete_rows(cell.row)
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir produto: {e}")
        return False

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

# Interface Principal
def main():
    st.title("📦 Sistema de Compras e Estoque")
    st.markdown("---")
    
    # Conectar ao Google Sheets
    spreadsheet = connect_to_gsheet()
    
    if spreadsheet is None:
        st.error("⚠️ Não foi possível conectar ao Google Sheets. Verifique suas credenciais.")
        st.info("""
        **Instruções de configuração:**
        1. Crie um projeto no Google Cloud Console
        2. Ative a API do Google Sheets e Google Drive
        3. Crie uma conta de serviço e baixe o JSON de credenciais
        4. Adicione as credenciais em `.streamlit/secrets.toml`:
        ```
        [gcp_service_account]
        type = "service_account"
        project_id = "seu-project-id"
        private_key_id = "sua-private-key-id"
        private_key = "sua-private-key"
        client_email = "seu-client-email"
        client_id = "seu-client-id"
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "sua-cert-url"
        ```
        5. Compartilhe a planilha com o email da conta de serviço
        """)
        return
    
    # Inicializar planilhas
    inicializar_planilhas(spreadsheet)
    
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

# Páginas do Sistema
def pagina_home(spreadsheet):
    st.header("🏠 Dashboard Principal")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Métricas
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
                    
                    if cadastrar_produto(spreadsheet, dados_produto):
                        st.success("✅ Produto cadastrado com sucesso!")
                        st.balloons()
    
    with tab2:
        st.subheader("Editar Produto Existente")
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
                    
                    if atualizar_produto(spreadsheet, codigo_edit, dados_atualizados):
                        st.success("✅ Produto atualizado com sucesso!")
        else:
            st.info("Nenhum produto cadastrado ainda.")
    
    with tab3:
        st.subheader("Excluir Produto")
        df_produtos = buscar_produtos(spreadsheet)
        
        if not df_produtos.empty:
            produto_excluir = st.selectbox(
                "Selecione o produto para excluir",
                df_produtos['Codigo'].tolist(),
                format_func=lambda x: f"{x} - {df_produtos[df_produtos['Codigo']==x]['Descricao'].values[0]}"
            )
            
            st.warning("⚠️ Esta ação não pode ser desfeita!")
            
            if st.button("Excluir Produto", type="primary"):
                if excluir_produto(spreadsheet, produto_excluir):
                    st.success("✅ Produto excluído com sucesso!")
                    st.rerun()
        else:
            st.info("Nenhum produto cadastrado ainda.")

def pagina_busca_produtos(spreadsheet):
    st.header("🔍 Busca de Produtos")
    
    with st.expander("🔎 Filtros de Busca", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtro_codigo = st.text_input("Código")
            filtro_descricao = st.text_input("Descrição")
        
        with col2:
            filtro_referencia = st.text_input("Referência")
            filtro_marca = st.text_input("Marca")
        
        with col3:
            filtro_grupo = st.text_input("Grupo")
            filtro_fornecedor = st.text_input("Fornecedor")
        
        with col4:
            filtro_endereco = st.text_input("Endereço")
    
    filtros = {}
    if filtro_codigo:
        filtros['Codigo'] = filtro_codigo
    if filtro_descricao:
        filtros['Descricao'] = filtro_descricao
    if filtro_referencia:
        filtros['Referencia'] = filtro_referencia
    if filtro_marca:
        filtros['Marca'] = filtro_marca
    if filtro_grupo:
        filtros['Grupo'] = filtro_grupo
    if filtro_fornecedor:
        filtros['Fornecedor'] = filtro_fornecedor
    if filtro_endereco:
        filtros['Endereco'] = filtro_endereco
    
    df_resultados = buscar_produtos(spreadsheet, filtros)
    
    if not df_resultados.empty:
        st.success(f"✅ Encontrados {len(df_resultados)} produto(s)")
        st.dataframe(df_resultados, use_container_width=True)
        
        # Opção de exportar
        csv = df_resultados.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"produtos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum produto encontrado com os filtros aplicados.")

def pagina_necessidade_compra(spreadsheet):
    st.header("⚠️ Necessidade de Compra")
    
    df_necessidade = calcular_necessidade_compra(spreadsheet)
    
    if not df_necessidade.empty:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            fornecedor_filtro = st.selectbox(
                "Filtrar por Fornecedor",
                ["Todos"] + df_necessidade['Fornecedor'].unique().tolist()
            )
        
        with col2:
            grupo_filtro = st.selectbox(
                "Filtrar por Grupo",
                ["Todos"] + df_necessidade['Grupo'].unique().tolist()
            )
        
        # Aplicar filtros
        df_filtrado = df_necessidade.copy()
        if fornecedor_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Fornecedor'] == fornecedor_filtro]
        if grupo_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Grupo'] == grupo_filtro]
        
        # Informações resumidas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Itens com Necessidade", len(df_filtrado))
        with col2:
            st.metric("Quantidade Total", int(df_filtrado['Necessidade'].sum()))
        with col3:
            st.metric("Valor Total", f"R$ {df_filtrado['Valor_Total'].sum():,.2f}")
        
        st.markdown("---")
        
        # Exibir tabela
        st.dataframe(
            df_filtrado[['Codigo', 'Descricao', 'Estoque_Atual', 'Estoque_Minimo', 
                        'Necessidade', 'Fornecedor', 'Grupo', 'Valor_Total']],
            use_container_width=True
        )
        
        # Exportar
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Relatório",
            data=csv,
            file_name=f"necessidade_compra_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.success("✅ Todos os produtos estão com estoque adequado!")

def pagina_orcamento_compra(spreadsheet):
    st.header("💰 Orçamento de Compra")
    
    tab1, tab2 = st.tabs(["➕ Novo Orçamento", "📋 Consultar Orçamentos"])
    
    with tab1:
        with st.form("form_orcamento"):
            col1, col2 = st.columns(2)
            
            with col1:
                num_orcamento = st.text_input("Número do Orçamento*")
                requisitante = st.text_input("Requisitante*")
                endereco = st.text_input("Endereço")
            
            with col2:
                data_solicitacao = st.date_input("Data da Solicitação", value=datetime.now())
                usar_necessidade = st.radio("Buscar da Necessidade?", ["Não", "Sim"])
                fornecedor_orc = st.text_input("Fornecedor*")
            
            st.markdown("---")
            
            if usar_necessidade == "Sim":
                df_necessidade = calcular_necessidade_compra(spreadsheet)
                if not df_necessidade.empty:
                    df_fornecedor = df_necessidade[df_necessidade['Fornecedor'] == fornecedor_orc]
                    
                    if not df_fornecedor.empty:
                        st.subheader("Produtos com Necessidade")
                        
                        produtos_selecionados = []
                        for idx, row in df_fornecedor.iterrows():
                            col_a, col_b, col_c = st.columns([3, 1, 1])
                            with col_a:
                                st.text(f"{row['Codigo']} - {row['Descricao']}")
                            with col_b:
                                qtd = st.number_input(
                                    "Qtd", 
                                    min_value=0, 
                                    value=int(row['Necessidade']),
                                    key=f"qtd_{row['Codigo']}"
                                )
                            with col_c:
                                incluir = st.checkbox("Incluir", key=f"inc_{row['Codigo']}")
                            
                            if incluir and qtd > 0:
                                produtos_selecionados.append({
                                    'Codigo': row['Codigo'],
                                    'Descricao': row['Descricao'],
                                    'Quantidade': qtd,
                                    'Valor_Unit': row['Valor'],
                                    'Valor_Total': qtd * float(row['Valor'])
                                })
                    else:
                        st.warning(f"Nenhum produto com necessidade para o fornecedor {fornecedor_orc}")
                        produtos_selecionados = []
                else:
                    st.info("Não há produtos com necessidade de compra no momento.")
                    produtos_selecionados = []
            else:
                st.subheader("Adicionar Produtos Manualmente")
                num_produtos = st.number_input("Quantos produtos adicionar?", min_value=1, max_value=20, value=1)
                
                produtos_selecionados = []
                df_produtos = buscar_produtos(spreadsheet)
                
                for i in range(num_produtos):
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    
                    with col_a:
                        if not df_produtos.empty:
                            codigo_sel = st.selectbox(
                                f"Produto {i+1}",
                                df_produtos['Codigo'].tolist(),
                                key=f"prod_{i}",
                                format_func=lambda x: f"{x} - {df_produtos[df_produtos['Codigo']==x]['Descricao'].values[0]}"
                            )
                            produto_info = df_produtos[df_produtos['Codigo'] == codigo_sel].iloc[0]
                        else:
                            st.warning("Nenhum produto cadastrado")
                            break
                    
                    with col_b:
                        qtd_manual = st.number_input("Quantidade", min_value=1, value=1, key=f"qtd_manual_{i}")
                    
                    with col_c:
                        st.metric("Valor Unit.", f"R$ {float(produto_info['Valor']):.2f}")
                    
                    produtos_selecionados.append({
                        'Codigo': codigo_sel,
                        'Descricao': produto_info['Descricao'],
                        'Quantidade': qtd_manual,
                        'Valor_Unit': produto_info['Valor'],
                        'Valor_Total': qtd_manual * float(produto_info['Valor'])
                    })
            
            motivo = st.text_area("Motivo da Compra")
            
            submitted_orc = st.form_submit_button("Criar Orçamento")
            
            if submitted_orc:
                if not num_orcamento or not requisitante or not fornecedor_orc:
                    st.error("Preencha os campos obrigatórios!")
                elif not produtos_selecionados:
                    st.error("Adicione pelo menos um produto ao orçamento!")
                else:
                    try:
                        worksheet = spreadsheet.worksheet("Orcamentos")
                        for produto in produtos_selecionados:
                            row_data = [
                                num_orcamento,
                                data_solicitacao.strftime("%d/%m/%Y"),
                                requisitante,
                                endereco,
                                fornecedor_orc,
                                produto['Codigo'],
                                produto['Descricao'],
                                produto['Quantidade'],
                                produto['Valor_Unit'],
                                produto['Valor_Total'],
                                "Pendente",
                                motivo
                            ]
                            worksheet.append_row(row_data)
                        
                        st.success(f"✅ Orçamento {num_orcamento} criado com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao criar orçamento: {e}")
    
    with tab2:
        st.subheader("Consultar Orçamentos Existentes")
        
        try:
            worksheet = spreadsheet.worksheet("Orcamentos")
            data = worksheet.get_all_records()
            df_orcamentos = pd.DataFrame(data)
            
            if not df_orcamentos.empty:
                # Filtros
                col1, col2, col3 = st.columns(3)
                with col1:
                    filtro_orc_num = st.text_input("Número do Orçamento")
                with col2:
                    filtro_orc_forn = st.selectbox(
                        "Fornecedor",
                        ["Todos"] + df_orcamentos['Fornecedor'].unique().tolist()
                    )
                with col3:
                    filtro_orc_status = st.selectbox(
                        "Status",
                        ["Todos"] + df_orcamentos['Status'].unique().tolist()
                    )
                
                # Aplicar filtros
                df_orc_filtrado = df_orcamentos.copy()
                if filtro_orc_num:
                    df_orc_filtrado = df_orc_filtrado[df_orc_filtrado['Num_Orcamento'].astype(str).str.contains(filtro_orc_num)]
                if filtro_orc_forn != "Todos":
                    df_orc_filtrado = df_orc_filtrado[df_orc_filtrado['Fornecedor'] == filtro_orc_forn]
                if filtro_orc_status != "Todos":
                    df_orc_filtrado = df_orc_filtrado[df_orc_filtrado['Status'] == filtro_orc_status]
                
                st.dataframe(df_orc_filtrado, use_container_width=True)
                
                # Resumo por orçamento
                if not df_orc_filtrado.empty:
                    st.markdown("---")
                    st.subheader("Resumo por Orçamento")
                    resumo = df_orc_filtrado.groupby('Num_Orcamento').agg({
                        'Valor_Total': 'sum',
                        'Quantidade': 'sum',
                        'Status': 'first',
                        'Fornecedor': 'first'
                    }).reset_index()
                    st.dataframe(resumo, use_container_width=True)
            else:
                st.info("Nenhum orçamento cadastrado ainda.")
        except Exception as e:
            st.error(f"Erro ao buscar orçamentos: {e}")

def pagina_entrada_produtos(spreadsheet):
    st.header("📥 Entrada de Produtos")
    
    tab1, tab2 = st.tabs(["➕ Nova Entrada", "📋 Consultar Entradas"])
    
    with tab1:
        tipo_entrada = st.radio("Tipo de Entrada", ["Com Orçamento", "Sem Orçamento (Correção)"])
        
        with st.form("form_entrada"):
            if tipo_entrada == "Com Orçamento":
                # Buscar orçamentos disponíveis
                try:
                    worksheet_orc = spreadsheet.worksheet("Orcamentos")
                    data_orc = worksheet_orc.get_all_records()
                    df_orcamentos = pd.DataFrame(data_orc)
                    
                    if not df_orcamentos.empty:
                        orcamentos_disponiveis = df_orcamentos['Num_Orcamento'].unique().tolist()
                        num_orc_entrada = st.selectbox("Número do Orçamento", orcamentos_disponiveis)
                        
                        # Carregar itens do orçamento
                        df_orc_selecionado = df_orcamentos[df_orcamentos['Num_Orcamento'] == num_orc_entrada]
                        
                        st.subheader("Itens do Orçamento")
                        
                        entradas = []
                        for idx, row in df_orc_selecionado.iterrows():
                            col_a, col_b, col_c = st.columns([3, 1, 1])
                            
                            with col_a:
                                st.text(f"{row['Codigo']} - {row['Descricao']}")
                            
                            with col_b:
                                st.text(f"Comprado: {row['Quantidade']}")
                            
                            with col_c:
                                qtd_entregue = st.number_input(
                                    "Entregue",
                                    min_value=0,
                                    max_value=int(row['Quantidade']),
                                    value=int(row['Quantidade']),
                                    key=f"ent_{idx}"
                                )
                            
                            # Determinar status
                            if qtd_entregue == int(row['Quantidade']):
                                status_item = "Completo"
                            elif qtd_entregue > 0:
                                status_item = "Parcial"
                            else:
                                status_item = "Pendente"
                            
                            entradas.append({
                                'Codigo': row['Codigo'],
                                'Descricao': row['Descricao'],
                                'Qtd_Comprada': row['Quantidade'],
                                'Qtd_Entregue': qtd_entregue,
                                'Status': status_item
                            })
                    else:
                        st.warning("Nenhum orçamento disponível.")
                        entradas = []
                        num_orc_entrada = None
                except Exception as e:
                    st.error(f"Erro ao carregar orçamentos: {e}")
                    entradas = []
                    num_orc_entrada = None
            else:
                # Entrada sem orçamento
                num_orc_entrada = "SEM_ORC"
                st.info("Entrada de correção de estoque")
                
                df_produtos = buscar_produtos(spreadsheet)
                if not df_produtos.empty:
                    codigo_correcao = st.selectbox(
                        "Selecione o Produto",
                        df_produtos['Codigo'].tolist(),
                        format_func=lambda x: f"{x} - {df_produtos[df_produtos['Codigo']==x]['Descricao'].values[0]}"
                    )
                    
                    produto_correcao = df_produtos[df_produtos['Codigo'] == codigo_correcao].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Estoque Atual", produto_correcao['Estoque_Atual'])
                    with col2:
                        qtd_correcao = st.number_input("Quantidade para Adicionar", min_value=1, value=1)
                    
                    entradas = [{
                        'Codigo': codigo_correcao,
                        'Descricao': produto_correcao['Descricao'],
                        'Qtd_Comprada': qtd_correcao,
                        'Qtd_Entregue': qtd_correcao,
                        'Status': 'Completo'
                    }]
                else:
                    st.warning("Nenhum produto cadastrado.")
                    entradas = []
            
            num_romaneio = st.text_input("Número do Romaneio*")
            data_recebimento = st.date_input("Data de Recebimento", value=datetime.now())
            obs_entrada = st.text_area("Observações da Entrega")
            
            submitted_entrada = st.form_submit_button("Registrar Entrada")
            
            if submitted_entrada:
                if not num_romaneio:
                    st.error("Número do romaneio é obrigatório!")
                elif not entradas:
                    st.error("Nenhum item para entrada!")
                else:
                    try:
                        worksheet_entrada = spreadsheet.worksheet("Entradas")
                        worksheet_produtos = spreadsheet.worksheet("Produtos")
                        
                        # Registrar entradas
                        for entrada in entradas:
                            if entrada['Qtd_Entregue'] > 0:
                                row_data = [
                                    num_orc_entrada,
                                    num_romaneio,
                                    data_recebimento.strftime("%d/%m/%Y"),
                                    entrada['Codigo'],
                                    entrada['Descricao'],
                                    entrada['Qtd_Comprada'],
                                    entrada['Qtd_Entregue'],
                                    entrada['Status'],
                                    obs_entrada
                                ]
                                worksheet_entrada.append_row(row_data)
                                
                                # Atualizar estoque
                                cell = worksheet_produtos.find(str(entrada['Codigo']))
                                if cell:
                                    row_num = cell.row
                                    estoque_atual_col = 11  # Coluna K (Estoque_Atual)
                                    estoque_atual = worksheet_produtos.cell(row_num, estoque_atual_col).value
                                    novo_estoque = int(estoque_atual) + entrada['Qtd_Entregue']
                                    worksheet_produtos.update_cell(row_num, estoque_atual_col, novo_estoque)
                        
                        # Atualizar status do orçamento se necessário
                        if tipo_entrada == "Com Orçamento":
                            todos_completos = all(e['Status'] == 'Completo' for e in entradas)
                            if todos_completos:
                                worksheet_orc = spreadsheet.worksheet("Orcamentos")
                                data_orc = worksheet_orc.get_all_records()
                                for i, row in enumerate(data_orc, start=2):
                                    if row['Num_Orcamento'] == num_orc_entrada:
                                        worksheet_orc.update_cell(i, 11, "Completo")
                        
                        st.success(f"✅ Entrada registrada com sucesso! Romaneio: {num_romaneio}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao registrar entrada: {e}")
    
    with tab2:
        st.subheader("Consultar Entradas")
        
        try:
            worksheet = spreadsheet.worksheet("Entradas")
            data = worksheet.get_all_records()
            df_entradas = pd.DataFrame(data)
            
            if not df_entradas.empty:
                col1, col2 = st.columns(2)
                with col1:
                    filtro_romaneio = st.text_input("Número do Romaneio")
                with col2:
                    filtro_orcamento = st.text_input("Número do Orçamento")
                
                df_ent_filtrado = df_entradas.copy()
                if filtro_romaneio:
                    df_ent_filtrado = df_ent_filtrado[df_ent_filtrado['Num_Romaneio'].astype(str).str.contains(filtro_romaneio)]
                if filtro_orcamento:
                    df_ent_filtrado = df_ent_filtrado[df_ent_filtrado['Num_Orcamento'].astype(str).str.contains(filtro_orcamento)]
                
                st.dataframe(df_ent_filtrado, use_container_width=True)
            else:
                st.info("Nenhuma entrada registrada ainda.")
        except Exception as e:
            st.error(f"Erro ao buscar entradas: {e}")

def pagina_relatorio_fechamento(spreadsheet):
    st.header("📊 Relatório de Fechamento")
    
    with st.form("form_fechamento"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fornecedor_fech = st.text_input("Fornecedor*")
        
        with col2:
            data_inicial = st.date_input("Data Inicial")
        
        with col3:
            data_final = st.date_input("Data Final", value=datetime.now())
        
        gerar_fechamento = st.form_submit_button("Gerar Relatório de Fechamento")
        
        if gerar_fechamento:
            if not fornecedor_fech:
                st.error("Fornecedor é obrigatório!")
            else:
                try:
                    # Buscar entradas no período
                    worksheet_entradas = spreadsheet.worksheet("Entradas")
                    data_entradas = worksheet_entradas.get_all_records()
                    df_entradas = pd.DataFrame(data_entradas)
                    
                    if not df_entradas.empty:
                        # Converter datas
                        df_entradas['Data_Recebimento'] = pd.to_datetime(df_entradas['Data_Recebimento'], format='%d/%m/%Y')
                        
                        # Filtrar por período
                        df_filtrado = df_entradas[
                            (df_entradas['Data_Recebimento'] >= pd.to_datetime(data_inicial)) &
                            (df_entradas['Data_Recebimento'] <= pd.to_datetime(data_final))
                        ]
                        
                        # Buscar orçamentos para pegar fornecedor
                        worksheet_orc = spreadsheet.worksheet("Orcamentos")
                        data_orc = worksheet_orc.get_all_records()
                        df_orcamentos = pd.DataFrame(data_orc)
                        
                        if not df_orcamentos.empty:
                            # Filtrar por fornecedor
                            df_orc_fornecedor = df_orcamentos[df_orcamentos['Fornecedor'] == fornecedor_fech]
                            orcamentos_fornecedor = df_orc_fornecedor['Num_Orcamento'].unique()
                            
                            df_filtrado = df_filtrado[df_filtrado['Num_Orcamento'].isin(orcamentos_fornecedor)]
                        
                        if not df_filtrado.empty:
                            # Buscar SKU dos produtos
                            df_produtos = buscar_produtos(spreadsheet)
                            df_filtrado = df_filtrado.merge(
                                df_produtos[['Codigo', 'SKU', 'Valor']], 
                                on='Codigo', 
                                how='left'
                            )
                            
                            # Calcular valor total
                            df_filtrado['Valor_Total'] = df_filtrado['Qtd_Entregue'].astype(float) * df_filtrado['Valor'].astype(float)
                            
                            # Agrupar por produto
                            df_resumo = df_filtrado.groupby(['Codigo', 'SKU', 'Descricao']).agg({
                                'Qtd_Entregue': 'sum',
                                'Valor_Total': 'sum'
                            }).reset_index()
                            
                            st.success(f"✅ Relatório gerado para {fornecedor_fech}")
                            
                            # Métricas
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Total de Itens", len(df_resumo))
                            with col_b:
                                st.metric("Quantidade Total", int(df_resumo['Qtd_Entregue'].sum()))
                            with col_c:
                                st.metric("Valor Total", f"R$ {df_resumo['Valor_Total'].sum():,.2f}")
                            
                            st.markdown("---")
                            st.subheader("Itens para Faturamento")
                            st.dataframe(df_resumo, use_container_width=True)
                            
                            # Salvar fechamento
                            try:
                                worksheet_fech = spreadsheet.worksheet("Fechamentos")
                                periodo = f"{data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}"
                                
                                for _, row in df_resumo.iterrows():
                                    row_data = [
                                        periodo,
                                        fornecedor_fech,
                                        data_inicial.strftime('%d/%m/%Y'),
                                        data_final.strftime('%d/%m/%Y'),
                                        "",  # Num_Orcamento
                                        row['Codigo'],
                                        row['SKU'],
                                        row['Descricao'],
                                        row['Qtd_Entregue'],
                                        row['Valor_Total']
                                    ]
                                    worksheet_fech.append_row(row_data)
                                
                                st.success("✅ Fechamento salvo com sucesso!")
                            except Exception as e:
                                st.warning(f"Relatório gerado mas não foi possível salvar: {e}")
                            
                            # Download
                            csv = df_resumo.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Baixar Relatório para PO",
                                data=csv,
                                file_name=f"fechamento_{fornecedor_fech}_{data_inicial.strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning(f"Nenhuma entrada encontrada para {fornecedor_fech} no período selecionado.")
                    else:
                        st.info("Nenhuma entrada registrada ainda.")
                except Exception as e:
                    st.error(f"Erro ao gerar fechamento: {e}")

def pagina_estoque(spreadsheet):
    st.header("📦 Estoque")
    
    # Filtros
    with st.expander("🔎 Filtros", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtro_est_codigo = st.text_input("Código")
            filtro_est_desc = st.text_input("Descrição")
        
        with col2:
            filtro_est_grupo = st.text_input("Grupo")
            filtro_est_endereco = st.text_input("Endereço")
        
        with col3:
            filtro_est_ref = st.text_input("Referência")
        
        with col4:
            mostrar_criticos = st.checkbox("Apenas Estoque Crítico")
    
    # Buscar produtos
    filtros_estoque = {}
    if filtro_est_codigo:
        filtros_estoque['Codigo'] = filtro_est_codigo
    if filtro_est_desc:
        filtros_estoque['Descricao'] = filtro_est_desc
    if filtro_est_grupo:
        filtros_estoque['Grupo'] = filtro_est_grupo
    if filtro_est_endereco:
        filtros_estoque['Endereco'] = filtro_est_endereco
    if filtro_est_ref:
        filtros_estoque['Referencia'] = filtro_est_ref
    
    df_estoque = buscar_produtos(spreadsheet, filtros_estoque)
    
    if not df_estoque.empty:
        # Adicionar Curva ABC (simplificada)
        df_estoque['Valor_Estoque'] = df_estoque['Estoque_Atual'].astype(float) * df_estoque['Valor'].astype(float)
        df_estoque = df_estoque.sort_values('Valor_Estoque', ascending=False)
        
        total_valor = df_estoque['Valor_Estoque'].sum()
        df_estoque['Percentual_Acumulado'] = (df_estoque['Valor_Estoque'].cumsum() / total_valor * 100)
        
        def classificar_abc(percentual):
            if percentual <= 80:
                return 'A'
            elif percentual <= 95:
                return 'B'
            else:
                return 'C'
        
        df_estoque['Curva_ABC'] = df_estoque['Percentual_Acumulado'].apply(classificar_abc)
        
        # Calcular necessidade
        df_estoque['Necessidade'] = df_estoque.apply(
            lambda row: max(0, float(row['Estoque_Minimo']) - float(row['Estoque_Atual'])),
            axis=1
        )
        
        # Filtrar críticos se solicitado
        if mostrar_criticos:
            df_estoque = df_estoque[df_estoque['Estoque_Atual'].astype(float) <= df_estoque['Estoque_Minimo'].astype(float)]
        
        # Exibir resumo
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Itens", len(df_estoque))
        with col2:
            curva_a = len(df_estoque[df_estoque['Curva_ABC'] == 'A'])
            st.metric("Itens Curva A", curva_a)
        with col3:
            criticos = len(df_estoque[df_estoque['Estoque_Atual'].astype(float) <= df_estoque['Estoque_Minimo'].astype(float)])
            st.metric("Itens Críticos", criticos)
        with col4:
            st.metric("Valor Total", f"R$ {df_estoque['Valor_Estoque'].sum():,.2f}")
        
        st.markdown("---")
        
        # Exibir tabela
        colunas_exibir = ['Codigo', 'Descricao', 'Estoque_Atual', 'Estoque_Minimo', 
                         'Endereco', 'Curva_ABC', 'Necessidade', 'Grupo', 'Valor']
        
        st.dataframe(
            df_estoque[colunas_exibir],
            use_container_width=True,
            column_config={
                "Valor": st.column_config.NumberColumn(
                    "Valor (R$)",
                    format="R$ %.2f"
                ),
                "Curva_ABC": st.column_config.TextColumn(
                    "Curva ABC",
                )
            }
        )
        
        # Gráfico de distribuição ABC
        st.markdown("---")
        st.subheader("📊 Análise Curva ABC")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            distribuicao_abc = df_estoque['Curva_ABC'].value_counts().sort_index()
            st.bar_chart(distribuicao_abc)
        
        with col_b:
            st.markdown("**Classificação ABC:**")
            st.markdown("- **A**: 80% do valor do estoque")
            st.markdown("- **B**: 15% do valor do estoque")
            st.markdown("- **C**: 5% do valor do estoque")
        
        # Exportar
        csv = df_estoque.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Estoque",
            data=csv,
            file_name=f"estoque_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum produto encontrado com os filtros aplicados.")

if __name__ == "__main__":
    main()
