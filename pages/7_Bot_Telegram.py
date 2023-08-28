import time
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import schedule
import telebot
import pytz
import pandas as pd

# Define o intervalo de tempo desejado em segundos
# intervalo_tempo = 70
intervalo_tempo = 90
referencia_consumo = 1350

# Configurações de autenticação do bot Telegram
chave = st.secrets["lista_chave"]['list_key']
bot_token = chave[0]
chat_id = [chave[1], chave[2]]

# Cria uma instância do bot Telegram
bot = telebot.TeleBot(bot_token)

# credenciais do serviço
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = st.secrets["gcp_service_account_3"]

# autenticação do serviço
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=SCOPE, )
client = gspread.authorize(creds)

# identificador das planilhas
planilha = st.secrets['lista_id_planilha']['id_planilha']
SOURCE_SPREADSHEET_ID = planilha[0]
TARGET_SPREADSHEET_ID = planilha[1]

# Fuso horário brasileiro
tz = pytz.timezone('America/Sao_Paulo')

def debugging_codigo(horario_atual, horario_ultima_linha_rpi, horario_ultima_linha_pc_debugging, consumo_ultima_linha,
                     rpi_on, pc_on, consumo_alto, condicao_1, condicao_2, condicao_3):
    print(f''' \n
            hora atual: {horario_atual} \n
            hora rpi: {horario_ultima_linha_rpi} \n
            hora pc: {horario_ultima_linha_pc_debugging} \n
            consumo: {consumo_ultima_linha} \n \n
            horario atual: {datetime.strptime(horario_atual, '%Y-%m-%d %H:%M:%S').timestamp()} : {datetime.now()} \n
            ultimo horario rpi: {horario_ultima_linha_rpi.timestamp()} \n
            ultimo horario pc: {horario_ultima_linha_pc_debugging} \n \n
            rpi_on: {rpi_on} \n
            pc_on: {pc_on} \n
            consumo_alto: {consumo_alto} \n \n
            Condição 1: {condicao_1} \n
            Condição 2: {condicao_2} \n
            Condição 3: {condicao_3} \n
            -----------------------------------------------------------------------------''')

# Função que verifica se já passou o intervalo de tempo definido e se houve novas linhas adicionadas na planilha
def verifica_planilha():
    global texto, garantir_execucao_unica
    time.sleep(15)
    if garantir_execucao_unica:
        try:
            source_sheet = pd.DataFrame(client.open_by_key(SOURCE_SPREADSHEET_ID).sheet1.get_all_records())
            target_sheet = pd.DataFrame(client.open_by_key(TARGET_SPREADSHEET_ID).sheet1.get_all_records())

            horario_atual = datetime.strftime(datetime.now().replace(tzinfo=pytz.utc).astimezone(tz),
                                              '%Y-%m-%d %H:%M:%S')
            horario_ultima_linha_rpi = pd.to_datetime(target_sheet['DATA-RPI']).dropna().tail(1).reset_index(drop=True)[
                0]
            try:
                horario_ultima_linha_pc = \
                pd.to_datetime(target_sheet['DATA-PC']).dropna().tail(1).reset_index(drop=True)[0]
                horario_ultima_linha_pc_debugging = horario_ultima_linha_pc.timestamp()
            except:
                horario_ultima_linha_pc_debugging = 'PC Desligado!'
            consumo_ultima_linha = \
            source_sheet[['Potência Ativa A', 'Potência Ativa B', 'Potência Ativa C']].tail(1).reset_index(
                drop=True).sum(axis=1)[0]
            hora_ultimo_consumo = pd.to_datetime(source_sheet['Hora']).dropna().tail(1).reset_index(drop=True)

            if horario_ultima_linha_pc_debugging == 'PC Desligado!':
                rpi_on = datetime.strptime(horario_atual,
                                           '%Y-%m-%d %H:%M:%S').timestamp() - horario_ultima_linha_rpi.timestamp() <= 300
            else:
                rpi_on = datetime.strptime(horario_atual,
                                           '%Y-%m-%d %H:%M:%S').timestamp() - horario_ultima_linha_rpi.timestamp() <= intervalo_tempo
            try:
                pc_on = datetime.strptime(horario_atual,
                                          '%Y-%m-%d %H:%M:%S').timestamp() - horario_ultima_linha_pc.timestamp() <= intervalo_tempo
                consumo_alto = consumo_ultima_linha > referencia_consumo
            except:
                pc_on = False
                consumo_alto = False

            condicao_1 = not rpi_on and not pc_on and consumo_alto
            condicao_2 = not pc_on and (rpi_on or consumo_alto)
            condicao_3 = rpi_on or pc_on or consumo_alto

            # Para debbuging do código
            debugging_codigo(horario_atual, horario_ultima_linha_rpi, horario_ultima_linha_pc_debugging, consumo_ultima_linha,
                             rpi_on, pc_on, consumo_alto, condicao_1, condicao_2, condicao_3)

            if horario_ultima_linha_pc_debugging == 'PC Desligado!':
                if rpi_on:
                    bot.send_message(chat_id=chat_id[0],
                                     text='SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!')
                    if texto != 'SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!':
                        texto = 'SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!'
                        bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ ABERTO!')
                else:
                    bot.send_message(chat_id=chat_id[0],
                                     text='PERDA DE CONEXÃO COM A INTERNET!')
                    if texto != 'PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!':
                        texto = 'PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!'
                        bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ FECHADO!')
            else:
                energia = 0
                if condicao_1:
                    energia = 1
                    # print('O GEDAE ESTÁ SEM ENERGIA!')
                elif condicao_2:
                    energia = 2
                    # print('HOUVE QUEDA DE ENERGIA NO GEDAE, RELIGUE O COMPUTADOR!')
                else:
                    # print('O GEDAE ESTÁ FUNCIONANDO NORMALMENTE!')
                    pass

                aberto = 1
                if condicao_3:
                    # print('O GEDAE ESTÁ ABERTO!')
                    pass
                else:
                    aberto = 0
                    # print('O GEDAE ESTÁ FECHADO!')

                if aberto == 1:
                    if energia == 0:
                        # print('O GEDAE ESTÁ ABERTO E TUDO ESTÁ FUNCIONANDO NORMALMENTE!')
                        bot.send_message(chat_id=chat_id[0], text='O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!')
                        if texto != 'O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!' or texto == 'SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!':
                            texto = 'O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!'
                            bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ ABERTO!')
                    elif energia == 1:
                        if hora_ultimo_consumo.dt.hour[0] < 18:
                            # print('O GEDAE ESTÁ SEM ENERGIA!')
                            bot.send_message(chat_id=chat_id[0],
                                             text='PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA!')
                            if texto != 'PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA!':
                                texto = 'PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA!'
                                bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ SEM ENERGIA!')
                        else:
                            # print('O GEDAE ESTÁ FECHADO!')
                            bot.send_message(chat_id=chat_id[0],
                                             text='PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA APÓS AS 18H00!')
                            if texto != 'PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA APÓS AS 18H00!':
                                texto = 'PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA APÓS AS 18H00!'
                                bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ FECHADO!')
                    elif energia == 2:
                        # print('O GEDAE ESTÁ ABERTO, MAS HOUVE QUEDA DE ENERGIA. RELIGUE O COMPUTADOR!')
                        bot.send_message(chat_id=chat_id[0],
                                         text='SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!')
                        if texto != 'SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!':
                            texto = 'SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!'
                            bot.send_message(chat_id=chat_id[1], text='ENERGIA RESTABELECIDA NO GEDAE!')
                else:
                    # print('O GEDAE ESTÁ FECHADO!')
                    bot.send_message(chat_id=chat_id[0], text='PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!')
                    if texto != 'PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!':
                        texto = 'PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!'
                        bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ FECHADO!')
        except:
            bot.send_message(chat_id=chat_id[0], text='LIMITE DE LEITURA POR MINUTO EXCEDIDO!')
            time.sleep(60 - datetime.now(tz).second)
            pass
        garantir_execucao_unica = False


#if st.button("Iniciar Robô"):
if st.text_input('Senha: ') == st.secrets['senha']['senha']:
    # agenda a execução da função a cada 1 minuto
    time.sleep(60 - datetime.now(tz).second)
    schedule.every(60).seconds.do(verifica_planilha)

    texto = ''
    # loop principal para executar o agendador de tarefas
    while True:
        garantir_execucao_unica = True
        schedule.run_pending()
else:
    st.write('Digite a senha!')
