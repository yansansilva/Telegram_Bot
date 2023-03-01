import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd

@st.cache_data
def carregar_dados(up, modo):
	if modo == 'integralizar' or modo == 'HxQ':
		dados_df = pd.DataFrame()
		for data_file in up:
			try:
				df = pd.read_csv(data_file, sep=';', decimal=',')
			except:
				df = pd.read_excel(data_file)
			try:
				df[df.columns[0]] = df[df.columns[0]].astype('string')
				df[df.columns[1]] = df[df.columns[1]].astype('string')
				juntar = df[df.columns[0]] + ' ' + df[df.columns[1]]
				df.insert(0, 'TEMPO', pd.to_datetime(juntar, dayfirst=True), True)
				dados_df = dados_df.append(df.drop([df.columns[1], df.columns[2]], axis=1))
			except:
				df.insert(0, 'TEMPO', pd.to_datetime(df[df.columns[0]].astype('string'), dayfirst=True), True)
				dados_df = dados_df.append(df.drop([df.columns[1]], axis=1))

	elif modo == 'FDI' or modo == 'Energia':
		if up.type != "text/csv":
			dados_df = pd.read_excel(up, sheet_name=0, index_col=0)
		else:
			dados_df = pd.read_csv(up)

	return dados_df

@st.cache_data
def import_from_GoogleDrive():
	# Selecionar planilha
    inversores = gspread.authorize(Credentials.from_service_account_info(st.secrets["gcp_service_account"],scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive",],)).open('Dados_Simulacao').worksheet('Inversores')
    modulos = gspread.authorize(Credentials.from_service_account_info(st.secrets["gcp_service_account"],scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive",],)).open('Dados_Simulacao').worksheet('Modulos')
    ambiente = gspread.authorize(Credentials.from_service_account_info(st.secrets["gcp_service_account"],scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive",],)).open('Dados_Simulacao').worksheet('Ambiente')

    dados_inversor = pd.DataFrame(inversores.get_all_records()).set_index('Inversor')
    dados_modulo = pd.DataFrame(modulos.get_all_records()).set_index('Módulo')
    dados_ambiente = pd.DataFrame(ambiente.get_all_records())

    return dados_modulo, dados_inversor, dados_ambiente

@st.cache_data
def Access_Folder():
    cred_file = Credentials.from_service_account_info(st.secrets["gcp_service_account_2"], scopes=["https://www.googleapis.com/auth/drive","https://www.googleapis.com/auth/spreadsheets",],)
    service = build('drive', 'v3', credentials=cred_file)
    folder_id = st.secrets["gcp_files"]['list_folder_id']
    df = []
    for folder in folder_id:
        query = f"parents ='{folder}'"
        resource = service.files().list(q=query).execute()
        files = resource.get("files")
        nextPageToken = resource.get('nextPageToken')

        while nextPageToken:
            resource = service.files().list(q=query).execute()
            files.extend(resource.get("files"))
            nextPageToken = resource.get('nextPageToken')
        df.append(pd.DataFrame(files))
    return df

@st.cache_data(ttl=360)
def import_from_GoogleSheets(lista_arquivos_teste):
    # Arquivos de dados de medição importados da nuvem
    resultado = []
    for arquivo in lista_arquivos_teste:
        resultado.append(pd.DataFrame(gspread.authorize(Credentials.from_service_account_info(st.secrets["gcp_service_account_2"], scopes=[
                "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive", ], )).open(
                arquivo).worksheet('Sheet1').get_all_records()))
    return resultado

#@st.experimental_memo
def plot_graficos(parametros_eletricos, dados, nome_arquivo, filtro_data):
    import plotly.graph_objs as go
    fig = go.Figure()
    dados['Hora'] = pd.to_datetime(dados['Hora'])
    periodo = (dados['Hora'] >= filtro_data.min()) & (dados['Hora'] <= filtro_data.max())
    for parametro_eletrico in parametros_eletricos:
        fig.add_trace(go.Line(x=filtro_data, y=dados[periodo][parametro_eletrico], name=parametro_eletrico))
    fig.update_layout(
        title=f'Dados de {nome_arquivo}',
        title_x=0.25, title_y=0.85,
        xaxis_title='tempo', yaxis_title='',
        font=dict(family="Courier New, monospace", size=12, color="RebeccaPurple"),
        showlegend=True,
        width=500, height=350
    )
    fig.update_xaxes(rangemode='tozero')
    fig.update_yaxes(rangemode='tozero')
    return fig
