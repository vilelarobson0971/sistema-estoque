import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import requests
import os

# Configuração da página
st.set_page_config(
    page_title="Sistema de Compras e Estoque",
    page_icon="📦",
    layout="wide"
)

# Classe para gerenciar o banco de dados
class DatabaseManager:
    def __init__(self, csv_url):
        self.csv_url = csv_url
    
    def load_data(self):
        try:
            # Tenta carregar do GitHub
            df = pd.read_csv(self.csv_url)
            return df
        except:
            # Se não conseguir, cria estrutura vazia
            return self.create_empty_dataframe()
    
    def create_empty_dataframe(self):
        return pd.DataFrame({
            'codigo': [],
            'referencia': [],
            'sku': [],
            'ean': [],
            'marca': [],
            'grupo': [],
            'fornecedor': [],
            'valor_produto': [],
            'descricao': [],
            'descricao_complementar': [],
            'estoque_atual': [],
            'estoque_minimo': [],
            'endereco': [],
            'curva_abc': [],
            'data_cadastro': []
        })
    
    def save_data(self, df):
        # Em ambiente local, salva no diretório data/
        df.to_csv('data/produtos.csv', index=False)
        return True

# Inicialização do banco de dados
@st.cache_resource
def init_database():
    # URL do CSV no GitHub (substitua pela sua URL real)
    CSV_URL = "https://raw.githubusercontent.com/seu-usuario/seu-repo/main/data/produtos.csv"
    return DatabaseManager(CSV_URL)

db = init_database()

# Funções auxiliares
def calcular_necessidade_compra(estoque_atual, estoque_minimo):
    return max(0, estoque_minimo + 2 - estoque_atual)

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Sidebar para navegação
st.sidebar.title("📦 Sistema de Compras e Estoque")
st.sidebar.write("**Infralink - Shopping Catuaí Londrina**")

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

# Carrega os dados
df_produtos = db.load_data()

# Página: Cadastro de Produto
if menu == "Cadastro de Produto":
    st.title("📝 Cadastro de Produto")
    
    with st.form("cadastro_produto"):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.number_input("Código do Produto*", min_value=0, step=1)
            referencia = st.text_input("Referência*")
            sku = st.text_input("SKU*")
            ean = st.text_input("EAN")
            marca = st.text_input("Marca*")
            grupo = st.selectbox("Grupo*", ["HIDRAULICA", "ELETRICA", "PINTURA", "OUTROS"])
            
        with col2:
            fornecedor = st.text_input("Fornecedor*")
            valor_produto = st.number_input("Valor do Produto*", min_value=0.0, format="%.2f")
            descricao = st.text_area("Descrição do Produto*")
            descricao_complementar = st.text_area("Descrição Complementar")
            estoque_atual = st.number_input("Estoque Atual*", min_value=0, step=1)
            estoque_minimo = st.number_input("Estoque Mínimo*", min_value=0, step=1)
            endereco = st.text_input("Endereço (Ex: RUA B BOX 5 SEQ 2)")
            curva_abc = st.selectbox("Curva ABC", ["A", "B", "C"])
        
        submitted = st.form_submit_button("Cadastrar Produto")
        
        if submitted:
            if all([codigo, referencia, sku, marca, grupo, fornecedor, valor_produto, descricao]):
                novo_produto = {
                    'codigo': codigo,
                    'referencia': referencia,
                    'sku': sku,
                    'ean': ean,
                    'marca': marca,
                    'grupo': grupo,
                    'fornecedor': fornecedor,
                    'valor_produto': valor_produto,
                    'descricao': descricao,
                    'descricao_complementar': descricao_complementar,
                    'estoque_atual': estoque_atual,
                    'estoque_minimo': estoque_minimo,
                    'endereco': endereco,
                    'curva_abc': curva_abc,
                    'data_cadastro': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Adiciona ao DataFrame
                df_novo = pd.DataFrame([novo_produto])
                df_produtos = pd.concat([df_produtos, df_novo], ignore_index=True)
                
                # Salva os dados
                if db.save_data(df_produtos):
                    st.success("Produto cadastrado com sucesso!")
                else:
                    st.error("Erro ao salvar o produto.")
            else:
                st.error("Preencha todos os campos obrigatórios (*)")

# Página: Busca de Produto
elif menu == "Busca de Produto":
    st.title("🔍 Campo de Busca de Produto")
    
    with st.expander("Filtros de Busca"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_codigo = st.text_input("Código do Produto")
            filtro_referencia = st.text_input("Referência")
            filtro_endereco = st.text_input("Endereço")
        
        with col2:
            filtro_descricao = st.text_input("Descrição do Produto")
            filtro_marca = st.text_input("Marca")
            filtro_grupo = st.selectbox("Grupo", ["", "HIDRAULICA", "ELETRICA", "PINTURA", "OUTROS"])
        
        with col3:
            filtro_fornecedor = st.text_input("Fornecedor")
            valor_min = st.number_input("Valor Mínimo", min_value=0.0, format="%.2f")
            valor_max = st.number_input("Valor Máximo", min_value=0.0, format="%.2f")
    
    # Aplica filtros
    df_filtrado = df_produtos.copy()
    
    if filtro_codigo:
        df_filtrado = df_filtrado[df_filtrado['codigo'].astype(str).str.contains(filtro_codigo, na=False)]
    if filtro_referencia:
        df_filtrado = df_filtrado[df_filtrado['referencia'].str.contains(filtro_referencia, na=False)]
    if filtro_endereco:
        df_filtrado = df_filtrado[df_filtrado['endereco'].str.contains(filtro_endereco, na=False)]
    if filtro_descricao:
        df_filtrado = df_filtrado[df_filtrado['descricao'].str.contains(filtro_descricao, na=False)]
    if filtro_marca:
        df_filtrado = df_filtrado[df_filtrado['marca'].str.contains(filtro_marca, na=False)]
    if filtro_grupo:
        df_filtrado = df_filtrado[df_filtrado['grupo'] == filtro_grupo]
    if filtro_fornecedor:
        df_filtrado = df_filtrado[df_filtrado['fornecedor'].str.contains(filtro_fornecedor, na=False)]
    if valor_min > 0:
        df_filtrado = df_filtrado[df_filtrado['valor_produto'] >= valor_min]
    if valor_max > 0:
        df_filtrado = df_filtrado[df_filtrado['valor_produto'] <= valor_max]
    
    # Exibe resultados
    st.subheader("Resultados da Busca")
    
    if not df_filtrado.empty:
        # Formata a exibição
        df_display = df_filtrado[['codigo', 'descricao', 'marca', 'referencia', 'endereco', 
                                'estoque_atual', 'valor_produto']].copy()
        df_display['valor_produto'] = df_display['valor_produto'].apply(formatar_moeda)
        
        st.dataframe(df_display, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Itens", len(df_filtrado))
        with col2:
            st.metric("Valor Total em Estoque", 
                     formatar_moeda((df_filtrado['estoque_atual'] * df_filtrado['valor_produto']).sum()))
        with col3:
            itens_risco = len(df_filtrado[df_filtrado['estoque_atual'] <= df_filtrado['estoque_minimo']])
            st.metric("Itens em Risco", itens_risco)
    else:
        st.info("Nenhum produto encontrado com os filtros aplicados.")

# Página: Necessidade de Compra
elif menu == "Necessidade de Compra":
    st.title("🛒 Necessidade de Compra")
    
    with st.expander("Filtros"):
        col1, col2 = st.columns(2)
        with col1:
            filtro_fornecedor_nc = st.selectbox("Fornecedor", 
                                              [""] + list(df_produtos['fornecedor'].unique()))
        with col2:
            filtro_grupo_nc = st.selectbox("Grupo", 
                                         [""] + list(df_produtos['grupo'].unique()))
    
    # Calcula necessidade de compra
    df_necessidade = df_produtos.copy()
    df_necessidade['necessidade'] = df_necessidade.apply(
        lambda x: calcular_necessidade_compra(x['estoque_atual'], x['estoque_minimo']), 
        axis=1
    )
    
    # Filtra itens com necessidade > 0
    df_necessidade = df_necessidade[df_necessidade['necessidade'] > 0]
    
    # Aplica filtros adicionais
    if filtro_fornecedor_nc:
        df_necessidade = df_necessidade[df_necessidade['fornecedor'] == filtro_fornecedor_nc]
    if filtro_grupo_nc:
        df_necessidade = df_necessidade[df_necessidade['grupo'] == filtro_grupo_nc]
    
    # Cabeçalho do relatório
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write("**Requisitante:** João Henrique")
    with col2:
        st.write("**Instituição:** OROPEIRO CÁLIOXI")
    with col3:
        st.write("**Data:**", datetime.now().strftime("%d/%m/%Y"))
    with col4:
        st.write("**Base:** Shopping Catuai Londrina")
    
    if not df_necessidade.empty:
        # Prepara dados para exibição
        df_display = df_necessidade[[
            'codigo', 'descricao', 'estoque_atual', 'estoque_minimo', 
            'necessidade', 'fornecedor', 'valor_produto'
        ]].copy()
        
        df_display['valor_total'] = df_display['necessidade'] * df_display['valor_produto']
        df_display['valor_produto'] = df_display['valor_produto'].apply(formatar_moeda)
        df_display['valor_total'] = df_display['valor_total'].apply(formatar_moeda)
        
        st.dataframe(df_display, use_container_width=True)
        
        # Totais
        total_necessidade = df_necessidade['necessidade'].sum()
        total_valor = (df_necessidade['necessidade'] * df_necessidade['valor_produto']).sum()
        
        st.success(f"**Total de Itens com Necessidade:** {total_necessidade} | "
                  f"**Valor Total Estimado:** {formatar_moeda(total_valor)}")
    else:
        st.info("Nenhum item com necessidade de compra no momento.")

# Página: Orçamento de Compra
elif menu == "Orçamento de Compra":
    st.title("💰 Orçamento de Compra")
    
    tab1, tab2 = st.tabs(["Criar Orçamento", "Consultar Orçamentos"])
    
    with tab1:
        st.subheader("Criar Novo Orçamento")
        
        busca_necessidade = st.radio("Buscar Necessidade:", ["Sim", "Não"], horizontal=True)
        
        if busca_necessidade == "Sim":
            # Busca automática dos itens com necessidade
            df_necessidade = df_produtos.copy()
            df_necessidade['necessidade'] = df_necessidade.apply(
                lambda x: calcular_necessidade_compra(x['estoque_atual'], x['estoque_minimo']), 
                axis=1
            )
            df_necessidade = df_necessidade[df_necessidade['necessidade'] > 0]
            
            if not df_necessidade.empty:
                st.write("Itens com necessidade de compra:")
                
                # Seleção de itens
                itens_selecionados = []
                for idx, row in df_necessidade.iterrows():
                    if st.checkbox(f"{row['codigo']} - {row['descricao']} | "
                                 f"Necessidade: {row['necessidade']} | "
                                 f"Fornecedor: {row['fornecedor']} | "
                                 f"Valor: {formatar_moeda(row['valor_produto'])}", 
                                 key=f"item_{idx}"):
                        itens_selecionados.append({
                            'codigo': row['codigo'],
                            'descricao': row['descricao'],
                            'quantidade': row['necessidade'],
                            'fornecedor': row['fornecedor'],
                            'valor_unitario': row['valor_produto']
                        })
                
                if itens_selecionados:
                    st.subheader("Resumo do Orçamento")
                    df_orcamento = pd.DataFrame(itens_selecionados)
                    df_orcamento['valor_total'] = df_orcamento['quantidade'] * df_orcamento['valor_unitario']
                    
                    st.dataframe(df_orcamento)
                    
                    total_orcamento = df_orcamento['valor_total'].sum()
                    st.write(f"**Valor Total do Orçamento:** {formatar_moeda(total_orcamento)}")
                    
                    motivo_compra = st.text_area("Motivo da Compra")
                    
                    if st.button("Gerar Orçamento"):
                        st.success("Orçamento gerado com sucesso!")
            else:
                st.info("Nenhum item com necessidade de compra.")
        
        else:
            st.info("Modo de busca manual - em desenvolvimento")
    
    with tab2:
        st.subheader("Consultar Orçamentos")
        st.info("Funcionalidade de consulta de orçamentos - em desenvolvimento")

# Página: Estoque
elif menu == "Estoque":
    st.title("📊 Estoque")
    
    with st.expander("Filtros"):
        col1, col2 = st.columns(2)
        
        with col1:
            filtro_codigo_est = st.text_input("Código do Produto", key="filtro_est_cod")
            filtro_referencia_est = st.text_input("Referência", key="filtro_est_ref")
            filtro_descricao_est = st.text_input("Descrição do Produto", key="filtro_est_desc")
        
        with col2:
            filtro_endereco_est = st.text_input("Endereço", key="filtro_est_end")
            filtro_grupo_est = st.selectbox("Grupo", [""] + list(df_produtos['grupo'].unique()), key="filtro_est_grp")
    
    # Aplica filtros
    df_estoque = df_produtos.copy()
    
    if filtro_codigo_est:
        df_estoque = df_estoque[df_estoque['codigo'].astype(str).str.contains(filtro_codigo_est, na=False)]
    if filtro_referencia_est:
        df_estoque = df_estoque[df_estoque['referencia'].str.contains(filtro_referencia_est, na=False)]
    if filtro_descricao_est:
        df_estoque = df_estoque[df_estoque['descricao'].str.contains(filtro_descricao_est, na=False)]
    if filtro_endereco_est:
        df_estoque = df_estoque[df_estoque['endereco'].str.contains(filtro_endereco_est, na=False)]
    if filtro_grupo_est:
        df_estoque = df_estoque[df_estoque['grupo'] == filtro_grupo_est]
    
    # Calcula necessidade
    df_estoque['necessidade'] = df_estoque.apply(
        lambda x: calcular_necessidade_compra(x['estoque_atual'], x['estoque_minimo']), 
        axis=1
    )
    
    # Prepara dados para exibição
    df_display = df_estoque[[
        'codigo', 'descricao', 'estoque_atual', 'estoque_minimo', 
        'necessidade', 'endereco', 'curva_abc', 'grupo'
    ]].copy()
    
    st.dataframe(df_display, use_container_width=True)
    
    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Itens", len(df_estoque))
    with col2:
        st.metric("Itens em Risco", len(df_estoque[df_estoque['necessidade'] > 0]))
    with col3:
        valor_total = (df_estoque['estoque_atual'] * df_estoque['valor_produto']).sum()
        st.metric("Valor Total Estoque", formatar_moeda(valor_total))
    with col4:
        st.metric("Diversidade de Grupos", df_estoque['grupo'].nunique())

# Páginas em desenvolvimento
elif menu == "Busca de Orçamentos":
    st.title("🔍 Busca de Orçamentos")
    st.info("Funcionalidade em desenvolvimento")
    
elif menu == "Entrada de Produto":
    st.title("📥 Entrada de Produto")
    st.info("Funcionalidade em desenvolvimento")
    
elif menu == "Relatório de Fechamento":
    st.title("📋 Relatório de Fechamento")
    st.info("Funcionalidade em desenvolvimento")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.info(
    "Idealizado por João Henrique\n\n"
    "Dev. Robson Vilela"
    "Versão 1.0 - 2025"
)


