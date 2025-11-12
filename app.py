import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from fpdf import FPDF
import tempfile
import os
import numpy as np
import requests
import base64
import io
import time
import json
from pathlib import Path

# Configuração inicial da página
def setup_page():
    st.set_page_config(
        page_title="PMOC - Plano de Manutenção, Operação e Controle - AKR Brands",
        page_icon="❄️",
        layout="wide"
    )

# Constantes
CONFIG_FILE = "pmoc_config.json"
REPO = "vilelarobson0971/pmoc"
FILE_PATH = "pmoc.csv"

# Funções para sincronização com GitHub
def get_github_file_url(repo, file_path):
    return f"https://api.github.com/repos/{repo}/contents/{file_path}"

def load_config():
    """Carrega as configurações do arquivo JSON"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.error(f"Erro ao carregar configurações: {str(e)}")
        return {}

def save_config(config):
    """Salva as configurações no arquivo JSON"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {str(e)}")
        return False

def load_from_github(repo, file_path, token=None):
    try:
        url = get_github_file_url(repo, file_path)
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        } if token else {}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        
        content = response.json().get("content", "")
        if not content:
            return None
            
        decoded_content = base64.b64decode(content).decode("utf-8")
        
        if not decoded_content.strip():
            return None
            
        return pd.read_csv(io.StringIO(decoded_content))
    except Exception as e:
        st.error(f"Erro ao carregar dados do GitHub: {str(e)}")
        return None

def save_to_github(repo, file_path, data, token=None):
    try:
        url = get_github_file_url(repo, file_path)
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        } if token else {}
        
        # Verifica se o arquivo já existe para obter o SHA
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha", "") if response.status_code == 200 else ""
        
        # Converte DataFrame para CSV
        csv_data = data.to_csv(index=False)
        encoded_content = base64.b64encode(csv_data.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Atualização PMOC - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": encoded_content,
            "sha": sha if sha else None
        }
        
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados no GitHub: {str(e)}")
        return False

# Inicialização dos dados
def init_data():
    if 'data' not in st.session_state:
        # Carrega configurações
        config = load_config()
        token = config.get('github_token', '')
        
        # Tenta carregar do GitHub se houver token
        if token:
            saved_data = load_from_github(REPO, FILE_PATH, token)
            if saved_data is not None:
                if 'Observações' not in saved_data.columns:
                    saved_data['Observações'] = ''
                st.session_state.data = saved_data
                return
        
        # Se não conseguir carregar do GitHub, usa dados iniciais
        initial_data = {
            'TAG': list(range(1, 42)),
            'Local': ['Matriz']*20 + ['Filial']*13 + ['Matriz']*8,
            'Setor': ['Recepção', 'CPD', 'CPD', 'RH', 'Marketing', 'Marketing', 'Inteligência de mercado',
                     'Antigo Show Room', 'Diretoria - Rafael', 'Controladoria', 'Diretoria - Jair',
                     'Sala reunião térreo', 'Financeiro', 'Diretoria', 'Sala reunião principal',
                     'Sala reunião principal', 'Expedição - Recepção', 'Expedição - Sala Welder',
                     'Corte - Risco', 'Estoque - Sala Umberto', 'Laboratório - Sala ADM',
                     'Laboratório - Sala ADM', 'Gerência', 'Modelagem', 'Inteligência do Produto',
                     'Estilo', 'Show Room', 'T.I.', 'PCP', 'PCP', 'Compras', 'Refeitório', 'Refeitório',
                     'Refeitório', 'Sala de Reunião', 'Estúdio', 'Estúdio', 'Refeitório', 'Refeitório',
                     'Sala Expedição Kids', 'Ecommerce'],
            'Marca': ['Springer', 'Philco', 'Elgin', 'Springer', 'TCL', 'TCL', 'TCL', 'Springer',
                     'Springer', 'Springer', 'COMFEE', 'COMFEE', 'Springer', 'Springer', 'Springer',
                     'Springer', 'Philco', 'Agratto', 'COMFEE', 'GREE', 'GREE', 'GREE', 'GREE', 'GREE',
                     'GREE', 'GREE', 'GREE', 'Consul', 'Electrolux', 'GREE', 'Philco', 'GREE', 'GREE',
                     'GREE', 'GREE', 'Philco', 'Springer', 'Agratto', 'Agratto', '', ''],
            'Modelo': ['42MACA12S5', 'Eco Inverter', 'HWFL18B2IA', '42MACB18S5', 'TAC18CSA1', 'TAC18CSA1',
                      'TAC18CSA1', '42MACB18S5', '42AFFCL12', '42MACB18S5', '42AFCE12X5', '42AFCD18F5',
                      '42MACB18S5', '42TFCA', '42MACB18S5', '42MACB18S5', 'Eco Inverter', 'ACST12FR4-02',
                      '42AFCD12F5', 'GWC12QC-D3NNB4D/I', 'GWC18AAD-D3NNA1D/I', 'GWC18AAD-D3NNA1D/I',
                      'GWC12AAC-D3NNB4D/I', 'GWC12AAC-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I',
                      'GWC24QE-D3NNB4D/I', '', 'VI18F', 'GWC12QC-D3NNB4D/I', 'Eco Inverter',
                      'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I', 'GWC24QE-D3NNB4D/I',
                      '', '', 'LCS24F-02', 'LCS24F-02', '', ''],
            'BTU': [12000, 12000, 18000, 18000, 18000, 18000, 18000, 18000, 12000, 18000, 12000, 18000,
                   18000, 12000, 18000, 18000, 18000, 12000, 12000, 12000, 18000, 18000, 12000, 12000,
                   24000, 24000, 24000, 12000, 18000, 12000, 12000, 24000, 24000, 24000, 24000, 24000,
                   24000, 24000, 24000, 0, 12000],
            'Data Manutenção': ['']*41,
            'Técnico Executante': ['']*41,
            'Aprovação Supervisor': ['']*41,
            'Próxima manutenção': ['']*41,
            'Observações': ['']*41
        }
        st.session_state.data = pd.DataFrame(initial_data)
        st.session_state.data['BTU'] = st.session_state.data['BTU'].astype(str)

# Função para salvar dados
def save_data():
    try:
        # Carrega configurações
        config = load_config()
        token = config.get('github_token', '')
        
        if not token:
            st.error("Token de acesso ao GitHub não configurado. Configure na página de Configuração.")
            return False
        
        # Salva no GitHub
        if save_to_github(REPO, FILE_PATH, st.session_state.data, token):
            st.success("Dados salvos no GitHub com sucesso!")
            return True
        else:
            st.error("Falha ao salvar dados no GitHub.")
            return False
    except Exception as e:
        st.error(f"Erro ao salvar dados: {str(e)}")
        return False

# Página de Consulta
def show_consultation_page():
    st.header("Consulta de Aparelhos")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        local_filter = st.selectbox("Local", ["Todos"] + list(st.session_state.data['Local'].unique()))
    with col2:
        setor_filter = st.selectbox("Setor", ["Todos"] + list(st.session_state.data['Setor'].unique()))
    with col3:
        marca_filter = st.selectbox("Marca", ["Todos"] + list(st.session_state.data['Marca'].unique()))
    
    # Aplicar filtros
    filtered_data = st.session_state.data.copy()
    if local_filter != "Todos":
        filtered_data = filtered_data[filtered_data['Local'] == local_filter]
    if setor_filter != "Todos":
        filtered_data = filtered_data[filtered_data['Setor'] == setor_filter]
    if marca_filter != "Todos":
        filtered_data = filtered_data[filtered_data['Marca'] == marca_filter]
    
    # Calcular próxima manutenção para exibição
    display_data = filtered_data.copy()
    
    def calculate_next_maintenance(row):
        if row['Data Manutenção'] and str(row['Data Manutenção']) != '':
            try:
                maintenance_date = datetime.strptime(str(row['Data Manutenção']), '%d/%m/%Y')
                next_maintenance = maintenance_date + timedelta(days=180)
                return next_maintenance.strftime('%d/%m/%Y')
            except:
                return 'data inválida'
        return 'aguardando programação'
    
    display_data['Próxima manutenção (calculada)'] = display_data.apply(calculate_next_maintenance, axis=1)
    
    # Seção de Relatório PDF
    st.subheader("Gerar Relatório em PDF")
    selected_tags = st.multiselect(
        "Selecione os aparelhos para incluir no relatório (deixe vazio para todos)",
        options=filtered_data['TAG'].unique()
    )
    
    if st.button("Gerar Relatório PDF"):
        if selected_tags:
            report_data = filtered_data[filtered_data['TAG'].isin(selected_tags)]
            title = f"Relatório de Aparelhos Selecionados ({len(report_data)} itens)"
        else:
            report_data = filtered_data
            title = f"Relatório Completo de Aparelhos ({len(report_data)} itens)"
        
        pdf_file = generate_pdf_report(report_data, title)
        
        if pdf_file:
            with open(pdf_file, "rb") as f:
                pdf_bytes = f.read()
            
            st.download_button(
                label="Baixar Relatório PDF",
                data=pdf_bytes,
                file_name=f"relatorio_pmoc_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
            
            # Limpeza
            os.unlink(pdf_file)
    
    # Mostrar dados com a coluna calculada
    columns_to_show = [
        "TAG", "Local", "Setor", "Marca", "Modelo", 
        "BTU", "Data Manutenção", "Próxima manutenção (calculada)",
        "Técnico Executante", "Aprovação Supervisor", "Observações"
    ]
    
    st.dataframe(
        display_data[columns_to_show],
        use_container_width=True,
        hide_index=True,
        column_config={
            "TAG": "TAG",
            "Local": "Local",
            "Setor": "Setor",
            "Marca": "Marca",
            "Modelo": "Modelo",
            "BTU": "BTU",
            "Data Manutenção": st.column_config.TextColumn(
                "Data Manutenção",
                help="Data da última manutenção"
            ),
            "Próxima manutenção (calculada)": st.column_config.Column(
                "Próxima Manutenção",
                help="Calculada automaticamente como Data Manutenção + 180 dias"
            ),
            "Técnico Executante": "Técnico",
            "Aprovação Supervisor": "Aprovação",
            "Observações": "Observações"
        }
    )
    
    # Botão de exportação
    st.download_button(
        label="Exportar para CSV",
        data=st.session_state.data.to_csv(index=False).encode('utf-8'),
        file_name='pmoc_export.csv',
        mime='text/csv'
    )
    
    # Estatísticas
    st.subheader("Estatísticas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Aparelhos", len(filtered_data))
    with col2:
        with_maintenance = len(filtered_data[filtered_data['Data Manutenção'] != ''])
        st.metric("Com manutenção registrada", with_maintenance)
    with col3:
        try:
            overdue_count = 0
            for _, row in display_data.iterrows():
                if row['Próxima manutenção (calculada)'] not in ['aguardando programação', 'data inválida']:
                    try:
                        next_date = datetime.strptime(row['Próxima manutenção (calculada)'], '%d/%m/%Y')
                        if next_date < datetime.now():
                            overdue_count += 1
                    except:
                        pass
            st.metric("Manutenções Atrasadas", overdue_count, delta=f"-{overdue_count}" if overdue_count > 0 else None)
        except Exception as e:
            st.error(f"Erro ao calcular atrasos: {str(e)}")
            st.metric("Manutenções Atrasadas", 0)
    
    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.text("Desenvolvido por Robson Vilela")
    st.sidebar.text("Versão 1.0")
    st.sidebar.text("2025")

# Gerar relatório PDF
def generate_pdf_report(data, title="Relatório de Aparelhos"):
    try:
        pdf = FPDF(orientation='L')
        pdf.add_page()
        
        # Configuração de fonte e cores
        pdf.set_font("Arial", size=9)
        pdf.set_text_color(0, 0, 0)
        
        # Ajuste do fuso horário
        tz = pytz.timezone('America/Sao_Paulo')
        now = datetime.now(tz)
        
        # Cabeçalho
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "PMOC - Plano de Manutenção, Operação e Controle - AKR Brands", 0, 1, 'C')
        pdf.ln(5)
        
        # Título do relatório
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, title, 0, 1, 'C')
        pdf.ln(5)
        
        # Data e hora
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(0, 10, f"Gerado em: {now.strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        pdf.ln(8)
        
        # Configuração das colunas
        col_widths = [12, 20, 30, 20, 25, 12, 25, 25, 25, 25, 40]
        headers = [
            "TAG", "Local", "Setor", "Marca", "Modelo", 
            "BTU", "Última Manut.", "Próx. Manut.", 
            "Técnico", "Aprovação", "Observações"
        ]
        
        # Cabeçalho da tabela
        pdf.set_font("Arial", 'B', 8)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
        pdf.ln()
        
        # Conteúdo da tabela
        pdf.set_font("Arial", size=7)
        for _, row in data.iterrows():
            cells = [
                str(row['TAG'])[:10] if pd.notna(row['TAG']) else '',
                str(row['Local'])[:18] if pd.notna(row['Local']) else '',
                str(row['Setor'])[:25] if pd.notna(row['Setor']) else '',
                str(row['Marca'])[:18] if pd.notna(row['Marca']) else '',
                str(row['Modelo'])[:22] if pd.notna(row['Modelo']) else '',
                str(row['BTU'])[:10] if pd.notna(row['BTU']) else '',
                str(row['Data Manutenção'])[:10] if pd.notna(row['Data Manutenção']) and str(row['Data Manutenção']) != '' else 'N/A',
                str(row['Próxima manutenção'])[:10] if pd.notna(row['Próxima manutenção']) and str(row['Próxima manutenção']) != '' else 'N/A',
                str(row['Técnico Executante'])[:22] if pd.notna(row['Técnico Executante']) else '',
                str(row['Aprovação Supervisor'])[:22] if pd.notna(row['Aprovação Supervisor']) else '',
                str(row['Observações'])[:60] if pd.notna(row['Observações']) and str(row['Observações']) != '' else 'Nenhuma'
            ]
            
            for i, cell in enumerate(cells):
                pdf.cell(col_widths[i], 6, cell, 1, 0, 'C' if i in [0, 5, 6, 7] else 'L')
            pdf.ln()
        
        # Estatísticas
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Estatísticas:", 0, 1)
        pdf.set_font("Arial", size=10)
        
        total = len(data)
        pdf.cell(0, 10, f"Total de Aparelhos: {total}", 0, 1)
        
        try:
            next_maintenance = len(data[(data['Próxima manutenção'].notna()) & (data['Próxima manutenção'] != '')])
            pdf.cell(0, 10, f"Com próxima manutenção agendada: {next_maintenance}", 0, 1)
            
            overdue_count = 0
            for _, row in data.iterrows():
                if pd.notna(row['Próxima manutenção']) and str(row['Próxima manutenção']) != '':
                    try:
                        next_date = datetime.strptime(str(row['Próxima manutenção']), '%d/%m/%Y')
                        if next_date < datetime.now():
                            overdue_count += 1
                    except:
                        pass
            
            pdf.cell(0, 10, f"Manutenções atrasadas: {overdue_count}", 0, 1)
        except Exception as e:
            pdf.cell(0, 10, f"Erro ao calcular estatísticas: {str(e)[:50]}", 0, 1)
        
        # Rodapé
        pdf.ln(15)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, "Sistema PMOC - AKR Brands", 0, 0, 'C')
        
        # Gera o arquivo PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_file.name)
        
        return temp_file.name
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")
        return None

# Página de Adicionar Aparelho
def show_add_device_page():
    st.header("Adicionar Novo Aparelho")
    
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            tag = st.number_input("TAG*", min_value=1, step=1)
            local = st.selectbox("Local*", ["Matriz", "Filial"])
            setor = st.text_input("Setor*")
            marca = st.text_input("Marca*")
        with col2:
            modelo = st.text_input("Modelo")
            btu = st.number_input("BTU*", min_value=0, step=1000)
        
        st.markdown("(*) Campos obrigatórios")
        submit_button = st.form_submit_button("Adicionar Aparelho")
        
        if submit_button:
            if tag in st.session_state.data['TAG'].values:
                st.error("Já existe um aparelho com esta TAG!")
            elif not tag or not local or not setor or not marca or not btu:
                st.error("Preencha todos os campos obrigatórios!")
            else:
                new_row = {
                    'TAG': tag,
                    'Local': local,
                    'Setor': setor,
                    'Marca': marca,
                    'Modelo': modelo,
                    'BTU': btu,
                    'Data Manutenção': '',
                    'Técnico Executante': '',
                    'Aprovação Supervisor': '',
                    'Próxima manutenção': '',
                    'Observações': ''
                }
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                if save_data():
                    st.success("Aparelho adicionado com sucesso!")
                st.rerun()

# Página de Editar Aparelho
def show_edit_device_page():
    st.header("Editar Aparelho Existente")
    
    tag_to_edit = st.selectbox(
        "Selecione a TAG do aparelho a editar",
        st.session_state.data['TAG'].unique()
    )
    
    if tag_to_edit:
        aparelho_data = st.session_state.data[st.session_state.data['TAG'] == tag_to_edit].iloc[0]
        
        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                tag = st.number_input("TAG*", value=int(aparelho_data['TAG']), min_value=1, step=1)
                local = st.selectbox(
                    "Local*", 
                    ["Matriz", "Filial"], 
                    index=0 if aparelho_data['Local'] == "Matriz" else 1
                )
                setor = st.text_input("Setor*", value=aparelho_data['Setor'])
                marca = st.text_input("Marca*", value=aparelho_data['Marca'])
            with col2:
                modelo = st.text_input("Modelo", value=aparelho_data['Modelo'])
                btu = st.number_input("BTU*", value=int(aparelho_data['BTU']), min_value=0, step=1000)
            
            st.markdown("(*) Campos obrigatórios")
            submit_button = st.form_submit_button("Atualizar Aparelho")
            
            if submit_button:
                if not tag or not local or not setor or not marca or not btu:
                    st.error("Preencha todos os campos obrigatórios!")
                else:
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'TAG'] = tag
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Local'] = local
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Setor'] = setor
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Marca'] = marca
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'Modelo'] = modelo
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_edit, 'BTU'] = btu
                    
                    if save_data():
                        st.success("Aparelho atualizado com sucesso!")
                    st.rerun()

# Página de Remover Aparelho
def show_remove_device_page():
    st.header("Remover Aparelho")
    
    tag_to_remove = st.selectbox(
        "Selecione a TAG do aparelho a remover",
        st.session_state.data['TAG'].unique()
    )
    
    if tag_to_remove:
        aparelho_data = st.session_state.data[st.session_state.data['TAG'] == tag_to_remove].iloc[0]
        
        st.warning(f"Você está prestes a remover o aparelho com TAG {tag_to_remove}:")
        st.write(f"Local: {aparelho_data['Local']}")
        st.write(f"Setor: {aparelho_data['Setor']}")
        st.write(f"Marca/Modelo: {aparelho_data['Marca']} {aparelho_data['Modelo']}")
        st.write(f"Observações: {aparelho_data['Observações']}")
        
        if st.button("Confirmar Remoção"):
            st.session_state.data = st.session_state.data[st.session_state.data['TAG'] != tag_to_remove]
            if save_data():
                st.success("Aparelho removido com sucesso!")
            st.rerun()

# Página de Realizar Manutenção
def show_maintenance_page():
    st.header("Registrar Manutenção")
    
    tag_to_maintain = st.selectbox(
        "Selecione a TAG do aparelho para registrar manutenção",
        st.session_state.data['TAG'].unique()
    )
    
    if tag_to_maintain:
        aparelho_data = st.session_state.data[st.session_state.data['TAG'] == tag_to_maintain].iloc[0]
        
        with st.form("maintenance_form"):
            st.write(f"**Aparelho selecionado:** TAG {tag_to_maintain} - {aparelho_data['Marca']} {aparelho_data['Modelo']}")
            st.write(f"**Localização:** {aparelho_data['Local']} - {aparelho_data['Setor']}")
            
            data_manutencao = st.date_input(
                "Data da Manutenção*",
                format="DD/MM/YYYY"
            )
            tecnico = st.text_input("Técnico Executante*", value=aparelho_data['Técnico Executante'])
            aprovacao = st.text_input("Aprovação Supervisor", value=aparelho_data['Aprovação Supervisor'])
            observacoes = st.text_area("Observações", value=aparelho_data['Observações'])
            
            if data_manutencao:
                proxima_manutencao = data_manutencao + timedelta(days=180)
                st.write(f"**Próxima manutenção será automaticamente agendada para:** {proxima_manutencao.strftime('%d/%m/%Y')}")
            else:
                st.write("**Próxima manutenção:** Não definida (insira uma data de manutenção)")
            
            st.markdown("(*) Campos obrigatórios")
            submit_button = st.form_submit_button("Registrar Manutenção")
            
            if submit_button:
                if not data_manutencao or not tecnico:
                    st.error("Preencha todos os campos obrigatórios!")
                else:
                    proxima_manutencao = data_manutencao + timedelta(days=180)
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Data Manutenção'] = data_manutencao.strftime('%d/%m/%Y')
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Técnico Executante'] = tecnico
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Aprovação Supervisor'] = aprovacao
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Próxima manutenção'] = proxima_manutencao.strftime('%d/%m/%Y')
                    st.session_state.data.loc[st.session_state.data['TAG'] == tag_to_maintain, 'Observações'] = observacoes
                    
                    if save_data():
                        st.toast(f"Manutenção para TAG {tag_to_maintain} registrada com sucesso!", icon="✅")
                        st.success(f"Próxima manutenção agendada para: {proxima_manutencao.strftime('%d/%m/%Y')}")
                    st.rerun()

# Configuração de acesso
def check_password():
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
    
    if not st.session_state.password_correct:
        password = st.text_input("Digite a senha de acesso:", type="password")
        if password == "king@2025":
            st.session_state.password_correct = True
            st.rerun()
        elif password != "":
            st.error("Senha incorreta!")
        return False
    return True

# Página de Configuração
def show_configuration_page():
    st.header("Configuração")
    
    if not check_password():
        st.stop()
    
    # Carrega configurações existentes
    config = load_config()
    
    # Configuração do Token do GitHub
    st.subheader("Configuração do GitHub")
    
    github_token = st.text_input(
        "Token de Acesso ao GitHub (obrigatório para sincronização)",
        type="password",
        value=config.get('github_token', ''),
        help="Obtenha em: GitHub > Settings > Developer Settings > Personal Access Tokens"
    )
    
    if st.button("Salvar Configurações"):
        config['github_token'] = github_token
        if save_config(config):
            st.success("Configurações salvas com sucesso!")
            # Tenta carregar os dados do GitHub após salvar o token
            if github_token:
                saved_data = load_from_github(REPO, FILE_PATH, github_token)
                if saved_data is not None:
                    if 'Observações' not in saved_data.columns:
                        saved_data['Observações'] = ''
                    st.session_state.data = saved_data
                    st.success("Dados carregados do GitHub com sucesso!")
    
    # Sincronização manual
    st.subheader("Sincronização Manual")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Carregar Dados do GitHub"):
            if github_token:
                saved_data = load_from_github(REPO, FILE_PATH, github_token)
                if saved_data is not None:
                    if 'Observações' not in saved_data.columns:
                        saved_data['Observações'] = ''
                    st.session_state.data = saved_data
                    st.success("Dados carregados do GitHub com sucesso!")
            else:
                st.error("Token de acesso não configurado!")
    
    with col2:
        if st.button("Salvar Dados no GitHub"):
            if github_token:
                if save_data():
                    st.success("Dados salvos no GitHub com sucesso!")
            else:
                st.error("Token de acesso não configurado!")
    
    # Menu de configuração
    config_option = st.sidebar.radio(
        "Opções de Configuração",
        ["Adicionar Aparelho", "Editar Aparelho", "Remover Aparelho", "Realizar Manutenção"]
    )
    
    if config_option == "Adicionar Aparelho":
        show_add_device_page()
    elif config_option == "Editar Aparelho":
        show_edit_device_page()
    elif config_option == "Remover Aparelho":
        show_remove_device_page()
    elif config_option == "Realizar Manutenção":
        show_maintenance_page()
    
    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.text("Desenvolvido por Robson Vilela")
    st.sidebar.text("Versão 1.0")
    st.sidebar.text("2025")

# Função principal
def main():
    try:
        setup_page()
        init_data()
        
        st.title("❄️ PMOC - Plano de Manutenção, Operação e Controle - AKR Brands")
        st.markdown("Controle de manutenção preventiva de aparelhos de ar condicionado")
        
        # Menu principal
        menu = st.sidebar.radio(
            "Menu Principal",
            ["Consulta", "Configuração"]
        )
        
        if menu == "Consulta":
            show_consultation_page()
        elif menu == "Configuração":
            show_configuration_page()
            
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {str(e)}")

if __name__ == "__main__":
    main()
