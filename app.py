5. Compartilhe a planilha com o email da conta de serviço
""")
        return

    inicializar_planilhas(spreadsheet)

    # Menu lateral
    paginas = [
        "🏠 Home",
        "📝 Cadastro de Produto",
        "🔍 Busca de Produtos",
        "⚠️ Necessidade de Compra",
        "💰 Orçamento de Compra",
        "📥 Entrada de Produtos",
        "📊 Relatório de Fechamento",
        "📦 Estoque"
    ]
    menu = st.sidebar.selectbox("Menu Principal", paginas)

    # Aqui você deve chamar as funções de cada página conforme implementadas no seu app original.
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

# [Coloque aqui as funções pagina_home, pagina_cadastro_produto, pagina_busca_produtos etc. conforme no seu arquivo original.]

if __name__ == "__main__":
    main()
