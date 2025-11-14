def salvar_produtos(spreadsheet, df):
    worksheet = spreadsheet.worksheet('Produtos')
    import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Sistema de Compras e Estoque",
    page_icon="📦",
    layout="wide"
)

# Sistema de dados em memória (simples e eficiente)
if 'produtos' not in st.session_state:
    st.session_state.produtos = pd.DataFrame(columns=[
        'Codigo', 'Referencia', 'SKU', 'EAN', 'Marca', 'Grupo', 
        'Fornecedor', 'Valor', 'Descricao', 'Descricao_Complementar',
        'Estoque_Atual', 'Estoque_Minimo', 'Endereco', 'Curva_ABC'
    ])

if 'orcamentos' not in st.session_state:
    st.session_state.orcamentos = pd.DataFrame(columns=[
        'Numero_Orcamento', 'Fornecedor', 'Requisitante', 'Data_Solicitacao',
        'Codigo_Produto', 'Descricao_Produto', 'Quantidade', 'Valor_Unitario',
        'Valor_Total', 'Status', 'Motivo_Compra'
    ])

def main():
    st.title("📦 SISTEMA DE COMPRAS E ESTOQUE")
    st.markdown("---")
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu Principal",
        [
            "Cadastro de Produto", 
            "Busca de Produto", 
            "Necessidade de Compra",
            "Orçamento de Compra", 
            "Busca de Orçamentos",
            "Entrada de Produto",
            "Relatório de Fechamento",
            "Estoque"
        ]
    )
    
    if menu == "Cadastro de Produto":
        cadastro_produto()
    elif menu == "Busca de Produto":
        busca_produto()
    elif menu == "Necessidade de Compra":
        necessidade_compra()
    elif menu == "Orçamento de Compra":
        orcamento_compra()
    elif menu == "Busca de Orçamentos":
        busca_orcamentos()
    elif menu == "Entrada de Produto":
        entrada_produto()
    elif menu == "Relatório de Fechamento":
        relatorio_fechamento()
    elif menu == "Estoque":
        consulta_estoque()

def cadastro_produto():
    st.header("📝 CADASTRO DE PRODUTO")
    
    with st.form("cadastro_produto"):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.number_input("CÓDIGO DO PRODUTO", min_value=1, step=1, value=1)
            referencia = st.text_input("REFERÊNCIA", value="563242")
            sku = st.text_input("SKU", value="35645")
            ean = st.text_input("EAN", value="754512215632")
            marca = st.text_input("MARCA", value="TIGRE")
            grupo = st.selectbox("GRUPO", ["HIDRAULICA", "ELETRICA", "PINTURA", "OUTROS"])
        
        with col2:
            fornecedor = st.text_input("FORNECEDOR", value="PEROLA")
            valor = st.number_input("VALOR DO PRODUTO (R$)", min_value=0.0, format="%.2f", value=16.50)
            descricao = st.text_area("DESCRIÇÃO DO PRODUTO", value="REGISTRO ESFERA COMPACTO SOLDAVEL 60MM")
            descricao_complementar = st.text_area("DESCRIÇÃO COMPLEMENTAR", 
                                                value="MATERIAL DE PVC, BITOLA DE 60MM PRESSÃO MAXIMO DE 10KGF/CM² FUNÇÃO DE CONTROLA O FLUXO DO LIQUIDO QUE PASSA NA TUBULAÇÃO.")
            endereco = st.text_input("ENDEREÇO", value="RUA B BOX 5 SEQ 2")
        
        col3, col4, col5 = st.columns(3)
        with col3:
            estoque_atual = st.number_input("ESTOQUE ATUAL", min_value=0, step=1, value=1)
        with col4:
            estoque_minimo = st.number_input("ESTOQUE MÍNIMO", min_value=0, step=1, value=3)
        with col5:
            curva_abc = st.selectbox("CURVA ABC", ["A", "B", "C"])
        
        submitted = st.form_submit_button("CADASTRAR PRODUTO")
        
        if submitted:
            if codigo and descricao:
                novo_produto = {
                    'Codigo': int(codigo),
                    'Referencia': referencia,
                    'SKU': sku,
                    'EAN': ean,
                    'Marca': marca,
                    'Grupo': grupo,
                    'Fornecedor': fornecedor,
                    'Valor': valor,
                    'Descricao': descricao,
                    'Descricao_Complementar': descricao_complementar,
                    'Estoque_Atual': estoque_atual,
                    'Estoque_Minimo': estoque_minimo,
                    'Endereco': endereco,
                    'Curva_ABC': curva_abc
                }
                
                # Verificar se código já existe
                if not st.session_state.produtos.empty and codigo in st.session_state.produtos['Codigo'].values:
                    st.warning("Código de produto já existe!")
                else:
                    novo_df = pd.DataFrame([novo_produto])
                    st.session_state.produtos = pd.concat([st.session_state.produtos, novo_df], ignore_index=True)
                    st.success("✅ Produto cadastrado com sucesso!")
            else:
                st.error("Código e Descrição são obrigatórios!")
    
    # Lista de produtos cadastrados
    st.subheader("📋 Produtos Cadastrados")
    if not st.session_state.produtos.empty:
        st.dataframe(st.session_state.produtos, use_container_width=True)
        
        # Opções de excluir
        if not st.session_state.produtos.empty:
            codigo_excluir = st.selectbox("Selecionar produto para excluir", 
                                        st.session_state.produtos['Codigo'].unique())
            if st.button("EXCLUIR ITEM"):
                st.session_state.produtos = st.session_state.produtos[st.session_state.produtos['Codigo'] != codigo_excluir]
                st.success("✅ Produto excluído com sucesso!")
                st.rerun()
    else:
        st.info("📝 Nenhum produto cadastrado. Use o formulário acima para cadastrar o primeiro produto.")

def busca_produto():
    st.header("🔍 CAMPO DE BUSCA DE PRODUTO")
    
    if st.session_state.produtos.empty:
        st.info("📝 Nenhum produto cadastrado para busca.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        codigo_busca = st.number_input("CÓDIGO DO PRODUTO", min_value=0, step=1, key="busca_codigo")
        referencia_busca = st.text_input("REFERÊNCIA", key="busca_referencia")
        endereco_busca = st.text_input("ENDEREÇO", key="busca_endereco")
    
    with col2:
        descricao_busca = st.text_input("DESCRIÇÃO DO PRODUTO", key="busca_descricao")
        marca_busca = st.text_input("MARCA", key="busca_marca")
        valor_busca = st.number_input("VALOR DO PRODUTO", min_value=0.0, format="%.2f", key="busca_valor")
    
    with col3:
        grupo_busca = st.selectbox("GRUPO", ["TODOS"] + list(st.session_state.produtos['Grupo'].unique()))
        fornecedor_busca = st.text_input("FORNECEDOR", key="busca_fornecedor")
    
    if st.button("🔍 BUSCAR"):
        resultado = st.session_state.produtos.copy()
        
        if codigo_busca > 0:
            resultado = resultado[resultado['Codigo'] == codigo_busca]
        if referencia_busca:
            resultado = resultado[resultado['Referencia'].str.contains(referencia_busca, case=False, na=False)]
        if endereco_busca:
            resultado = resultado[resultado['Endereco'].str.contains(endereco_busca, case=False, na=False)]
        if descricao_busca:
            resultado = resultado[resultado['Descricao'].str.contains(descricao_busca, case=False, na=False)]
        if marca_busca:
            resultado = resultado[resultado['Marca'].str.contains(marca_busca, case=False, na=False)]
        if valor_busca > 0:
            resultado = resultado[resultado['Valor'] == valor_busca]
        if grupo_busca != "TODOS":
            resultado = resultado[resultado['Grupo'] == grupo_busca]
        if fornecedor_busca:
            resultado = resultado[resultado['Fornecedor'].str.contains(fornecedor_busca, case=False, na=False)]
        
        st.subheader("📊 Resultados da Busca")
        if not resultado.empty:
            st.dataframe(resultado[['Codigo', 'Descricao', 'Marca', 'Estoque_Atual', 'Valor', 'Endereco']], 
                        use_container_width=True)
        else:
            st.info("🔍 Nenhum produto encontrado com os filtros aplicados.")

def necessidade_compra():
    st.header("📊 NECESSIDADE DE COMPRA")
    
    if st.session_state.produtos.empty:
        st.info("📝 Nenhum produto cadastrado no sistema.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        fornecedor_filtro = st.selectbox(
            "FORNECEDOR", 
            ["TODOS"] + list(st.session_state.produtos['Fornecedor'].unique())
        )
    with col2:
        grupo_filtro = st.selectbox(
            "GRUPO", 
            ["TODOS"] + list(st.session_state.produtos['Grupo'].unique())
        )
    
    # Calcular necessidade de compra
    df_necessidade = st.session_state.produtos.copy()
    df_necessidade['Necessidade'] = df_necessidade.apply(
        lambda x: max(0, x['Estoque_Minimo'] - x['Estoque_Atual'] + 2), axis=1
    )
    df_necessidade = df_necessidade[df_necessidade['Necessidade'] > 0]
    
    # Aplicar filtros
    if fornecedor_filtro != "TODOS":
        df_necessidade = df_necessidade[df_necessidade['Fornecedor'] == fornecedor_filtro]
    if grupo_filtro != "TODOS":
        df_necessidade = df_necessidade[df_necessidade['Grupo'] == grupo_filtro]
    
    st.subheader("📋 Itens com Necessidade de Compra")
    
    if not df_necessidade.empty:
        # Adicionar valor total
        df_necessidade['VR_TOT'] = df_necessidade['Necessidade'] * df_necessidade['Valor']
        
        # Exibir tabela
        st.dataframe(
            df_necessidade[[
                'Codigo', 'Descricao', 'Estoque_Atual', 'Estoque_Minimo', 
                'Necessidade', 'Fornecedor', 'VR_TOT'
            ]].rename(columns={
                'Codigo': 'CÓDIGO',
                'Descricao': 'DESCRIÇÃO DO ITEM',
                'Estoque_Atual': 'ESTOQUE',
                'Estoque_Minimo': 'EST. MINI.',
                'Necessidade': 'NECESS.',
                'Fornecedor': 'FORNEC.',
                'VR_TOT': 'VR. TOT.'
            }),
            use_container_width=True
        )
        
        # Total geral
        total_geral = df_necessidade['VR_TOT'].sum()
        st.metric("💰 VALOR TOTAL DA NECESSIDADE", f"R$ {total_geral:,.2f}")
    else:
        st.success("✅ Nenhum item com necessidade de compra no momento!")

def orcamento_compra():
    st.header("💰 ORÇAMENTO DE COMPRA")
    
    tab1, tab2 = st.tabs(["Criar Orçamento", "Consultar Orçamentos"])
    
    with tab1:
        st.subheader("📝 Criar Novo Orçamento")
        
        if st.session_state.produtos.empty:
            st.info("📝 Nenhum produto cadastrado no sistema.")
            return
        
        busca_necessidade = st.radio("BUSCAR NECESSIDADE", ["SIM", "NÃO"], horizontal=True)
        
        if busca_necessidade == "SIM":
            # Buscar itens com necessidade
            df_necessidade = st.session_state.produtos.copy()
            df_necessidade['Necessidade'] = df_necessidade.apply(
                lambda x: max(0, x['Estoque_Minimo'] - x['Estoque_Atual'] + 2), axis=1
            )
            df_necessidade = df_necessidade[df_necessidade['Necessidade'] > 0]
            
            if not df_necessidade.empty:
                st.write("### Itens com necessidade de compra:")
                
                # Selecionar itens para orçamento
                itens_selecionados = []
                for idx, row in df_necessidade.iterrows():
                    if st.checkbox(f"**{row['Codigo']}** - {row['Descricao']} | Necessidade: {row['Necessidade']} | Fornecedor: {row['Fornecedor']} | Valor: R$ {row['Valor']:.2f}", 
                                 key=f"nec_{row['Codigo']}"):
                        itens_selecionados.append({
                            'codigo': row['Codigo'],
                            'descricao': row['Descricao'],
                            'quantidade': row['Necessidade'],
                            'valor_unitario': row['Valor'],
                            'fornecedor': row['Fornecedor']
                        })
                
                if itens_selecionados:
                    col1, col2 = st.columns(2)
                    with col1:
                        numero_orcamento = st.text_input("NÚMERO DO ORÇAMENTO", value="ORC001")
                        requisitante = st.text_input("REQUISITANTE", value="JOÃO HENRIQUE")
                    with col2:
                        fornecedor_principal = st.selectbox(
                            "FORNECEDOR PRINCIPAL",
                            list(set(item['fornecedor'] for item in itens_selecionados))
                        )
                        data_solicitacao = st.date_input("DATA DA SOLICITAÇÃO")
                    
                    if st.button("📄 GERAR ORÇAMENTO"):
                        if numero_orcamento:
                            # Salvar orçamento
                            novos_orcamentos = []
                            for item in itens_selecionados:
                                if item['fornecedor'] == fornecedor_principal:
                                    novo_orcamento = {
                                        'Numero_Orcamento': numero_orcamento,
                                        'Fornecedor': fornecedor_principal,
                                        'Requisitante': requisitante,
                                        'Data_Solicitacao': data_solicitacao.strftime("%d/%m/%Y"),
                                        'Codigo_Produto': item['codigo'],
                                        'Descricao_Produto': item['descricao'],
                                        'Quantidade': item['quantidade'],
                                        'Valor_Unitario': item['valor_unitario'],
                                        'Valor_Total': item['quantidade'] * item['valor_unitario'],
                                        'Status': 'PENDENTE',
                                        'Motivo_Compra': 'ITEM NECESSARIO PARA REPOSIÇÃO DE ESTOQUE'
                                    }
                                    novos_orcamentos.append(novo_orcamento)
                            
                            if novos_orcamentos:
                                df_novos = pd.DataFrame(novos_orcamentos)
                                st.session_state.orcamentos = pd.concat([st.session_state.orcamentos, df_novos], ignore_index=True)
                                st.success("✅ Orçamento gerado com sucesso!")
                                st.rerun()
                            else:
                                st.error("❌ Nenhum item selecionado para este fornecedor!")
                        else:
                            st.error("❌ Número do orçamento é obrigatório!")
                else:
                    st.info("📝 Selecione os itens para criar o orçamento")
            else:
                st.success("✅ Nenhum item com necessidade de compra encontrado!")
        
        else:
            st.info("🛠️ Modo manual de criação de orçamento em desenvolvimento")
    
    with tab2:
        st.subheader("📋 Orçamentos Existentes")
        if not st.session_state.orcamentos.empty:
            st.dataframe(st.session_state.orcamentos, use_container_width=True)
        else:
            st.info("📝 Nenhum orçamento cadastrado.")

def busca_orcamentos():
    st.header("🔍 BUSCA DE ORÇAMENTOS")
    
    if st.session_state.orcamentos.empty:
        st.info("📝 Nenhum orçamento cadastrado para busca.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        numero_busca = st.text_input("NÚMERO DO ORÇAMENTO")
        fornecedor_busca = st.selectbox(
            "FORNECEDOR",
            ["TODOS"] + list(st.session_state.orcamentos['Fornecedor'].unique())
        )
    with col2:
        status_busca = st.selectbox(
            "STATUS",
            ["TODOS"] + list(st.session_state.orcamentos['Status'].unique())
        )
    
    resultado = st.session_state.orcamentos.copy()
    
    if numero_busca:
        resultado = resultado[resultado['Numero_Orcamento'].str.contains(numero_busca, case=False, na=False)]
    if fornecedor_busca != "TODOS":
        resultado = resultado[resultado['Fornecedor'] == fornecedor_busca]
    if status_busca != "TODOS":
        resultado = resultado[resultado['Status'] == status_busca]
    
    st.dataframe(resultado, use_container_width=True)
    
    if st.button("🖨️ IMPRIMIR RELATÓRIO"):
        st.success("📄 Relatório gerado com sucesso! (Funcionalidade de impressão em desenvolvimento)")

def entrada_produto():
    st.header("📥 ENTRADA DE PRODUTO")
    
    if st.session_state.orcamentos.empty:
        st.info("📝 Nenhum orçamento cadastrado para entrada de produtos.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        numero_orcamento = st.selectbox(
            "N° DO ORÇAMENTO",
            [""] + list(st.session_state.orcamentos['Numero_Orcamento'].unique())
        )
    with col2:
        numero_romaneio = st.text_input("NÚMERO DO ROMANEIO", value="ROM001")
        data_recebimento = st.date_input("DATA DE RECEBIMENTO")
    
    if numero_orcamento:
        itens_orcamento = st.session_state.orcamentos[st.session_state.orcamentos['Numero_Orcamento'] == numero_orcamento]
        
        st.subheader("📋 Itens do Orçamento")
        for idx, item in itens_orcamento.iterrows():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"**{item['Codigo_Produto']} - {item['Descricao_Produto']}**")
            with col2:
                st.write(f"Quantidade: {item['Quantidade']}")
            with col3:
                status = st.selectbox(f"Status", ["PENDENTE", "PARCIAL", "FINALIZADO"], 
                                    key=f"status_{idx}")
    
    if st.button("✅ CONFIRMAR ENTRADA"):
        st.success("🎉 Entrada de produtos registrada com sucesso!")

def relatorio_fechamento():
    st.header("📋 RELATÓRIO DE FECHAMENTO")
    
    if st.session_state.orcamentos.empty:
        st.info("📝 Nenhum orçamento cadastrado para relatório.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        fornecedor_filtro = st.selectbox(
            "FORNECEDOR",
            ["TODOS"] + list(st.session_state.orcamentos['Fornecedor'].unique())
        )
    with col2:
        data_inicial = st.date_input("DATA INICIAL")
        data_final = st.date_input("DATA FINAL")
    
    if st.button("📊 GERAR RELATÓRIO"):
        resultado = st.session_state.orcamentos.copy()
        
        if fornecedor_filtro != "TODOS":
            resultado = resultado[resultado['Fornecedor'] == fornecedor_filtro]
        
        st.subheader("📈 Relatório de Fechamento")
        st.dataframe(
            resultado[[
                'Numero_Orcamento', 'Fornecedor', 'Codigo_Produto', 'Descricao_Produto',
                'Quantidade', 'Valor_Total', 'Status'
            ]].rename(columns={
                'Numero_Orcamento': 'ORÇAMENTO',
                'Fornecedor': 'FORNECEDOR',
                'Codigo_Produto': 'CÓDIGO',
                'Descricao_Produto': 'DESCRIÇÃO',
                'Quantidade': 'QUANTIDADE',
                'Valor_Total': 'VALOR TOTAL',
                'Status': 'STATUS'
            }),
            use_container_width=True
        )
        
        total = resultado['Valor_Total'].sum()
        quantidade_itens = resultado['Quantidade'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 VALOR TOTAL", f"R$ {total:,.2f}")
        with col2:
            st.metric("📦 TOTAL DE ITENS", quantidade_itens)

def consulta_estoque():
    st.header("📊 ESTOQUE")
    
    if st.session_state.produtos.empty:
        st.info("📝 Nenhum produto cadastrado no sistema.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        codigo_estoque = st.number_input("CÓDIGO DO PRODUTO", min_value=0, step=1, key="estoque_codigo")
        referencia_estoque = st.text_input("REFERÊNCIA", key="estoque_referencia")
    with col2:
        descricao_estoque = st.text_input("DESCRIÇÃO DO PRODUTO", key="estoque_descricao")
        grupo_estoque = st.selectbox(
            "GRUPO", 
            ["TODOS"] + list(st.session_state.produtos['Grupo'].unique()),
            key="estoque_grupo"
        )
    
    if st.button("🔍 CONSULTAR ESTOQUE"):
        resultado = st.session_state.produtos.copy()
        
        if codigo_estoque > 0:
            resultado = resultado[resultado['Codigo'] == codigo_estoque]
        if referencia_estoque:
            resultado = resultado[resultado['Referencia'].str.contains(referencia_estoque, case=False, na=False)]
        if descricao_estoque:
            resultado = resultado[resultado['Descricao'].str.contains(descricao_estoque, case=False, na=False)]
        if grupo_estoque != "TODOS":
            resultado = resultado[resultado['Grupo'] == grupo_estoque]
        
        st.subheader("📋 Situação do Estoque")
        if not resultado.empty:
            st.dataframe(
                resultado[[
                    'Codigo', 'Descricao', 'Estoque_Atual', 'Estoque_Minimo',
                    'Endereco', 'Curva_ABC', 'Grupo', 'Fornecedor'
                ]].rename(columns={
                    'Codigo': 'CÓDIGO',
                    'Descricao': 'DESCRIÇÃO DO ITEM',
                    'Estoque_Atual': 'EST. AT.',
                    'Estoque_Minimo': 'EST. MIN.',
                    'Endereco': 'ENDEREÇO',
                    'Curva_ABC': 'CURVA ABC',
                    'Grupo': 'GRUPO',
                    'Fornecedor': 'FORNECEDOR'
                }),
                use_container_width=True
            )
        else:
            st.info("🔍 Nenhum produto encontrado com os filtros aplicados.")

if __name__ == "__main__":
    main()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

# Funções para orçamentos
def carregar_orcamentos(spreadsheet):
    worksheet = spreadsheet.worksheet('Orcamentos')
    dados = worksheet.get_all_records()
    if not dados:
        colunas = [
            'Numero_Orcamento', 'Fornecedor', 'Requisitante', 'Data_Solicitacao',
            'Codigo_Produto', 'Descricao_Produto', 'Quantidade', 'Valor_Unitario',
            'Valor_Total', 'Status', 'Motivo_Compra'
        ]
        return pd.DataFrame(columns=colunas)
    return pd.DataFrame(dados)

def salvar_orcamentos(spreadsheet, df):
    worksheet = spreadsheet.worksheet('Orcamentos')
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

# Interface principal
def main():
    st.title("📦 SISTEMA DE COMPRAS E ESTOQUE")
    st.markdown("---")
    
    # Conectar ao Google Sheets
    client = conectar_google_sheets()
    if not client:
        st.error("Não foi possível conectar ao Google Sheets")
        return
    
    spreadsheet = inicializar_worksheets(client)
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu Principal",
        [
            "Cadastro de Produto", 
            "Busca de Produto", 
            "Necessidade de Compra",
            "Orçamento de Compra", 
            "Busca de Orçamentos",
            "Entrada de Produto",
            "Relatório de Fechamento",
            "Estoque"
        ]
    )
    
    # Carregar dados
    df_produtos = carregar_produtos(spreadsheet)
    df_orcamentos = carregar_orcamentos(spreadsheet)
    
    if menu == "Cadastro de Produto":
        cadastro_produto(df_produtos, spreadsheet)
    
    elif menu == "Busca de Produto":
        busca_produto(df_produtos)
    
    elif menu == "Necessidade de Compra":
        necessidade_compra(df_produtos)
    
    elif menu == "Orçamento de Compra":
        orcamento_compra(df_produtos, df_orcamentos, spreadsheet)
    
    elif menu == "Busca de Orçamentos":
        busca_orcamentos(df_orcamentos)
    
    elif menu == "Entrada de Produto":
        entrada_produto(df_orcamentos, spreadsheet)
    
    elif menu == "Relatório de Fechamento":
        relatorio_fechamento(df_orcamentos)
    
    elif menu == "Estoque":
        consulta_estoque(df_produtos)

# Módulo de Cadastro de Produto
def cadastro_produto(df_produtos, spreadsheet):
    st.header("📝 CADASTRO DE PRODUTO")
    
    with st.form("cadastro_produto"):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.number_input("CÓDIGO DO PRODUTO", min_value=0, step=1)
            referencia = st.text_input("REFERÊNCIA")
            sku = st.text_input("SKU")
            ean = st.text_input("EAN")
            marca = st.text_input("MARCA")
            grupo = st.selectbox("GRUPO", ["HIDRAULICA", "ELETRICA", "PINTURA", "OUTROS"])
        
        with col2:
            fornecedor = st.text_input("FORNECEDOR")
            valor = st.number_input("VALOR DO PRODUTO (R$)", min_value=0.0, format="%.2f")
            descricao = st.text_area("DESCRIÇÃO DO PRODUTO")
            descricao_complementar = st.text_area("DESCRIÇÃO COMPLEMENTAR")
            endereco = st.text_input("ENDEREÇO (Ex: RUA B BOX 5 SEQ 2)")
        
        col3, col4, col5 = st.columns(3)
        with col3:
            estoque_atual = st.number_input("ESTOQUE ATUAL", min_value=0, step=1)
        with col4:
            estoque_minimo = st.number_input("ESTOQUE MÍNIMO", min_value=0, step=1)
        with col5:
            curva_abc = st.selectbox("CURVA ABC", ["A", "B", "C"])
        
        submitted = st.form_submit_button("CADASTRAR PRODUTO")
        
        if submitted:
            if codigo and descricao:
                novo_produto = {
                    'Codigo': int(codigo),
                    'Referencia': referencia,
                    'SKU': sku,
                    'EAN': ean,
                    'Marca': marca,
                    'Grupo': grupo,
                    'Fornecedor': fornecedor,
                    'Valor': valor,
                    'Descricao': descricao,
                    'Descricao_Complementar': descricao_complementar,
                    'Estoque_Atual': estoque_atual,
                    'Estoque_Minimo': estoque_minimo,
                    'Endereco': endereco,
                    'Curva_ABC': curva_abc
                }
                
                # Verificar se código já existe
                if codigo in df_produtos['Codigo'].values:
                    st.warning("Código de produto já existe!")
                else:
                    df_produtos = pd.concat([df_produtos, pd.DataFrame([novo_produto])], ignore_index=True)
                    salvar_produtos(spreadsheet, df_produtos)
                    st.success("Produto cadastrado com sucesso!")
            else:
                st.error("Código e Descrição são obrigatórios!")
    
    # Lista de produtos cadastrados
    st.subheader("Produtos Cadastrados")
    if not df_produtos.empty:
        st.dataframe(df_produtos, use_container_width=True)
        
        # Opções de alterar/excluir
        col1, col2 = st.columns(2)
        with col1:
            codigo_alterar = st.selectbox("Selecionar produto para alterar", df_produtos['Codigo'].unique())
            if st.button("ALTERAR CADASTRO"):
                st.session_state.alterar_produto = codigo_alterar
                st.info("Funcionalidade de alteração em desenvolvimento")
        
        with col2:
            codigo_excluir = st.selectbox("Selecionar produto para excluir", df_produtos['Codigo'].unique())
            if st.button("EXCLUIR ITEM"):
                df_produtos = df_produtos[df_produtos['Codigo'] != codigo_excluir]
                salvar_produtos(spreadsheet, df_produtos)
                st.success("Produto excluído com sucesso!")
                st.rerun()

# Módulo de Busca de Produto
def busca_produto(df_produtos):
    st.header("🔍 CAMPO DE BUSCA DE PRODUTO")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        codigo_busca = st.number_input("CÓDIGO DO PRODUTO", min_value=0, step=1, key="busca_codigo")
        referencia_busca = st.text_input("REFERÊNCIA", key="busca_referencia")
        endereco_busca = st.text_input("ENDEREÇO", key="busca_endereco")
    
    with col2:
        descricao_busca = st.text_input("DESCRIÇÃO DO PRODUTO", key="busca_descricao")
        marca_busca = st.text_input("MARCA", key="busca_marca")
        valor_busca = st.number_input("VALOR DO PRODUTO", min_value=0.0, format="%.2f", key="busca_valor")
    
    with col3:
        grupo_busca = st.selectbox("GRUPO", ["TODOS"] + list(df_produtos['Grupo'].unique()) if not df_produtos.empty else ["TODOS"])
        fornecedor_busca = st.text_input("FORNECEDOR", key="busca_fornecedor")
    
    if st.button("BUSCAR"):
        resultado = df_produtos.copy()
        
        if codigo_busca > 0:
            resultado = resultado[resultado['Codigo'] == codigo_busca]
        if referencia_busca:
            resultado = resultado[resultado['Referencia'].str.contains(referencia_busca, case=False, na=False)]
        if endereco_busca:
            resultado = resultado[resultado['Endereco'].str.contains(endereco_busca, case=False, na=False)]
        if descricao_busca:
            resultado = resultado[resultado['Descricao'].str.contains(descricao_busca, case=False, na=False)]
        if marca_busca:
            resultado = resultado[resultado['Marca'].str.contains(marca_busca, case=False, na=False)]
        if valor_busca > 0:
            resultado = resultado[resultado['Valor'] == valor_busca]
        if grupo_busca != "TODOS":
            resultado = resultado[resultado['Grupo'] == grupo_busca]
        if fornecedor_busca:
            resultado = resultado[resultado['Fornecedor'].str.contains(fornecedor_busca, case=False, na=False)]
        
        st.subheader("Resultados da Busca")
        if not resultado.empty:
            st.dataframe(resultado[['Codigo', 'Descricao', 'Marca', 'Estoque_Atual', 'Valor']], use_container_width=True)
        else:
            st.info("Nenhum produto encontrado com os filtros aplicados.")

# Módulo de Necessidade de Compra
def necessidade_compra(df_produtos):
    st.header("📊 NECESSIDADE DE COMPRA")
    
    col1, col2 = st.columns(2)
    with col1:
        fornecedor_filtro = st.selectbox(
            "FORNECEDOR", 
            ["TODOS"] + list(df_produtos['Fornecedor'].unique()) if not df_produtos.empty else ["TODOS"]
        )
    with col2:
        grupo_filtro = st.selectbox(
            "GRUPO", 
            ["TODOS"] + list(df_produtos['Grupo'].unique()) if not df_produtos.empty else ["TODOS"]
        )
    
    # Calcular necessidade de compra
    if not df_produtos.empty:
        df_necessidade = df_produtos.copy()
        df_necessidade['Necessidade'] = df_necessidade.apply(
            lambda x: max(0, x['Estoque_Minimo'] - x['Estoque_Atual'] + 2), axis=1
        )
        df_necessidade = df_necessidade[df_necessidade['Necessidade'] > 0]
        
        # Aplicar filtros
        if fornecedor_filtro != "TODOS":
            df_necessidade = df_necessidade[df_necessidade['Fornecedor'] == fornecedor_filtro]
        if grupo_filtro != "TODOS":
            df_necessidade = df_necessidade[df_necessidade['Grupo'] == grupo_filtro]
        
        st.subheader("Itens com Necessidade de Compra")
        
        if not df_necessidade.empty:
            # Adicionar valor total
            df_necessidade['VR_TOT'] = df_necessidade['Necessidade'] * df_necessidade['Valor']
            
            # Exibir tabela
            st.dataframe(
                df_necessidade[[
                    'Codigo', 'Descricao', 'Estoque_Atual', 'Estoque_Minimo', 
                    'Necessidade', 'Fornecedor', 'VR_TOT'
                ]].rename(columns={
                    'Codigo': 'CÓDIGO',
                    'Descricao': 'DESCRIÇÃO DO ITEM',
                    'Estoque_Atual': 'ESTOQUE',
                    'Estoque_Minimo': 'EST. MINI.',
                    'Necessidade': 'NECESS.',
                    'Fornecedor': 'FORNEC.',
                    'VR_TOT': 'VR. TOT.'
                }),
                use_container_width=True
            )
            
            # Total geral
            total_geral = df_necessidade['VR_TOT'].sum()
            st.metric("VALOR TOTAL DA NECESSIDADE", f"R$ {total_geral:,.2f}")
        else:
            st.success("✅ Nenhum item com necessidade de compra no momento!")
    else:
        st.info("Nenhum produto cadastrado no sistema.")

# Módulo de Orçamento de Compra
def orcamento_compra(df_produtos, df_orcamentos, spreadsheet):
    st.header("💰 ORÇAMENTO DE COMPRA")
    
    tab1, tab2 = st.tabs(["Criar Orçamento", "Consultar Orçamentos"])
    
    with tab1:
        st.subheader("Criar Novo Orçamento")
        
        busca_necessidade = st.radio("BUSCAR NECESSIDADE", ["SIM", "NÃO"], horizontal=True)
        
        if busca_necessidade == "SIM":
            # Buscar itens com necessidade
            df_necessidade = df_produtos.copy()
            df_necessidade['Necessidade'] = df_necessidade.apply(
                lambda x: max(0, x['Estoque_Minimo'] - x['Estoque_Atual'] + 2), axis=1
            )
            df_necessidade = df_necessidade[df_necessidade['Necessidade'] > 0]
            
            if not df_necessidade.empty:
                st.write("Itens com necessidade de compra:")
                
                # Selecionar itens para orçamento
                itens_selecionados = []
                for idx, row in df_necessidade.iterrows():
                    if st.checkbox(f"{row['Codigo']} - {row['Descricao']} (Necessidade: {row['Necessidade']})", key=f"nec_{row['Codigo']}"):
                        itens_selecionados.append({
                            'codigo': row['Codigo'],
                            'descricao': row['Descricao'],
                            'quantidade': row['Necessidade'],
                            'valor_unitario': row['Valor'],
                            'fornecedor': row['Fornecedor']
                        })
                
                if itens_selecionados:
                    col1, col2 = st.columns(2)
                    with col1:
                        numero_orcamento = st.text_input("NÚMERO DO ORÇAMENTO")
                        requisitante = st.text_input("REQUISITANTE", value="JOÃO HENRIQUE")
                    with col2:
                        fornecedor_principal = st.selectbox(
                            "FORNECEDOR PRINCIPAL",
                            list(set(item['fornecedor'] for item in itens_selecionados))
                        )
                        data_solicitacao = st.date_input("DATA DA SOLICITAÇÃO")
                    
                    if st.button("GERAR ORÇAMENTO"):
                        if numero_orcamento:
                            # Salvar orçamento
                            novos_orcamentos = []
                            for item in itens_selecionados:
                                if item['fornecedor'] == fornecedor_principal:
                                    novo_orcamento = {
                                        'Numero_Orcamento': numero_orcamento,
                                        'Fornecedor': fornecedor_principal,
                                        'Requisitante': requisitante,
                                        'Data_Solicitacao': data_solicitacao.strftime("%d/%m/%Y"),
                                        'Codigo_Produto': item['codigo'],
                                        'Descricao_Produto': item['descricao'],
                                        'Quantidade': item['quantidade'],
                                        'Valor_Unitario': item['valor_unitario'],
                                        'Valor_Total': item['quantidade'] * item['valor_unitario'],
                                        'Status': 'PENDENTE',
                                        'Motivo_Compra': 'ITEM NECESSARIO PARA REPOSIÇÃO DE ESTOQUE'
                                    }
                                    novos_orcamentos.append(novo_orcamento)
                            
                            df_novos = pd.DataFrame(novos_orcamentos)
                            df_orcamentos = pd.concat([df_orcamentos, df_novos], ignore_index=True)
                            salvar_orcamentos(spreadsheet, df_orcamentos)
                            st.success("Orçamento gerado com sucesso!")
                        else:
                            st.error("Número do orçamento é obrigatório!")
            else:
                st.info("Nenhum item com necessidade de compra encontrado.")
        
        else:
            st.info("Modo manual de criação de orçamento em desenvolvimento")
    
    with tab2:
        st.subheader("Orçamentos Existentes")
        if not df_orcamentos.empty:
            st.dataframe(df_orcamentos, use_container_width=True)
        else:
            st.info("Nenhum orçamento cadastrado.")

# Módulo de Busca de Orçamentos
def busca_orcamentos(df_orcamentos):
    st.header("🔍 BUSCA DE ORÇAMENTOS")
    
    if not df_orcamentos.empty:
        col1, col2 = st.columns(2)
        with col1:
            numero_busca = st.text_input("NÚMERO DO ORÇAMENTO")
            fornecedor_busca = st.selectbox(
                "FORNECEDOR",
                ["TODOS"] + list(df_orcamentos['Fornecedor'].unique())
            )
        with col2:
            status_busca = st.selectbox(
                "STATUS",
                ["TODOS"] + list(df_orcamentos['Status'].unique())
            )
        
        resultado = df_orcamentos.copy()
        
        if numero_busca:
            resultado = resultado[resultado['Numero_Orcamento'].str.contains(numero_busca, case=False, na=False)]
        if fornecedor_busca != "TODOS":
            resultado = resultado[resultado['Fornecedor'] == fornecedor_busca]
        if status_busca != "TODOS":
            resultado = resultado[resultado['Status'] == status_busca]
        
        st.dataframe(resultado, use_container_width=True)
        
        # Botão imprimir
        if st.button("IMPRIMIR RELATÓRIO"):
            st.info("Funcionalidade de impressão em desenvolvimento")
    else:
        st.info("Nenhum orçamento cadastrado para busca.")

# Módulo de Entrada de Produto
def entrada_produto(df_orcamentos, spreadsheet):
    st.header("📥 ENTRADA DE PRODUTO")
    
    col1, col2 = st.columns(2)
    with col1:
        numero_orcamento = st.selectbox(
            "N° DO ORÇAMENTO",
            [""] + list(df_orcamentos['Numero_Orcamento'].unique()) if not df_orcamentos.empty else [""]
        )
        iniciar_sem_orcamento = st.checkbox("INICIAR SEM ORÇAMENTO")
    with col2:
        numero_romaneio = st.text_input("NÚMERO DO ROMANEIO")
        obs_entrega = st.text_area("OBSERVAÇÃO DA ENTREGA")
        data_recebimento = st.date_input("DATA DE RECEBIMENTO")
    
    if numero_orcamento and not iniciar_sem_orcamento:
        itens_orcamento = df_orcamentos[df_orcamentos['Numero_Orcamento'] == numero_orcamento]
        
        st.subheader("Itens do Orçamento")
        for idx, item in itens_orcamento.iterrows():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
            with col1:
                st.write(f"**{item['Codigo_Produto']} - {item['Descricao_Produto']}**")
            with col2:
                comprado = st.number_input(f"Comprado", value=int(item['Quantidade']), min_value=0, key=f"comp_{idx}")
            with col3:
                entregue = st.number_input(f"Entregue", value=0, min_value=0, max_value=comprado, key=f"ent_{idx}")
            with col4:
                status = "PARCIAL" if entregue < comprado else "FINALIZADO"
                st.text(f"Status: {status}")
                obs = st.text_input(f"Observação", key=f"obs_{idx}")
    
    if st.button("CONFIRMAR ENTRADA"):
        st.success("Entrada de produtos registrada com sucesso!")

# Módulo de Relatório de Fechamento
def relatorio_fechamento(df_orcamentos):
    st.header("📋 RELATÓRIO DE FECHAMENTO")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fornecedor_filtro = st.selectbox(
            "FORNECEDOR",
            ["TODOS"] + list(df_orcamentos['Fornecedor'].unique()) if not df_orcamentos.empty else ["TODOS"]
        )
    with col2:
        data_inicial = st.date_input("DATA INICIAL")
    with col3:
        data_fechamento = st.date_input("DATA DE FECHAMENTO")
    
    if st.button("GERAR RELATÓRIO"):
        if not df_orcamentos.empty:
            resultado = df_orcamentos.copy()
            
            if fornecedor_filtro != "TODOS":
                resultado = resultado[resultado['Fornecedor'] == fornecedor_filtro]
            
            st.subheader("Relatório de Fechamento")
            st.dataframe(
                resultado[[
                    'Numero_Orcamento', 'Codigo_Produto', 'Descricao_Produto',
                    'Quantidade', 'Valor_Total', 'Status'
                ]].rename(columns={
                    'Numero_Orcamento': 'ORÇAMENTO',
                    'Codigo_Produto': 'CÓDIGO',
                    'Descricao_Produto': 'DESCRIÇÃO',
                    'Quantidade': 'QUANTIDADE',
                    'Valor_Total': 'VALOR TOTAL',
                    'Status': 'STATUS'
                }),
                use_container_width=True
            )
            
            total = resultado['Valor_Total'].sum()
            st.metric("TOTAL DO PERÍODO", f"R$ {total:,.2f}")
        else:
            st.info("Nenhum dado disponível para o relatório.")

# Módulo de Consulta de Estoque
def consulta_estoque(df_produtos):
    st.header("📊 ESTOQUE")
    
    col1, col2 = st.columns(2)
    with col1:
        codigo_estoque = st.number_input("CÓDIGO DO PRODUTO", min_value=0, step=1, key="estoque_codigo")
        referencia_estoque = st.text_input("REFERÊNCIA", key="estoque_referencia")
    with col2:
        descricao_estoque = st.text_input("DESCRIÇÃO DO PRODUTO", key="estoque_descricao")
        endereco_estoque = st.text_input("ENDEREÇO", key="estoque_endereco")
        grupo_estoque = st.selectbox(
            "GRUPO", 
            ["TODOS"] + list(df_produtos['Grupo'].unique()) if not df_produtos.empty else ["TODOS"],
            key="estoque_grupo"
        )
    
    if st.button("CONSULTAR ESTOQUE"):
        resultado = df_produtos.copy()
        
        if codigo_estoque > 0:
            resultado = resultado[resultado['Codigo'] == codigo_estoque]
        if referencia_estoque:
            resultado = resultado[resultado['Referencia'].str.contains(referencia_estoque, case=False, na=False)]
        if descricao_estoque:
            resultado = resultado[resultado['Descricao'].str.contains(descricao_estoque, case=False, na=False)]
        if endereco_estoque:
            resultado = resultado[resultado['Endereco'].str.contains(endereco_estoque, case=False, na=False)]
        if grupo_estoque != "TODOS":
            resultado = resultado[resultado['Grupo'] == grupo_estoque]
        
        st.subheader("Situação do Estoque")
        if not resultado.empty:
            st.dataframe(
                resultado[[
                    'Codigo', 'Descricao', 'Estoque_Atual', 'Estoque_Minimo',
                    'Endereco', 'Curva_ABC', 'Grupo'
                ]].rename(columns={
                    'Codigo': 'CÓDIGO',
                    'Descricao': 'DESCRIÇÃO DO ITEM',
                    'Estoque_Atual': 'EST. AT.',
                    'Estoque_Minimo': 'EST. MIN.',
                    'Endereco': 'ENDEREÇO',
                    'Curva_ABC': 'CURVA ABC',
                    'Grupo': 'GRUPO'
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhum produto encontrado com os filtros aplicados.")

if __name__ == "__main__":
    main()


