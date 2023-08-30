import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np
from io import BytesIO
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
		dados_df = pd.read_csv(up, sep=';', decimal=',', dayfirst=True)

	return dados_df

# DataFrame de exemplo
st.write(f'''
	                _________________________________________________________________________
	                  ''')
arquivo = st.file_uploader('Dados para cálculo dos desvios:', type=['XLSX', 'CSV'])
st.write(f'''
	                _________________________________________________________________________
	                  ''')

if arquivo != None:
	df1 = carregar(arquivo).dropna().reset_index()
	df2 = df1.set_index('Data').resample('1d').sum()
	nome_ultima_coluna = df2.columns[-1]
	nome_penultima_coluna = df2.columns[-2]

	df2[nome_penultima_coluna] = df2[nome_penultima_coluna]/1000
	df2[nome_ultima_coluna] = df2[nome_ultima_coluna] / 1000
	df3 = df2[df2[nome_penultima_coluna] != 0]

	st.write(df2.resample('1M').sum())
	st.write()
	df = df3.reset_index()
	df['Dia'] = df['Data'].dt.day
	df['Mes'] = df['Data'].dt.month
	df['Ano'] = df['Data'].dt.year

	# Cálculo do RMSE e MAE para cada grupo de tempo
	resultados = df.groupby(['Ano', 'Mes']).apply(lambda x: pd.Series({
		'MSE': mean_squared_error(x[nome_penultima_coluna], x[nome_ultima_coluna]),
		'RMSE': np.sqrt(mean_squared_error(x[nome_penultima_coluna], x[nome_ultima_coluna])),
		'MAE': mean_absolute_error(x[nome_penultima_coluna], x[nome_ultima_coluna])
	}))

	# Cálculo do RMSE e MAE para cada grupo de tempo
	resultados2 = df.groupby('Ano').apply(lambda x: pd.Series({
		'MSE': mean_squared_error(x[nome_penultima_coluna], x[nome_ultima_coluna]),
		'RMSE': np.sqrt(mean_squared_error(x[nome_penultima_coluna], x[nome_ultima_coluna])),
		'MAE': mean_absolute_error(x[nome_penultima_coluna], x[nome_ultima_coluna])
	}))

	# Exibindo os resultados
	coluna1, coluna2 = st.columns((3, 2))
	coluna1.write(resultados)
	coluna2.write(resultados2)

	st.write("### Salvar Resultados")

	coluna_nomear_arquivo_1, coluna_nomear_arquivo_2 = st.columns((3, 2))
	nomeprovisorio = 'Cálculo de RMSE e MAE do arquivo ' + arquivo.name[:-5]
	nomearquivo = coluna_nomear_arquivo_1.text_input('Digite um nome para o arquivo:', nomeprovisorio)

	coluna_salvar_1, coluna_salvar_2, coluna_salvar_3 = st.columns((2, 2, 6))
	csv = converter_df_csv(resultados.reset_index())
	excel = converter_df_excel(resultados.reset_index())
	coluna_salvar_1.download_button(label="Download em CSV", data=csv, file_name=nomearquivo + '.csv',
									mime='text/csv')
	coluna_salvar_2.download_button(label="Download em Excel", data=excel, file_name=nomearquivo + '.xlsx',
									mime='application/vnd.ms-excel')

st.write(f'''
	                _________________________________________________________________________
	                  ''')
