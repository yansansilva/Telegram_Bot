import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from ImportarArquivos import *

st.set_page_config(
    page_title="GEDAE Aplicativos - Geração e Consumo da Edificação",
    page_icon="👋",
    layout="wide"
)
  
lista_nomes_arquivos_climatizacao = Access_Folder()[0]['name']
lista_nomes_arquivos_equipamentos = Access_Folder()[1]['name']
lista_nomes_arquivos_iluminacao = Access_Folder()[2]['name']
lista_nomes_arquivos_geral = Access_Folder()[3]['name']
lista_nomes_arquivos_teste = Access_Folder()[4]['name']

def clear_cache():
    from streamlit.runtime.caching import cache_data_api
    cache_data_api.CachedFunc.clear(manual_import_from_GoogleSheets)

if st.sidebar.checkbox('Atualizar Dados Manualmente'):
    st.sidebar.button("Atualizar Dados",on_click=clear_cache)
    dados = manual_import_from_GoogleSheets(lista_nomes_arquivos_teste)
else:
    dados = auto_import_from_GoogleSheets(lista_nomes_arquivos_teste)

#dados = import_from_GoogleSheets(lista_nomes_arquivos_teste)
data = pd.to_datetime(dados[0]['Hora'])
coluna_1, coluna_2, coluna_3 = st.columns(3)
filtro_ano = coluna_1.selectbox('Ano:', options=data.dt.year.drop_duplicates(), index=(len(data.dt.year.drop_duplicates()))-1)
filtro_mes = coluna_2.selectbox('Mês:', options=data[data.dt.year == filtro_ano].dt.month.drop_duplicates(), index=(len(data[data.dt.year == filtro_ano].dt.month.drop_duplicates()))-1)
filtro_dia = coluna_3.selectbox('Dia:', options=data[data.dt.month == filtro_mes].dt.day.drop_duplicates(), index=(len(data[data.dt.month == filtro_mes].dt.day.drop_duplicates()))-1)

filtro_data = data[data.dt.year == filtro_ano][data.dt.month == filtro_mes][data.dt.day == filtro_dia].reset_index(drop=True)
escolher_parametros_eletricos = st.radio('', ['Escolher quais parâmetros plotar.', 'Plotar todos os parâmetros.'], horizontal=True)
parametros_eletricos = []
if escolher_parametros_eletricos == 'Escolher quais parâmetros plotar.':
    parametros_eletricos = st.multiselect('Parâmetros Elétricos:', dados[0].columns[1:])
else:
    parametros_eletricos = dados[0].columns[1:].to_list()

divisao_tela1, divisao_tela2, divisao_tela3 = st.columns((2.75, 0.5, 2.75))

if parametros_eletricos != []:
#    for i in range(len(lista_nomes_arquivos_teste)):
#        if i%2 == 0:
#            divisao_tela1.plotly_chart(plot_graficos(parametros_eletricos, dados[i], lista_nomes_arquivos_teste[i], filtro_data))
#        else:
#            divisao_tela3.plotly_chart(plot_graficos(parametros_eletricos, dados[i], lista_nomes_arquivos_teste[i], filtro_data))
    
    divisao_tela1.plotly_chart(plot_graficos(parametros_eletricos, dados[0], lista_nomes_arquivos_teste[0], filtro_data))
    divisao_tela3.plotly_chart(plot_graficos(parametros_eletricos, dados[1], lista_nomes_arquivos_teste[1], filtro_data))
    divisao_tela1.plotly_chart(plot_graficos(parametros_eletricos, dados[2], lista_nomes_arquivos_teste[2], filtro_data))
    divisao_tela3.plotly_chart(plot_graficos(parametros_eletricos, dados[3], lista_nomes_arquivos_teste[3], filtro_data))
    divisao_tela1.plotly_chart(plot_graficos(parametros_eletricos, dados[4], lista_nomes_arquivos_teste[4], filtro_data))
    divisao_tela3.plotly_chart(plot_graficos(parametros_eletricos, dados[5], lista_nomes_arquivos_teste[5], filtro_data))
    divisao_tela1.plotly_chart(plot_graficos(parametros_eletricos, dados[6], lista_nomes_arquivos_teste[6], filtro_data))
