import streamlit as st

@st.cache_data
def extrair_dados_modulos(dados_modulo, modulo, modo):
    ## Características elétricas
    Pmp = dados_modulo[modulo]['Pmp']  # Potência elétrica máxima
    Imp = dados_modulo[modulo]['Imp']  # Corrente na máxima potência
    Vmp = dados_modulo[modulo]['Vmp']  # tensão na máxima potência
    Isc = dados_modulo[modulo]['Isc']  # Corrente de curto - circuito
    Voc = dados_modulo[modulo]['Voc']  # Tensão de circuito aberto

    ## parâmetros térmicos
    TNOC = dados_modulo[modulo]['TNOC']  # Temperatura de operação da célula
    CIsc = dados_modulo[modulo][
               'Coef. Temp. I (%)'] / 100  # Coeficiente de temperatura de Isc(Não está expresso em porcentagem)
    CVoc = dados_modulo[modulo][
               'Coef. Temp. V (%)'] / 100  # Coeficiente de temperatura de Voc(Não está expresso em porcentagem)
    Gama = dados_modulo[modulo][
               'Coef. Temp. P (%)'] / 100  # Coeficiente de temperatura do ponto de máxima potência do módulo fotovoltaico

    if modo == 'Energia':
        ## Arranjo do Sistema Fotovoltaico
        N_mod_serie = int(dados_modulo[modulo]['Nº de módulos série'])
        N_mod_paralelo = int(dados_modulo[modulo]['Nº de módulos paralelo'])

        return Pmp, Imp, Vmp, Isc, Voc, TNOC, CIsc, CVoc, Gama, N_mod_serie, N_mod_paralelo

    else:

        return Pmp, Imp, Vmp, Isc, Voc, TNOC, CIsc, CVoc, Gama


def extrair_dados_inversores(dados_inversor, inversor):
    ## Características do Inversor
    PnInv = dados_inversor[inversor]['PnInv']  # Potência elétrica nominal
    Pmax = dados_inversor[inversor]['Pmax']  # Potência elétrica máxima de saída
    FVImp = [dados_inversor[inversor]['Vmp_inp_inf'],
             dados_inversor[inversor]['Vmp_inp_sup']]  # Faixa de tensão na entrada na máxima potência[Vmin Vmax]
    Vioc = dados_inversor[inversor]['Vmax']  # tensão máxima de entrada sem carga
    Imax = dados_inversor[inversor]['I_max']  # corrente máxima de entrada

    PmaxInv = dados_inversor[inversor]['Pmax']  # Leitura da potência máxima na tabela 'CaracTecInversores'
    EficInv10 = dados_inversor[inversor]['η10% (%)']  # Leitura da eficiência a 10 % da carga
    EficInv50 = dados_inversor[inversor]['η50% (%)']  # Leitura da eficiência a 50 % da carga
    EficInv100 = dados_inversor[inversor]['η100% (%)']  # Leitura da eficiência a 100 % da carga

    return PnInv, Pmax, FVImp, Vioc, Imax, PmaxInv, EficInv10, EficInv50, EficInv100