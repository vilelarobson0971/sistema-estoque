import streamlit as st
import pandas as pd

# CONFIG PRIMEIRO
st.set_page_config(page_title="Sistema Estoque", layout="wide")

def main():
    st.title("📦 Sistema de Compras - TESTE")
    st.write("**Teste sem Google Sheets**")
    
    # Dados de exemplo
    dados_exemplo = {
        'Codigo': ['P001', 'P002', 'P003'],
        'Descricao': ['Produto A', 'Produto B', 'Produto C'],
        'Estoque_Atual': [10, 5, 15],
        'Estoque_Minimo': [5, 10, 8],
        'Fornecedor': ['Fornecedor 1', 'Fornecedor 2', 'Fornecedor 1']
    }
    
    df = pd.DataFrame(dados_exemplo)
    
    st.success("✅ Aplicação carregada com dados locais")
    
    # Menu simples
    opcao = st.sidebar.selectbox(
        "Menu:",
        ["Dashboard", "Produtos", "Necessidade Compra"]
    )
    
    if opcao == "Dashboard":
        st.header("📊 Dashboard")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Produtos", len(df))
        with col2:
            st.metric("Em Falta", len(df[df['Estoque_Atual'] < df['Estoque_Minimo']]))
        with col3:
            st.metric("Status", "✅ Online")
    
    elif opcao == "Produtos":
        st.header("📝 Produtos")
        st.dataframe(df)
    
    elif opcao == "Necessidade Compra":
        st.header("⚠️ Necessidade de Compra")
        necessidade = df[df['Estoque_Atual'] < df['Estoque_Minimo']]
        if not necessidade.empty:
            st.dataframe(necessidade)
        else:
            st.success("✅ Estoque adequado!")

if __name__ == "__main__":
    main()
