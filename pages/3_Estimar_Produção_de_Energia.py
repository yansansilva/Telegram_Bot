import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from scipy.interpolate import CubicSpline
from AnaliseFotovoltaico import *
from ExtrairDadosSFCR import *
from ImportarArquivos import *

st.set_page_config(
    page_title="GEDAE Aplicativos - Estimativa de Geração de Energia",
    page_icon="👋",
    layout="wide"
)

def clear_cache():
    from streamlit.runtime.caching import cache_data_api
    cache_data_api.CachedFunc.clear(import_from_GoogleDrive)

st.title("Estimativa de Geração de Energia")

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
        st.sidebar.button("Atualizar Dados",on_click=clear_cache)
        dados_modulo, dados_inversor, dados_ambiente = import_from_GoogleDrive()
        dadosAmbienteValidos = dados_ambiente[(dados_ambiente.dropna().values != 0).all(axis=1)]
        dadosAmbienteValidos['Data'] = pd.to_datetime(dadosAmbienteValidos['Data'], dayfirst=True)
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
            dados_modulo = carregar_dados(arquivo_modulos, 'FDI')  # Características do módulo fotovoltaico
            modulo = coluna_selecao_1.selectbox('Módulo', dados_modulo.columns)
            if coluna_selecao_1.checkbox('Mostrar Dados do Módulo'):
                coluna_selecao_1.dataframe(dados_modulo[modulo])
        if arquivo_inversores is not None:
            dados_inversor = carregar_dados(arquivo_inversores, 'FDI')  # Infomações dos inversores
            if dados_pre_estabelecidos:
                inversor = coluna_selecao_2.selectbox('Inversor', [dados_inversor.columns[int(dados_modulo[modulo]['Nº célula ref. ao inversor']) - 1]])
            else:
                inversor = coluna_selecao_2.selectbox('Inversor', dados_inversor.columns)
            if coluna_selecao_2.checkbox('Mostrar Dados do Inversor'):
                coluna_selecao_2.dataframe(dados_inversor[inversor])
        if arquivo_ambiente is not None:
            dados_ambiente = carregar_dados(arquivo_ambiente, 'FDI')  # Informações de irradiância e temperatura ambiente
            dadosAmbienteValidos = dados_ambiente[(dados_ambiente.dropna().values != 0).all(axis=1)]
            dadosAmbienteValidos['Data'] = pd.to_datetime(dadosAmbienteValidos['Data'])
            Iinci = dadosAmbienteValidos['Gk'].values  # Cria um vetor irradiância Iinci, eliminando os valores nulos
            Tambi = dadosAmbienteValidos['Ta'].values  # Cria um vetor temperatura ambiente Tamb, eliminando os valores
            # correspondentes ao zero de irradiância
        if arquivo_modulos and arquivo_inversores and arquivo_ambiente is not None:
            Pmp, Imp, Vmp, Isc, Voc, TNOC, CIsc, CVoc, Gama = extrair_dados_modulos(dados_modulo, modulo, 'FDI')
            PnInv, Pmax, FVImp, Vioc, Imax, PmaxInv, EficInv10, EficInv50, EficInv100 = extrair_dados_inversores(
                dados_inversor, inversor)
    else:
        st.write('### Selecione os componentes do SFCR')
        dados_pre_estabelecidos = st.checkbox('Utilizar configurações pré-estabelecidas dos SFCR')

        coluna_selecao_1, coluna_selecao_2, coluna_selecao_3 = st.columns((2, 2, 2))
        modulo = coluna_selecao_1.selectbox('Módulo', dados_modulo.columns)
        st.write(modulo)
        if coluna_selecao_1.checkbox('Mostrar Dados do Módulo'):
            coluna_selecao_1.dataframe(dados_modulo[modulo])
        if dados_pre_estabelecidos:
            inversor = coluna_selecao_2.selectbox('Inversor', [dados_inversor.columns[int(dados_modulo[modulo]['Nº célula ref. ao inversor']) - 1]])
        else:
            inversor = coluna_selecao_2.selectbox('Inversor', dados_inversor.columns)
        st.write(inversor)
        if coluna_selecao_2.checkbox('Mostrar Dados do Inversor'):
            coluna_selecao_2.dataframe(dados_inversor[inversor])
        st.write(Tambi)
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

if modulo != '' and inversor != '' and Tambi != []:
    while FDIi <= sol_span_high:
        Pmref = PnInv / FDIi
        # Função que calcula a potência teórica produzida por um gerador fotovoltaico
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
        FDI.append(FDIi)
        FDIi = round(FDIi + 0.1, 1)  # Incrementa o FDI

    #############-EFICIÊNCIA ENERGÉTICA DO INVERSOR-##########
    if uti_max == 1:
        ind_FDI_max = Yf.index(max(Yf))
        FDI_dim = FDI[ind_FDI_max]

    Tc = max(Tambi) + 1000 * (TNOC - 20) / 800
    Tc_min = min(Tambi) + 200 * (TNOC - 20) / 800

    FDI_interv = np.round(np.arange(-0.0019933, sol_span_high + 0.01, 0.01), 2).tolist()
    Yf_interp = CubicSpline(FDI, Yf)

    calculo = 'Energia'
    figura = None

    #Sistema.calc_ger(Vmp, Voc, CVoc, Imax, Imp, Pmp, Tc, Tc_min, Tcref, FVImp, PnInv, sol_span_low, sol_span_high,
    #                 FDI_interv, Yf_interp, modulo, inversor, calculo, figura)


    dadosAmbienteValidos = dadosAmbienteValidos.assign(Psaida=np.abs(Psaida)).set_index('Data')
    potenciaSaida = dadosAmbienteValidos['Psaida']

with tabs[2]:
    if modulo != '' and inversor != '' and Tambi != []:
        st.write('### Integralização')
        coluna_integralizacao_1, coluna_integralizacao_2, coluna_integralizacao_3 = st.columns((2, 2, 2))
        tempo = coluna_integralizacao_1.text_input('Período', '1')
        escala_de_tempo = {'Dia':'d', 'Mês':'M', 'Ano':'y'}
        integralizacao = coluna_integralizacao_2.selectbox('Escala de tempo', escala_de_tempo)
        periodo = tempo + escala_de_tempo[integralizacao]

        Energia = potenciaSaida.resample(periodo).sum().dropna()/1000
        Energia = Energia.rename('Energia')
        Yf = Energia*(1-PCP)/(Pmref/1000) # Produtividade, corrigidas as perdas em cabos e proteções
        Yf = Yf.rename('Yf')

        st.write(f'''
                _________________________________________________________________________
                  ''')

        coluna_resultado_1, coluna_resultado_2, coluna_resultado_3 = st.columns((2, 2, 3))
        coluna_resultado_1.write('Energia')
        coluna_resultado_1.dataframe(Energia)
        coluna_resultado_1.write('Total: ' + '{:.2f}'.format(Energia.sum()) + ' kWh')
        coluna_resultado_2.write('Produtividade')
        coluna_resultado_2.dataframe(Yf)

        fig = go.Figure()
        fig.add_trace(go.Line(x=Energia.index, y=Energia))
        fig.add_trace(go.Line(x=Yf.index, y=Yf, line=dict(dash='dash')))
        fig.update_layout(
            title=f'Inversor: {inversor} <br> Módulo: {modulo}',
            title_x=0.5,
            #xaxis_title='FDI = PnomInv/PnomGer',
            #yaxis_title="Yf (kWh / kWp)",
            font=dict(
                family="Courier New, monospace",
                size=12,
                color="RebeccaPurple"
            ),
            showlegend=False,
            width=500, height=350
        )
        fig.update_xaxes(rangemode='tozero')
        fig.update_yaxes(rangemode='tozero')

        coluna_resultado_3.plotly_chart(fig)

    st.write(f'''
                _________________________________________________________________________
                  ''')
