import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

@st.cache_data
def PMPArranjoFV(Pmref, Iincref, Gama, Tcref, TNOC, Iinci, Tambi):
    Tci = Tambi + Iinci * (TNOC - 20) / 800 * 0.9
    Pmei = Pmref * (Iinci / Iincref) * (1 - Gama * (Tci - Tcref))
    return Pmei

@st.cache_data
def CalcPotSaidaINV(Pmei, PnInv, PmaxInv, k0, k1, k2):
    N = len(Pmei)
    Pmei = Pmei.tolist()
    Psaida, PperdasDC, Pperdas, p0 = [], [], [], []
    for i in range(N):
        Pmaximo = max(np.roots([k2, 1 + k1, k0 - Pmei[i] / PnInv])) * PnInv
        Psaida.append(Pmaximo)
        if Psaida[i] >= PmaxInv:
            PperdasDC.append(Psaida[i] - PmaxInv)  # Perdas de potência CC decorrentes da limitação e eficiência(W)
            Pperdas.append(PperdasDC[i] + (Pmei[i] - Psaida[i]))  # = (Pmei - PmaxInv)
            Psaida[i] = PmaxInv
        elif Pmei[i] <= k0:
            Psaida.append(0)
            PperdasDC.append(0)
            Pperdas.append(Pmei[i])
        else:
            PperdasDC.append(0)
            Pperdas.append(Pmei[i] - Psaida[i])
        p0.append(Psaida[i] / PnInv)
        # n_spmp = 0.98  n_spmp_20 = 0.93
        n_spmp = 1
        Psaida[i] = Psaida[i] * n_spmp
        # if Psaida[i] <= 0.2 * PmaxInv:
        # Psaida[i] = Psaida[i] * n_spmp_20
    Psaida = np.asarray(Psaida)
    p0 = np.asarray(p0)
    PperdasDC = np.asarray(PperdasDC)
    Pperdas = np.asarray(Pperdas)
    return Psaida, p0, PperdasDC, Pperdas

def calc_ger(Vmp, Voc, CVoc, Imax, Imp, Pmp, Tc, Tc_min, Tcref, FVImp, PnInv, sol_span_low, sol_span_high, FDI_interv, Yf_interp, calculo):
    resultados, resultado_maior_produtividade, YfxFDI, YfxFDI_new = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Calcula o número de módulos em série baseado na faixa de tensão admissível do inversor
    Voc_cor_safe = Voc * (1 - CVoc * (Tc_min - Tcref))
    Vmp_cor = Vmp * (1 - CVoc * (Tc - Tcref))

    N_mod_serie_sup = int(np.floor(max(FVImp) / Voc_cor_safe))
    N_mod_serie_inf = int(np.ceil(min(FVImp) / Vmp_cor))

    if N_mod_serie_inf == N_mod_serie_sup:
        N_mod_serie_faixa = [N_mod_serie_inf]
    else:
        N_mod_serie_faixa = list(range(N_mod_serie_inf, N_mod_serie_sup))

    # Calcula o número de módulos em paralelo baseado na corrente admissível pelo inversor
    N_mod_paralelo_sup = int(np.floor(Imax / Imp))
    N_mod_paralelo_faixa = list(range(1, N_mod_paralelo_sup + 1))

    # Faz a combinação das configurações admissíveis
    conf_acep_aux = []
    for x in range(len(N_mod_serie_faixa)):
        for y in range(len(N_mod_paralelo_faixa)):
            conf_acep_aux.append([N_mod_serie_faixa[x],
                                  N_mod_paralelo_faixa[y],
                                  N_mod_paralelo_faixa[y] * N_mod_serie_faixa[x],
                                  N_mod_paralelo_faixa[y] * N_mod_serie_faixa[x] * Pmp,
                                  PnInv / (N_mod_paralelo_faixa[y] * N_mod_serie_faixa[x] * Pmp)])
    conf_acep = conf_acep_aux

    conf_acep = [conf_acep[i] for i in range(len(conf_acep)) if sol_span_low < conf_acep[i][4] < sol_span_high]

    if conf_acep != []:
        ind_aux = []
        for x in range(len(conf_acep)):
            ind_aux.append(conf_acep[x][4])
        Prod_esti = Yf_interp(ind_aux)

        linha, valor = [], []
        for lin, val in enumerate(Prod_esti):
            linha.append(lin)
            valor.append(val)
        for z in range(len(conf_acep)):
            conf_acep[int(linha[z])].append(valor[z])

        Prod_max_write = [index for index, item in enumerate(conf_acep) if item[5] == max(valor)][0]
        ind_prod_max_calc = [index for index, item in enumerate(conf_acep) if item[5] == max(valor)][0]

        # Fazendo os cálculos com a informação do coeficiente de temperatura
        resultados = pd.DataFrame(conf_acep,
                                  columns=['NS[un]', 'NP[un]', 'NM[un]', 'PGER[W]', 'FDI', 'Yf[kWh/kWp]'])

        resultado_maior_produtividade = resultados[resultados['Yf[kWh/kWp]'] == max(resultados['Yf[kWh/kWp]'])]

        if calculo == 'FDI':
            YfxFDI = pd.DataFrame(zip(*[FDI_interv, Yf_interp(FDI_interv)]), columns=['FDI', 'Yf'])
            ind_FDI_new, FDI_new, Yf_new = [], [], []

            for x in range(len(conf_acep)):
                ind_FDI_new_vet = [linha for linha, elemento in enumerate(FDI_interv) if elemento >= conf_acep[x][4]]
                ind_FDI_new.append(ind_FDI_new_vet[0])
                FDI_new.append(FDI_interv[int(ind_FDI_new[x])])
                # Yf_new.append(Yf_interp(ind_FDI_new[x]))
                Yf_new.append(Yf_interp(FDI_new[x]))

            YfxFDI_new = pd.DataFrame(zip(*[FDI_new, Yf_new]), columns=['FDI', 'Yf'])

    return resultados, resultado_maior_produtividade, YfxFDI, YfxFDI_new