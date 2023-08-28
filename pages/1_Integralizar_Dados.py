import streamlit as st
import pandas as pd
from io import BytesIO
from ImportarArquivos import carregar_dados
import plotly.graph_objs as go
import xlsxwriter
import openpyxl

st.set_page_config(
    page_title="GEDAE Aplicativos - Integralização dos Dados",
    page_icon="👋",
	layout="wide"
)

st.title("Integralização dos Dados")

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

tab_titles = [
    'Importar Arquivos',
    'Seleção de Dado(s), Ajustes e Resultados',
	'Visualizar Resultados'
]

tabs = st.tabs(tab_titles)

with tabs[0]:
	uploaded_files = st.file_uploader("Upload Arquivo(s)", type=["xlsx", "xls", "csv"], accept_multiple_files=True)

	up = []
	for file in uploaded_files:
		if file.name not in str(up):
			up.append(file)

	dados = carregar_dados(up, 'integralizar')

	st.write(f'''
		    _________________________________________________________________________
		        ''')
#dados_filtrados, dados_integralizados = pd.DataFrame(), pd.DataFrame()
with tabs[1]:
	if dados.size != 0:
		dados[dados.columns[1]] = dados[dados.columns[1]].astype(float)

		selecionar_tudo = st.checkbox("Selecionar todas as colunas de dados", value=True)

		coluna_selecao_1, coluna_selecao_2 = st.columns((3, 2))
		coluna_ajustes_1, coluna_ajustes_2 = st.columns((1, 3.3))

		if selecionar_tudo:
			filtro = dados.drop(['TEMPO'], axis=1).columns.tolist()
		else:
			filtro = coluna_selecao_1.multiselect('Selecione a(s) coluna(s) de dado(s):',
												dados.drop(['TEMPO'], axis=1).columns)

		if filtro != []:
			filtro.insert(0, 'TEMPO')
			filtragem_dados = dados.filter(items=filtro).sort_values(by=['TEMPO'], ignore_index=True)
			remover_linhas_nulas = coluna_selecao_1.radio('Existe alguma coluna que precisa filtrar os dados iguais a zero?',
												 ['Não', 'Sim'],
												 horizontal=True)
			if remover_linhas_nulas == 'Sim':
				filtro2 = coluna_selecao_1.multiselect('Selecione a(s) coluna(s) para filtrar os dados nulos:',
													   dados.drop(['TEMPO'], axis=1).columns)
				dados_filtrados = filtragem_dados.loc[(filtragem_dados[filtro2] > 0).all(axis=1)]
			else:
				dados_filtrados = filtragem_dados
			periodo = str(int(coluna_ajustes_1.number_input('Período de integralização:', min_value=1)))
			unidadetempo = coluna_ajustes_2.radio('Selecione a unidade de tempo:',
												  ['Segundo(s)', 'Minuto(s)', 'Hora(s)',
												   'Dia(s)', 'Mês(es)', 'Ano(s)'],
												  horizontal=True)

			if unidadetempo == 'Segundo(s)':
				unidade_de_periodo = 's'
			elif unidadetempo == 'Minuto(s)':
				unidade_de_periodo = 'min'
			elif unidadetempo == 'Hora(s)':
				unidade_de_periodo = 'h'
				complemento_nomearquivo = 'Horária'
			elif unidadetempo == 'Dia(s)':
				unidade_de_periodo = 'd'
				complemento_nomearquivo = 'Diária'
			elif unidadetempo == 'Mês(es)':
				unidade_de_periodo = 'M'
				complemento_nomearquivo = 'Mensal'
			elif unidadetempo == 'Ano(s)':
				unidade_de_periodo = 'y'
				complemento_nomearquivo = 'Anual'

			integralizacao = periodo+unidade_de_periodo
			novo_dados_integralizacao = dados_filtrados.groupby('TEMPO').mean()

			excluir_dados_ausentes = st.checkbox("Excluir todas as linhas com dados ausentes", value=True)
			formato_integralizacao = st.radio('Selecione o procedimento a ser realizado com os dados:',
												  ['Média', 'Integralização'],
												  horizontal=True)
			if excluir_dados_ausentes:
				if formato_integralizacao == 'Média':
					if (sum(novo_dados_integralizacao.index.minute) > 0 or sum(novo_dados_integralizacao.index.second) > 0) and unidade_de_periodo not in ['s','min','h']:
						dados_integralizados = novo_dados_integralizacao.resample(integralizacao).mean().dropna().reset_index()
						st.write('entrou 1')
					else:
						dados_integralizados = novo_dados_integralizacao.resample(integralizacao, label='right', closed='right').mean().dropna().reset_index()
						st.write('entrou 2')
				else:
					if (sum(novo_dados_integralizacao.index.minute) > 0 or sum(novo_dados_integralizacao.index.second) > 0):
						if unidade_de_periodo not in ['s','min', 'h']:
							novo_dados_integralizacao2 = novo_dados_integralizacao.resample('1h').mean().dropna()
							dados_integralizados = novo_dados_integralizacao2.resample(integralizacao).sum().dropna().reset_index()
							st.write('entrou 3.1')
						elif unidade_de_periodo == 'h':
							novo_dados_integralizacao2 = novo_dados_integralizacao.resample('1h', label='right', closed='right').mean().dropna()
							dados_integralizados = novo_dados_integralizacao2.resample(integralizacao).sum().dropna().reset_index()
							st.write('entrou 3.2')
						else:
							dados_integralizados = novo_dados_integralizacao.resample(integralizacao, label='right', closed='right').mean().dropna().reset_index()
							st.write('entrou 3.3')
					else:
						dados_integralizados = novo_dados_integralizacao.resample(integralizacao).sum().dropna().reset_index()
						#dados_integralizados = novo_dados_integralizacao.resample(integralizacao, label='right', closed='right').sum().dropna().reset_index()
						st.write('entrou 4')
			else:
				if formato_integralizacao == 'Média':
					if (sum(novo_dados_integralizacao.index.minute) > 0 or sum(novo_dados_integralizacao.index.second) > 0) and unidade_de_periodo not in ['s', 'min','h']:
						dados_integralizados = novo_dados_integralizacao.resample(integralizacao).mean().reset_index()
					else:
						dados_integralizados = novo_dados_integralizacao.resample(integralizacao, label='right', closed='right').mean().reset_index()
				else:
					if sum(novo_dados_integralizacao.index.minute) > 0 or sum(novo_dados_integralizacao.index.second) > 0:
						st.write('entrou')
						novo_dados_integralizacao2 = novo_dados_integralizacao.resample('1h').mean().reset_index()
						dados_integralizados = novo_dados_integralizacao2.resample(integralizacao).sum().reset_index()
					else:
						dados_integralizados = novo_dados_integralizacao.resample(integralizacao).sum().reset_index()

			dados_integralizados.insert(1, 'DATE', dados_integralizados['TEMPO'].dt.date)
			dados_integralizados.insert(2, 'TIME', dados_integralizados['TEMPO'].dt.time.astype('str'))
			dados_integralizados.rename(columns={'TEMPO': 'REF'}, inplace=True)

			st.write("### Salvar Resultados")

			coluna_nomear_arquivo_1, coluna_nomear_arquivo_2 = st.columns((3, 2))
			nomeprovisorio = formato_integralizacao + '-' + complemento_nomearquivo if unidade_de_periodo in ['h', 'd', 'M', 'y'] else formato_integralizacao
			nomearquivo = coluna_nomear_arquivo_1.text_input('Digite um nome para o arquivo:', nomeprovisorio)

			coluna_salvar_1, coluna_salvar_2, coluna_salvar_3 = st.columns((2, 2, 6))
			csv = converter_df_csv(dados_integralizados)
			excel = converter_df_excel(dados_integralizados)
			coluna_salvar_1.download_button(label="Download em CSV", data=csv, file_name=nomearquivo + '.csv', mime='text/csv')
			coluna_salvar_2.download_button(label="Download em Excel", data=excel, file_name=nomearquivo+'.xlsx', mime='application/vnd.ms-excel')

	st.write(f'''
			_________________________________________________________________________
				''')

with tabs[2]:
	if dados.size != 0:
		if filtro != []:
			if len(filtro[1::]) == 1:
				parametro = filtro[1]
			else:
				parametro = st.selectbox('Escolha um parâmetro para plotar: ', filtro[1::])
			st.write(parametro)
			fig = go.Figure()
			fig.add_trace(go.Line(x=dados_filtrados['TEMPO'], y=dados_filtrados[parametro], name='Dataset Original'))
			fig.add_trace(go.Line(x=dados_integralizados['REF'], y=dados_integralizados[parametro],
								  line=dict(dash='dash'), name='Dataset Integralizado'))
			fig.update_layout(
				title='Dataset Original e Integralizado',
				title_x=0.5,
				xaxis_title='Tempo',
				yaxis_title=parametro,
				font=dict(
					family="Courier New, monospace",
					size=12,
					color="RebeccaPurple"
				),
				#showlegend=False,
				width=800, height=400
			)
			fig.update_xaxes(rangemode='tozero')
			fig.update_yaxes(rangemode='tozero')

			st.plotly_chart(fig)

			coluna_resultados_1, coluna_resultados_2 = st.columns((2, 2))
			coluna_resultados_1.write("### Dataset Original")
			coluna_resultados_1.dataframe(dados_filtrados)
			coluna_resultados_2.write("### Resultados")
			coluna_resultados_2.dataframe(dados_integralizados)

	st.write(f'''
	    _________________________________________________________________________
	        ''')
