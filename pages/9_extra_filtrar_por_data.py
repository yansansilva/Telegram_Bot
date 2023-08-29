import pandas as pd
from io import BytesIO
import plotly.graph_objs as go
import streamlit as st

@st.cache_data
def converter_df_csv(df):
	# IMPORTANT: Cache the conversion to prevent computation on every rerun
	return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def converter_df_excel(df):
	output = BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	df.to_excel(writer, index=False, sheet_name='Plan1')
	workbook = writer.book
	worksheet = writer.sheets['Plan1']
	format1 = workbook.add_format({'num_format': '0.00'})
	worksheet.set_column('A:A', None, format1)
	writer.save()
	processed_data = output.getvalue()
	return processed_data

@st.cache_data
def carregar(up):
	if up.type != "text/csv":
		dados_df = pd.read_excel(up, sheet_name=0, index_col=0)
	else:
		dados_df = pd.read_csv(up, sep=';', decimal=',', dayfirst=True, encoding='cp1252')

	return dados_df

# DataFrame de exemplo
st.write(f'''
					_________________________________________________________________________
					  ''')
arquivo1 = st.file_uploader('Dados do Arquivo de Medição:', type=['XLSX', 'CSV'])

arquivo2 = st.file_uploader('Arquivo de Datas de Referência:', type=['XLSX', 'CSV'])

st.write(f'''
					_________________________________________________________________________
					  ''')

if arquivo1 != None and arquivo2 != None:
	# DataFrame maior
	df_dados = carregar(arquivo1).dropna().reset_index()
	df_dados['Data'] = pd.to_datetime(df_dados['Data'])
	st.write(df_dados)

	# DataFrame menor com dados adicionais
	df_datas_referencia = carregar(arquivo2).dropna().reset_index()
	df_datas_referencia['Data'] = pd.to_datetime(df_datas_referencia['Data'])
	st.write(df_datas_referencia)

	# Converter as colunas de datas para o tipo datetime e ignorar o horário
	df_datas_referencia['Data'] = pd.to_datetime(df_datas_referencia['Data']).dt.date
	df_dados['Data'] = pd.to_datetime(df_dados['Data'])

	# Filtrar os dados usando as datas de referência
	df_filtrado1 = df_dados[df_dados['Data'].dt.date.isin(df_datas_referencia['Data'])]

	df_filtrado2 = df_filtrado1[df_filtrado1['Psaida'] > 0]

	resultado = df_filtrado2[df_filtrado2['Potência'] > 0]

	st.write(resultado)

	st.write("### Salvar Resultados")

	coluna_nomear_arquivo_1, coluna_nomear_arquivo_2 = st.columns((3, 2))
	nomeprovisorio = 'Dados Mesclados de ' + arquivo1.name[:-5] + ' com ' + arquivo2.name[:-5]
	nomearquivo = coluna_nomear_arquivo_1.text_input('Digite um nome para o arquivo:', nomeprovisorio)

	coluna_salvar_1, coluna_salvar_2, coluna_salvar_3 = st.columns((2, 2, 6))
	csv = converter_df_csv(resultado)
	excel = converter_df_excel(resultado)
	coluna_salvar_1.download_button(label="Download em CSV", data=csv, file_name=nomearquivo + '.csv',
									mime='text/csv')
	coluna_salvar_2.download_button(label="Download em Excel", data=excel, file_name=nomearquivo + '.xlsx',
									mime='application/vnd.ms-excel')

st.write(f'''
				_________________________________________________________________________
					  ''')
