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

arquivo2 = st.file_uploader('Dados do Arquivo da Simulação:', type=['XLSX', 'CSV'])

st.write(f'''
					_________________________________________________________________________
					  ''')

if arquivo1 != None and arquivo2 != None:
	# DataFrame maior
	df1 = carregar(arquivo1).dropna().reset_index()
	df1['Data'] = pd.to_datetime(df1['Data'])
	st.write(df1)

	# DataFrame menor com dados adicionais
	df2 = carregar(arquivo2).dropna().reset_index()
	df2['Data'] = pd.to_datetime(df2['Data'])
	st.write(df2)

	# Mesclar os dataframes com base nas datas

	resultado = pd.merge(df1, df2, on='Data', how='inner').fillna(0).sort_values(by='Data')

	st.write(resultado)

	fig = go.Figure()
	fig.add_trace(go.Line(x=resultado['Data'], y=resultado['Potência'], name='Medido'))
	fig.add_trace(go.Line(x=resultado['Data'], y=resultado['Psaida'],
						  line=dict(dash='dash'), name='Simulado'))
	fig.update_layout(
		title='Potência Medida e Simulada para o QPFV 2',
		title_x=0.50,
		xaxis_title='Tempo',
		yaxis_title='Potência (W)',
		font=dict(
			family="Courier New, monospace",
			size=12,
			color="RebeccaPurple"
		),
		# showlegend=False,
		width=800, height=400
	)
	fig.update_xaxes(rangemode='tozero')
	fig.update_yaxes(rangemode='tozero')

	st.plotly_chart(fig)

	st.write("### Salvar Resultados")

	coluna_nomear_arquivo_1, coluna_nomear_arquivo_2 = st.columns((3, 2))
	nomeprovisorio = 'Dados Mesclados ' + arquivo1.name[:-5]
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
