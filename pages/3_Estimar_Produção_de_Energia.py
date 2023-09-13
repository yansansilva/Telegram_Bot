import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from scipy.interpolate import CubicSpline
from io import BytesIO
from AnaliseFotovoltaico import *
from ExtrairDadosSFCR import *
from ImportarArquivos import *

st.set_page_config(
    page_title="GEDAE Aplicativos - Estimativa de Geração de Energia",
    page_icon="👋",
    layout="wide"
)

st.title("Estimativa de Geração de Energia")

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
	writer.close() #writer.save()
	processed_data = output.getvalue()
	return processed_data

def calcular_degradacao(Energia, degradacao_mensal, data_de_instalacao):
    # Calcular a diferença em meses entre as datas (meses diferentes)
    listar_meses = 12 * (Energia.index.year - data_de_instalacao.year) + (Energia.index.month - data_de_instalacao.month)
    mes = pd.DataFrame(listar_meses).set_index(Energia.index)
    mes[mes < 0] = 0
    Energia_com_degradacao = Energia * (1 - degradacao_mensal * mes['Data'])
    Energia_com_degradacao = Energia_com_degradacao.rename('Energia com degradação (kWh)')
    Energia_com_degradacao[Energia_com_degradacao < 0] = 0
    return Energia_com_degradacao

tab_titles = [
    'Importar Arquivos',
    'Selecionar os componentes do SFCR',
    'Resultados',
]

tabs = st.tabs(tab_titles)

dados_modulo, dados_inversor, dadosAmbienteValidos = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
Iinci, Tambi = [], []
modulo, inversor, arquivo_modulos, arquivo_inversores, arquivo_ambiente = '', '', '', '',''

with tabs[0]:
    st.write("### Upload dos arquivos")
    importar_dados = st.radio('', ('Importar sua própria base de dados', 'Importar base de dados do servidor'),
                              horizontal=True)
    st.write(f'''
        _________________________________________________________________________
            ''')
    if importar_dados == 'Importar sua própria base de dados':
        coluna_upload_1, coluna_upload_2, coluna_upload_3 = st.columns((2, 2, 2))
        arquivo_modulos = coluna_upload_1.file_uploader('Dados dos Módulos', type=['XLS', 'XLSX'])
        arquivo_inversores = coluna_upload_2.file_uploader('Dados dos Inversores', type=['XLS', 'XLSX'])
        arquivo_ambiente = coluna_upload_3.file_uploader('Dados do Ambiente', type=['CSV'])
    else:
        dados_modulo, dados_inversor, dados_ambiente = import_from_GoogleDrive()
        dados_ambiente['Gk'] = pd.to_numeric(dados_ambiente['Gk'], errors='coerce')
        dados_ambiente['Ta'] = pd.to_numeric(dados_ambiente['Ta'], errors='coerce')
        dados_ambiente = dados_ambiente.dropna()

        dadosAmbienteValidos = dados_ambiente[(dados_ambiente.values != 0).all(axis=1)]
        dadosAmbienteValidos['Data'] = pd.to_datetime(dadosAmbienteValidos['Data'])
        Iinci = dadosAmbienteValidos['Gk'].values  # Cria um vetor irradiância Iinci, eliminando os valores nulos
        Tambi = dadosAmbienteValidos['Ta'].values  # Cria um vetor temperatura ambiente Tamb, eliminando os valores
        # correspondentes ao zero de irradiância
    st.write(f'''
            _________________________________________________________________________
              ''')

with tabs[1]:
    if importar_dados == 'Importar sua própria base de dados':
        if arquivo_modulos or arquivo_inversores is not None:
            st.write('### Selecione os componentes do SFCR')
            dados_pre_estabelecidos = st.checkbox('Utilizar configurações pré-estabelecidas dos SFCR')
        coluna_selecao_1, coluna_selecao_2, coluna_selecao_3 = st.columns((2, 2, 2))
        if arquivo_modulos is not None:
            dados_modulo = carregar_dados(arquivo_modulos, 'Energia')  # Características do módulo fotovoltaico
            modulo = coluna_selecao_1.selectbox('Módulo', dados_modulo.columns)
            if coluna_selecao_1.checkbox('Mostrar Dados do Módulo'):
                coluna_selecao_1.dataframe(dados_modulo[modulo])
        if arquivo_inversores is not None:
            dados_inversor = carregar_dados(arquivo_inversores, 'Energia')  # Infomações dos inversores
            if dados_pre_estabelecidos:
                inversor = coluna_selecao_2.selectbox('Inversor', [dados_inversor.columns[int(dados_modulo[modulo]['Nº célula ref. ao inversor']) - 1]])
            else:
                inversor = coluna_selecao_2.selectbox('Inversor', dados_inversor.columns)
            if coluna_selecao_2.checkbox('Mostrar Dados do Inversor'):
                coluna_selecao_2.dataframe(dados_inversor[inversor])
        if arquivo_ambiente is not None:
            dados_ambiente = carregar_dados(arquivo_ambiente, 'Energia').dropna()  # Informações de irradiância e temperatura ambiente
            dadosAmbienteValidos = dados_ambiente[(dados_ambiente.values != 0).all(axis=1)]
            dadosAmbienteValidos['Data'] = pd.to_datetime(dadosAmbienteValidos['Data'], dayfirst=True)
            Iinci = dadosAmbienteValidos['Gk'].values  # Cria um vetor irradiância Iinci, eliminando os valores nulos
            Tambi = dadosAmbienteValidos['Ta'].values  # Cria um vetor temperatura ambiente Tamb, eliminando os valores
            # correspondentes ao zero de irradiância
        if arquivo_modulos and arquivo_inversores and arquivo_ambiente is not None:
            Pmp, Imp, Vmp, Isc, Voc, TNOC, CIsc, CVoc, Gama, N_mod_serie, N_mod_paralelo = extrair_dados_modulos(dados_modulo, modulo, 'Energia')
            PnInv, Pmax, FVImp, Vioc, Imax, PmaxInv, EficInv10, EficInv50, EficInv100 = extrair_dados_inversores(
                dados_inversor, inversor)
    else:
        st.write('### Selecione os componentes do SFCR')
        dados_pre_estabelecidos = st.checkbox('Utilizar configurações pré-estabelecidas dos SFCR')

        coluna_selecao_1, coluna_selecao_2, coluna_selecao_3 = st.columns((2, 2, 2))
        modulo = coluna_selecao_1.selectbox('Módulo', dados_modulo.columns)
        if coluna_selecao_1.checkbox('Mostrar Dados do Módulo'):
            coluna_selecao_1.dataframe(dados_modulo[modulo])
        if dados_pre_estabelecidos:
            inversor = coluna_selecao_2.selectbox('Inversor', [dados_inversor.columns[int(dados_modulo[modulo]['Nº célula ref. ao inversor']) - 1]])
        else:
            inversor = coluna_selecao_2.selectbox('Inversor', dados_inversor.columns)
        if coluna_selecao_2.checkbox('Mostrar Dados do Inversor'):
            coluna_selecao_2.dataframe(dados_inversor[inversor])

        Pmp, Imp, Vmp, Isc, Voc, TNOC, CIsc, CVoc, Gama, N_mod_serie, N_mod_paralelo = extrair_dados_modulos(dados_modulo, modulo, 'Energia')
        PnInv, Pmax, FVImp, Vioc, Imax, PmaxInv, EficInv10, EficInv50, EficInv100 = extrair_dados_inversores(
            dados_inversor, inversor)
    st.write(f'''
            _________________________________________________________________________
              ''')
    # Pmref = N_mod_paralelo*N_mod_serie*Pmp # Potência nominal do gerador fotovoltaico
    ##### Fim das configurações iniciais

## Valores de referência
Iincref = 1000  # Irradiância de referência W/m2
Tcref = 25  # Temperatura na condição de referência

## Faixa de span da solução
sol_span_low = 0.6
sol_span_high = 2

## PERDAS CC
PD = 0.02  # Perdas decorrentes da dispersão entre módulos
PDCFP = 0.025  # Perdas em Diodos, Cabos, Fusíveis e Proteções
## PERDAS CA
PCP = 0.02  # Cabos e Proteções
##########################################################

uti_max = 1  # Utiliza o FDI cuja produtividade é máxima para o dimensionamento do gerador(1) para utilizar este procedimento e 0 para não utilizar)

FDIi = 0.2
FDI, EficInv, Yf = [], [], []

if modulo != '' and inversor != '' and Tambi is not []:
    # Função que calcula a potência teórica produzida por um gerador fotovoltaico
    Pmref = N_mod_paralelo * N_mod_serie * Pmp # Potência nominal do gerador fotovoltaico
    Pmei = PMPArranjoFV(Pmref, Iincref, Gama, Tcref, TNOC, Iinci, Tambi)
    # Correção de perdas associadas
    Pmei = Pmei * (1 - PD - PDCFP)
    # Parâmetro característico do inversor que computa as perdas de autoconsumo
    k0 = (1 / (9 * EficInv100) - 1 / (4 * EficInv50) + 5 / (36 * EficInv10)) * 100
    # Parâmetro característico do inversor que computa as perdas proporcionais ao carregamento
    k1 = (-1 + (-4 / (3 * EficInv100) + 33 / (12 * EficInv50) - 5 / (12 * EficInv10)) * 100)
    # Parâmetro característico do inversor que computa as perdas proporcionais ao quadrado do carregamento
    k2 = (20 / (9 * EficInv100) - 5 / (2 * EficInv50) + 5 / (18 * EficInv10)) * 100
    # Função que calcula a potência de saída do inversor
    Psaida, p0, PperdasDC, Pperdas = CalcPotSaidaINV(Pmei, PnInv, PmaxInv, k0, k1, k2)
    EficInv.append((sum(Psaida) / sum(Pmei)) * 100)  # Eficiência do inversor
    Yf.append((sum(Psaida) * (1 - PCP)) / Pmref)  # Produtividade, corrigidas as perdas em cabos e proteções

    dadosAmbienteValidos = dadosAmbienteValidos.assign(Psaida=np.abs(Psaida)).set_index('Data').dropna()
    potenciaSaida = dadosAmbienteValidos['Psaida']
    irradiancia = dadosAmbienteValidos['Gk']

with tabs[2]:
    if modulo != '' and inversor != '' and Tambi is not []:
        st.write('### Integralização')
        coluna_integralizacao_1, coluna_integralizacao_2, coluna_integralizacao_3 = st.columns((2, 2, 2))
        tempo = coluna_integralizacao_1.text_input('Período', '1')
        escala_de_tempo = {'Minuto':'min', 'Hora':'h', 'Dia':'d', 'Mês':'M', 'Ano':'y'}
        integralizacao = coluna_integralizacao_2.selectbox('Escala de tempo', escala_de_tempo, index=4)
        periodo = tempo + escala_de_tempo[integralizacao]

        Energia = potenciaSaida.resample(periodo).sum().dropna()/1000
        Energia = Energia.rename('Energia (kWh)')
        Irradiacao = irradiancia.resample(periodo).sum().dropna()/1000
        Irradiacao = Irradiacao.rename('Irradiação (kWh/m²)')
        Yf = Energia*(1-PCP)/(Pmref/1000) # Produtividade, corrigidas as perdas em cabos e proteções
        Yf = Yf.rename('Yf (kWh/kWp)')
        PR = Yf[Yf!=0]/(Irradiacao/1)*100
        PR = PR.rename('PR (%)')
        PR[PR>100] = 100

        if 'min' in periodo:
            Potencia = potenciaSaida.resample(periodo, label='right', closed='right').mean().dropna()/1000
            Potencia = Potencia.rename('Potência de saída (kW)')
        else:
            Potencia = potenciaSaida.resample(periodo).mean().dropna()/1000
            Potencia = Potencia.rename('Potência de saída (kW)')
        st.write(f'''
                _________________________________________________________________________
                  ''')

        st.write('## Resultados')
        considerar_degradacao = st.checkbox('Considerar degradação dos módulos fotovoltaicos')
        Energia_com_degradacao = 0
        if considerar_degradacao:
            escolha = st.radio('Taxa de degradação', options=['Digitar', 'Escolher por tipo de tecnologia'], horizontal=True)
            if escolha == 'Digitar':
                degradacao_anual = st.number_input('Informe a taxa anual de degradação (%): ', min_value=0.00, max_value=100.00, value=0.6)/100
            else:
                tipos_de_tecnologias = {'Si-m': 0.4, 'Si-p': 0.1, 'Si-mj': 1.5}
                # Referência da taxa de degradação: https://onlinelibrary.wiley.com/doi/epdf/10.1002/pip.2903
                tecnologia = st.selectbox('Selecione o tipo de tecnologia do módulo fotovoltaico:', tipos_de_tecnologias)
                degradacao_anual = tipos_de_tecnologias[tecnologia]/100
            data_de_instalacao = st.date_input('Informe a data de instalação do SFCR: ', value=Energia.index[0], max_value=Energia.index[-1])
            degradacao_mensal = degradacao_anual/12
            Energia_com_degradacao = calcular_degradacao(Energia, degradacao_mensal, data_de_instalacao)
            Resultados = pd.concat([Potencia, Energia, Energia_com_degradacao, Irradiacao, Yf, PR], axis=1)
        else:
            Resultados = pd.concat([Potencia, Energia, Irradiacao, Yf, PR], axis=1)
        st.dataframe(Resultados)
        coluna_Total1, coluna_Total2 = st.columns((2, 2))
        coluna_Total1.markdown('<b>Total de Produção de Energia:</b> ' + '{:.2f}'.format(Energia.sum()) + ' kWh', unsafe_allow_html=True)
        if considerar_degradacao:
            coluna_Total2.markdown('<b>Total de Produção de Energia com degradação:</b> ' + '{:.2f}'.format(Energia_com_degradacao.sum()) + ' kWh', unsafe_allow_html=True)

        st.write('### Produção de Energia')
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=Energia.index, y=Energia, name='Energia (kWh)', marker_color='blue'), secondary_y=False)
        if considerar_degradacao:
            fig.add_trace(go.Bar(x=Energia_com_degradacao.index, y=Energia_com_degradacao, name='Energia com degradação (kWh)', marker_color='orangered'), secondary_y=False)
        if st.checkbox('Acrescentar no gráfico os dados de irradiação solar (kWh/m²)'):
            fig.add_trace(go.Bar(x=Irradiacao.index, y=Irradiacao, name='Irradiação solar (kWh/m²)'), secondary_y=True)
        fig.update_layout(
            title=f'Inversor: {inversor} <br> Módulo: {modulo}',
            title_x=0.5,
            font=dict(family="Courier New, monospace", size=12, color="RebeccaPurple"),
            showlegend=True,
            #width=500, height=350
            width=1000, height=400
        )
        # Configurar eixos
        fig.update_xaxes(title_text="Tempo", rangemode='tozero')
        fig.update_yaxes(title_text="Energia (kWh)", secondary_y=False, rangemode='tozero')
        fig.update_yaxes(title_text="Irradiação (kWh/m²)", secondary_y=True, rangemode='tozero')

        st.plotly_chart(fig)

        st.write('### Figuras de Mérito')
        # Create figure with secondary y-axis
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Line(x=Yf.index, y=Yf, name='Produtividade (kWh/kWp)'), secondary_y=False)
        fig1.add_trace(go.Line(x=PR.index, y=PR, name='Rendimento Global (%)'), secondary_y=True)

        fig1.update_layout(
            title=f'Inversor: {inversor} <br> Módulo: {modulo}',
            title_x=0.5,
            font=dict(family="Courier New, monospace", size=12, color="RebeccaPurple"),
            showlegend=True,
            # width=500, height=350
            width=1000, height=400
        )
        # Configurar eixos
        fig1.update_xaxes(title_text="Tempo", rangemode='tozero')
        fig1.update_yaxes(title_text="Produtividade (kWh/kWp)", secondary_y=False, rangemode='tozero')
        fig1.update_yaxes(title_text="Rendimento Global (%)", secondary_y=True, rangemode='tozero')

        st.plotly_chart(fig1)

        st.write("### Salvar Resultados")

        coluna1_nomear_arquivo, coluna2_nomear_arquivo = st.columns((3, 2))
        dict_escala_tempo = {'Minuto':'em Minutos ', 'Hora':'Horários ', 'Dia':'Diários ', 'Mês':'Mensais ', 'Ano':'Anuais '}
        nomeprovisorio = 'Resultados ' + dict_escala_tempo[integralizacao] + 'do Sistema ' + modulo[-3:-1] + '_' + str(Energia.index[0].year) + '-' + str(Energia.index[-1].year)
        nomearquivo = coluna1_nomear_arquivo.text_input('Digite um nome para o arquivo de resultados:', nomeprovisorio)

        coluna1_salvar, coluna2_salvar, coluna3_salvar = st.columns((2, 2, 6))
        csv = converter_df_csv(Resultados.reset_index())
        excel = converter_df_excel(Resultados.reset_index())
        coluna1_salvar.download_button(label="Download em CSV", data=csv, file_name=nomearquivo + '.csv',
                                        mime='text/csv')
        coluna2_salvar.download_button(label="Download em Excel", data=excel, file_name=nomearquivo + '.xlsx',
                                        mime='application/vnd.ms-excel')

    st.write(f'''
                _________________________________________________________________________
                  ''')
