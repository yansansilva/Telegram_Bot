import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from scipy.interpolate import CubicSpline
from AnaliseFotovoltaico import *
from ExtrairDadosSFCR import *
from ImportarArquivos import *

st.set_page_config(
    page_title="GEDAE Aplicativos - Cálculo do FDI",
    page_icon="👋",
    layout="wide"
)

st.title('Cálculo do FDI')

tab_titles = [
    'Importar Arquivos',
    'Selecionar os componentes do SFCR',
    'Arranjos Propostos',
    'Arranjo com Maior Produtividade',
    'Gráficos'
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
        dadosAmbienteValidos = dados_ambiente[(dados_ambiente.dropna().values != 0).all(axis=1)]
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
            dados_modulo = carregar_dados(arquivo_modulos, 'FDI')  # Características do módulo fotovoltaico
            modulo = coluna_selecao_1.selectbox('Módulo', dados_modulo.columns)
            if coluna_selecao_1.checkbox('Mostrar Dados do Módulo'):
                coluna_selecao_1.dataframe(dados_modulo[modulo])
        if arquivo_inversores is not None:
            dados_inversor = carregar_dados(arquivo_inversores, 'FDI')  # Infomações dos inversores
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
            if dados_pre_estabelecidos:
                # Número da coluna do inversor desejado para análise
                inversor = dados_inversor.columns[int(dados_modulo[modulo]['Nº célula ref. ao inversor']) - 1]
            Pmp, Imp, Vmp, Isc, Voc, TNOC, CIsc, CVoc, Gama = extrair_dados_modulos(dados_modulo, modulo, 'FDI')
            PnInv, Pmax, FVImp, Vioc, Imax, PmaxInv, EficInv10, EficInv50, EficInv100 = extrair_dados_inversores(
                dados_inversor, inversor)
    else:
        st.write('### Selecione os componentes do SFCR')
        dados_pre_estabelecidos = st.checkbox('Utilizar configurações pré-estabelecidas dos SFCR')

        coluna_selecao_1, coluna_selecao_2, coluna_selecao_3 = st.columns((2, 2, 2))
        modulo = coluna_selecao_1.selectbox('Módulo', dados_modulo.columns)
        if coluna_selecao_1.checkbox('Mostrar Dados do Módulo'):
            coluna_selecao_1.dataframe(dados_modulo[modulo])
        inversor = coluna_selecao_2.selectbox('Inversor', dados_inversor.columns)
        if coluna_selecao_2.checkbox('Mostrar Dados do Inversor'):
            coluna_selecao_2.dataframe(dados_inversor[inversor])
        if dados_pre_estabelecidos:
            # Número da coluna do inversor desejado para análise
            inversor = dados_inversor.columns[int(dados_modulo[modulo]['Nº célula ref. ao inversor']) - 1]
        Pmp, Imp, Vmp, Isc, Voc, TNOC, CIsc, CVoc, Gama = extrair_dados_modulos(dados_modulo, modulo, 'FDI')
        PnInv, Pmax, FVImp, Vioc, Imax, PmaxInv, EficInv10, EficInv50, EficInv100 = extrair_dados_inversores(
            dados_inversor, inversor)
    st.write(f'''
            _________________________________________________________________________
              ''')

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

resultados, resultado_maior_produtividade, YfxFDI, YfxFDI_new = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
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

        # Eficiência do inversor
        EficInv.append((sum(Psaida) / sum(Pmei)) * 100)
        # Produtividade, corrigidas as perdas em cabos e proteções
        Yf.append((sum(Psaida) * (1 - PCP)) / Pmref)
        FDI.append(FDIi)
        FDIi = round(FDIi + 0.1, 1)  # Incrementa o FDI

    #############-EFICIÊNCIA ENERGÉTICA DO INVERSOR-##########
    # Gera o gráfico da eficiência do inversor em função do FDI
    YfxFDI = pd.DataFrame(zip(*[FDI, EficInv]), columns=['FDI', 'Yf'])
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=YfxFDI['FDI'], y=YfxFDI['Yf'],
                             marker_symbol='asterisk-open'))

    if uti_max == 1:
        ind_FDI_max = Yf.index(max(Yf))
        FDI_dim = FDI[ind_FDI_max]

    Tc = max(Tambi) + 1000 * (TNOC - 20) / 800
    Tc_min = min(Tambi) + 200 * (TNOC - 20) / 800

    FDI_interv = np.round(np.arange(-0.0019933, sol_span_high + 0.01, 0.01), 2).tolist()
    Yf_interp = CubicSpline(FDI, Yf)

    calculo = 'FDI'

    resultados, resultado_maior_produtividade, YfxFDI, YfxFDI_new = calc_ger(Vmp, Voc, CVoc, Imax, Imp, Pmp, Tc, Tc_min, Tcref, FVImp,
                                                         PnInv, sol_span_low, sol_span_high, FDI_interv, Yf_interp,
                                                         calculo)

with tabs[2]:
    if modulo != '' and inversor != '' and Tambi != []:
        if resultados.empty:
            st.write(f'''
        Não foram encontradas soluções para a faixa de FDI selecionada.
        Mude os valores da faixa de solução em "sol_span_high" e "sol_span_low".
            ''')
        else:
            tabela1 = go.Figure(data=go.Table(
                header=dict(
                    values=list(resultados[['NS[un]', 'NP[un]', 'NM[un]', 'PGER[W]', 'FDI', 'Yf[kWh/kWp]']].columns),
                    fill_color='#FD8E72',
                    align='center'),
                cells=dict(values=[resultados['NS[un]'], resultados['NP[un]'],
                                   resultados['NM[un]'], resultados['PGER[W]'],
                                   np.round(resultados['FDI'], 4), np.round(resultados['Yf[kWh/kWp]'], 4)],
                           fill_color='#E5ECF6',
                           align='center')))
            tabela1.update_layout(
                margin=dict(l=5, r=5, b=10, t=10),
                width=600, height=270
            )
            st.write(f'''
                        ### Resultados
                        _________________________________________________________________________''')
            coluna_tabela_1, coluna_tabela_2, coluna_tabela_3 = st.columns((2, 2, 1.8))

            coluna_tabela_1.write(tabela1)
            coluna_tabela_3.write(f'''
                        Legenda: \n
                        - **NS**: Módulos em série
                        - **NP**: Módulos em paralelo
                        - **NM**: Número de módulos
                        - **PGER**: Potência do gerador
                        - **FDI**: Fator de Dimensionamento do Inversor
                        - **Yf**: Produtividade''')
    st.write(f'''
        _________________________________________________________________________
          ''')

with tabs[3]:
    if modulo != '' and inversor != '' and Tambi != []:
        if resultado_maior_produtividade.empty:
            st.write(f'''
        Não foram encontradas soluções para a faixa de FDI selecionada.
        Mude os valores da faixa de solução em "sol_span_high" e "sol_span_low".
            ''')
        else:
            tabela2 = go.Figure(data=go.Table(
                header=dict(
                    values=list(
                        resultado_maior_produtividade[
                            ['NS[un]', 'NP[un]', 'NM[un]', 'PGER[W]', 'FDI', 'Yf[kWh/kWp]']].columns),
                    fill_color='#FD8E72',
                    align='center'),
                cells=dict(values=[resultado_maior_produtividade['NS[un]'], resultado_maior_produtividade['NP[un]'],
                                   resultado_maior_produtividade['NM[un]'], resultado_maior_produtividade['PGER[W]'],
                                   np.round(resultado_maior_produtividade['FDI'], 4),
                                   np.round(resultado_maior_produtividade['Yf[kWh/kWp]'], 4)],
                           fill_color='#E5ECF6',
                           align='center')))
            tabela2.update_layout(
                margin=dict(l=5, r=5, b=10, t=10),
                width=850, height=70
            )
            st.write(f'''
                        #### Configuração com maior produtividade
                        _________________________________________________________________________''')
            st.write(tabela2)
    st.write(f'''
        _________________________________________________________________________
          ''')

with tabs[4]:
    if modulo != '' and inversor != '' and Tambi != []:
        if YfxFDI.empty and YfxFDI_new.empty:
            st.write(f'''
        Não foram encontradas soluções para a faixa de FDI selecionada.
        Mude os valores da faixa de solução em "sol_span_high" e "sol_span_low".
            ''')
        else:
            fig2 = go.Figure()
            fig2.add_trace(go.Line(x=YfxFDI['FDI'], y=YfxFDI['Yf']))

            fig2.add_trace(go.Scatter(x=YfxFDI_new['FDI'], y=YfxFDI_new['Yf'],
                                      mode='markers', marker_symbol='asterisk-open'))

            fig2.add_vline(x=YfxFDI_new[YfxFDI_new['Yf'] == max(YfxFDI_new['Yf'])].reset_index()['FDI'][0],
                           line_dash="dash", line_color="red")
            for x in range(len(YfxFDI_new['FDI']) - 1):
                fig2.add_vline(x=YfxFDI_new[YfxFDI_new['Yf'] != max(YfxFDI_new['Yf'])].reset_index()['FDI'][x],
                               line_dash="dash", line_color="gray")

            fig1.update_layout(
                title=f'Inversor: {inversor}',
                title_x=0.5,
                title_y=0.85,
                xaxis_title='FDI = PnomInv/PnomGer',
                yaxis_title="Efic. Inversor (%)",
                font=dict(
                    family="Courier New, monospace",
                    size=12,
                    color="RebeccaPurple"
                ),
                showlegend=False,
                width=500, height=350
            )

            fig2.update_layout(
                title=f'Inversor: {inversor} <br> Módulo: {modulo}',
                title_x=0.5,
                xaxis_title='FDI = PnomInv/PnomGer',
                yaxis_title="Yf (kWh / kWp)",
                font=dict(
                    family="Courier New, monospace",
                    size=12,
                    color="RebeccaPurple"
                ),
                showlegend=False,
                width=500, height=350
            )
            fig2.update_xaxes(rangemode='tozero')
            fig2.update_yaxes(rangemode='tozero')

            coluna_Figura_1, coluna_Figura_2, coluna_Figura_3 = st.columns((2.75, 0.5, 2.75))
            coluna_Figura_1.plotly_chart(fig1)
            coluna_Figura_3.plotly_chart(fig2)
    st.write(f'''
            _________________________________________________________________________
              ''')
