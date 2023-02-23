import streamlit as st
import pandas as pd
import numpy as np
from scipy import optimize
import plotly.graph_objects as go
from ImportarArquivos import import_from_GoogleDrive

st.set_page_config(
    page_title="GEDAE Aplicativos - Curva IxV",
    page_icon="👋",
    layout="wide"
)

st.title("Curva IxV")

importar_dados = st.radio('Parâmetros do Módulo Fotovoltaico',
                          ('Digitar',
                           'Importar própria base de dados',
                           'Importar base de dados do servidor'),
                          horizontal=True)
st.write(f'''
    _________________________________________________________________________
        ''')
Pmp, Imp, Vmp, Isc, Voc, CIsc, CVoc = [0, 0, 0, 0, 0, 0, 0]

modulo = ''
if importar_dados != 'Digitar':
    st.write('### Importe os dados dos módulos fotovoltaicos')
    if importar_dados == 'Importar própria base de dados':
        arquivo_modulos = st.file_uploader('Dados dos módulos', type=['XLS', 'XLSX'])
        if arquivo_modulos is not None:
            dados_modulo = pd.read_excel(arquivo_modulos, sheet_name=0,
                                     index_col=0)  # Características do módulo fotovoltaico
            st.write('### Selecione o módulo fotovoltaico')
            modulo = st.selectbox('Módulo', dados_modulo.columns)
    elif importar_dados == 'Importar base de dados do servidor':
        dados_modulo, dados_inversor, dados_ambiente = import_from_GoogleDrive()
        st.write('### Selecione o módulo fotovoltaico')
        modulo = st.selectbox('Módulo', dados_modulo.columns)
    if modulo != '':
        if st.checkbox('Mostrar Dados do Módulo'):
            st.dataframe(dados_modulo[modulo])

        ## Características elétricas
        Pmp = dados_modulo[modulo]['Pmp']  # Potência elétrica máxima
        Imp = dados_modulo[modulo]['Imp']  # Corrente na máxima potência
        Vmp = dados_modulo[modulo]['Vmp']  # tensão na máxima potência
        Isc = dados_modulo[modulo]['Isc']  # Corrente de curto - circuito
        Voc = dados_modulo[modulo]['Voc']  # Tensão de circuito aberto

        ## parâmetros térmicos
        CIsc = dados_modulo[modulo][
                   'Coef. Temp. I (%)'] / 100  # Coeficiente de temperatura de Isc(Não está expresso em porcentagem)
        CVoc = dados_modulo[modulo][
                   'Coef. Temp. V (%)'] / 100  # Coeficiente de temperatura de Voc(Não está expresso em porcentagem)
else:
    st.write('### Digite os dados dos módulos fotovoltaicos')

    modulo = st.text_input('Modelo do módulo', value='')

    coluna1, coluna2, coluna3 = st.columns((2, 2, 1))

    coluna1.write('## Parâmetros elétricos')
    Pmp = coluna1.number_input('Pmp: ', min_value=0)  # Potência elétrica máxima
    Imp = coluna1.number_input('Imp: ', min_value=0.0)  # Corrente na máxima potência
    Vmp = coluna1.number_input('Vmp: ', min_value=0.0)  # tensão na máxima potência
    Isc = coluna1.number_input('Isc: ', min_value=0.0)  # Corrente de curto - circuito
    Voc = coluna1.number_input('Voc: ', min_value=0.0)  # Tensão de circuito aberto

    coluna2.write('## Parâmetros térmicos')
    CIsc = coluna2.number_input('CIsc: ', min_value=0.0, step=0.001, format="%.3f")/100    # Coeficiente de temperatura de Isc(Não está expresso em porcentagem)
    CVoc = coluna2.number_input('CVoc: ', max_value=0.0, step=0.001, format="%.3f")/100    # Coeficiente de temperatura de Voc(Não está expresso em porcentagem)


if Pmp != 0 and Imp != 0 and Vmp != 0 and Isc != 0 and Voc != 0 and CIsc != 0 and CVoc != 0:
    # --------------------------------------------------------------------------------------
    # Parâmetros nas condições STC
    Irradiancia_referencia = 1000
    Tac = 25
    # --------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------

    st.write('### Parâmetros ajustáveis para Curva I-V')

    coluna1, coluna2, coluna3 = st.columns((1, 1, 2))
    coluna1.markdown('''___''')
    coluna2.markdown('''___''')

    Irradiancia = coluna1.number_input('Irradiância: ', value=1000)
    Temperatura_costa_modulo = coluna2.number_input('Temperatura de costa do modulo: ', value=25.0)
    Resistencia_serie = coluna1.number_input('Resistência serie: ', min_value=0.0, step=0.001, format="%.3f")
    Resistencia_paralelo = coluna2.number_input('Resistência paralelo: ', min_value=1, value=1000000)
    Numero_celulas_serie = coluna1.number_input('Número de células em série: ', min_value=1, value=60)
    Fator_de_idealidade = coluna2.slider('Fator de idealidade: ', min_value=1.0, max_value=2.0)

    S = Irradiancia / Irradiancia_referencia
    Tc = Temperatura_costa_modulo
    Rs = Resistencia_serie
    Rp = Resistencia_paralelo
    # --------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------
    # Dados de Catálogo
    Ns = Numero_celulas_serie
    Voc_Tjref = Voc / Ns
    Isc_Tjref = Isc
    ALFA = CIsc
    BETA = CVoc
    # --------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------
    # Constantes
    q = 1.6E-19
    k = 1.38E-23
    n = Fator_de_idealidade
    Eg = 1.12
    Tjref = 273 + Tac
    # --------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------
    # Atribuindo os valores para Tensão de Módulo, Tensão de Célula e de Corrente
    Va = np.linspace(0, Voc, 255)
    Vc = np.linspace(0, Voc, 255) / Ns
    # --------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------
    # Cálculos
    Tak = Tjref
    Tj = 273 + Tc

    Voc_Tj = Voc_Tjref * (1 + BETA * (Tj - Tjref))
    Isc_Tj = Isc_Tjref * (1 + ALFA * (Tj - Tjref))

    Vt_Ta = n * k * Tjref / q

    Iph_Tjref = Isc_Tj * S
    Iph = Iph_Tjref + ALFA * (Tj - Tjref)
    Io_Tjref = Isc_Tj / (np.exp(Voc_Tj / Vt_Ta) - 1)
    Io = Io_Tjref * (Tak / Tjref) ** (3 / n) * np.exp(-q * Eg / (n * k) * ((1 / Tak) - (1 / Tjref)))

    # --------------------------------------------------------------------------------------
    # Método de Newton
    f = lambda I, Vc: Iph - I - Io * (np.exp((Vc + I * Rs) / Vt_Ta) - 1) - (Vc + I * Rs) / Rp
    fder = lambda I, Vc: - 1 - (Io * (np.exp((Vc + I * Rs) / Vt_Ta) - 1)) * Rs / Vt_Ta - Rs / Rp
    I = [0 for x in range(len(Vc))]
    I_res = optimize.newton(f, I, fprime=fder, args=(Vc,), maxiter=100)
    # --------------------------------------------------------------------------------------

    resultado = pd.DataFrame(zip(*[I_res, Va]), columns=['I_res', 'Va'])

    importar_curva_medida = st.checkbox('Plotar curva IxV medida')
    curva_medida = pd.DataFrame()
    if importar_curva_medida:
        st.write('#### Importe a curva IxV medida:')
        arquivo_curva_medida = st.file_uploader('Curva IxV medida', type=['XLS', 'XLSX'])
        if arquivo_curva_medida is not None:
            curva_medida = pd.read_excel(arquivo_curva_medida)

    fig = go.Figure()
    fig.add_trace(go.Line(x=resultado[resultado['I_res'] >= 0]['Va'],
                          y=resultado[resultado['I_res'] >= 0]['I_res']))

    if not curva_medida.empty:
        fig.add_trace(go.Line(x=curva_medida['V'],
                              y=curva_medida['I']))

    fig.update_layout(
        title=f'Curva IxV: {modulo}',
        title_x=0.5,
        title_y=0.85,
        xaxis_title='Tensão do módulo (V)',
        yaxis_title='Corrente do módulo (A)',
        font=dict(
            family="Courier New, monospace",
            size=12,
            color="RebeccaPurple"
        ),
        showlegend=False,
        width=700, height=400
    )

    coluna3.plotly_chart(fig)
    # --------------------------------------------------------------------------------------
