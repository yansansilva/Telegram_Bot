import time
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import schedule
import telebot
import pytz
import pandas as pd
from typing import Tuple, Optional

# Configurações iniciais
@st.cache_resource
def setup() -> Tuple[int, int, list, telebot.TeleBot, gspread.Client, str, str, pytz.timezone]:
    intervalo_tempo = 360  # 6 minutos
    referencia_consumo = 1350
    tz = pytz.timezone('America/Sao_Paulo')
    
    # Configuração do Telegram
    chave = st.secrets["lista_chave"]['list_key']
    bot = telebot.TeleBot(chave[0])
    chat_ids = [chave[1], chave[2]]
    
    # Autenticação Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account_3"], scopes=scope)
    client = gspread.authorize(creds)
    
    # IDs das planilhas
    planilha = st.secrets['lista_id_planilha']['id_planilha']
    source_id, target_id = planilha[0], planilha[1]
    
    return intervalo_tempo, referencia_consumo, chat_ids, bot, client, source_id, target_id, tz

# Função para acessar planilhas
@st.cache_data(ttl=60)
def fetch_sheets(client: gspread.Client, source_id: str, target_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    target_sheet = pd.DataFrame(client.open_by_key(target_id).sheet1.get_all_records())
    try:
        source_sheet = pd.DataFrame(client.open_by_key(source_id).sheet1.get_all_records())
    except:
        source_sheet = pd.DataFrame()
    return target_sheet, source_sheet

# Função para obter horários e consumo
def get_status_data(target_sheet: pd.DataFrame, source_sheet: pd.DataFrame, tz: pytz.timezone, 
                   intervalo_tempo: int, referencia_consumo: int) -> dict:
    now = datetime.now(tz)
    current_time = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Horários do RPi
    rpi_dates = pd.to_datetime(target_sheet['DATA-RPI']).dropna()
    last_rpi = rpi_dates.tail(1).iloc[0] if not rpi_dates.empty else None
    first_rpi = rpi_dates.head(1).iloc[0] if not rpi_dates.empty else None
    
    # Horários do PC
    pc_dates = pd.to_datetime(target_sheet['DATA-PC']).dropna()
    last_pc = pc_dates.tail(1).iloc[0] if not pc_dates.empty else None
    first_pc = pc_dates.head(1).iloc[0] if not pc_dates.empty else None
    
    # Consumo
    consumo = 0
    last_consumo_time = None
    if not source_sheet.empty:
        consumo_row = source_sheet[['Potência Ativa A', 'Potência Ativa B', 'Potência Ativa C']].tail(1)
        consumo = consumo_row.sum(axis=1).iloc[0] if not consumo_row.empty else 0
        last_consumo_time = pd.to_datetime(source_sheet['Hora']).dropna().tail(1).iloc[0] if 'Hora' in source_sheet else None
    
    # Status
    rpi_on = last_rpi and (now.timestamp() - last_rpi.timestamp() <= (300 if not last_pc else intervalo_tempo))
    pc_on = last_pc and (now.timestamp() - last_pc.timestamp() <= intervalo_tempo)
    consumo_alto = consumo > referencia_consumo
    
    return {
        'current_time': current_time,
        'last_rpi': last_rpi,
        'first_rpi': first_rpi,
        'last_pc': last_pc,
        'first_pc': first_pc,
        'consumo': consumo,
        'last_consumo_time': last_consumo_time,
        'rpi_on': rpi_on,
        'pc_on': pc_on,
        'consumo_alto': consumo_alto
    }

# Função para determinar mensagens
def determine_messages(status: dict, last_admin_msg: str, last_group_msg: str) -> Tuple[str, str]:
    rpi_on, pc_on, consumo_alto = status['rpi_on'], status['pc_on'], status['consumo_alto']
    first_rpi, first_pc, last_rpi, last_pc = status['first_rpi'], status['first_pc'], status['last_rpi'], status['last_pc']
    last_consumo_time = status['last_consumo_time']
    
    admin_msg, group_msg = last_admin_msg, last_group_msg
    
    if not pc_on:
        if rpi_on:
            admin_msg = "SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!"
            group_msg = f"O GEDAE ESTÁ ABERTO! Abriu às {first_rpi.time()} do dia {first_rpi.strftime('%d/%m/%Y')}."
        else:
            admin_msg = "PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!"
            group_msg = f"O GEDAE ESTÁ FECHADO! Fechou às {last_rpi.time()} do dia {last_rpi.strftime('%d/%m/%Y')}."
    else:
        cond_1 = not rpi_on and not pc_on and consumo_alto
        cond_2 = not pc_on and (rpi_on or consumo_alto)
        cond_3 = rpi_on or pc_on or consumo_alto
        
        if cond_3:
            if cond_1 and last_consumo_time and last_consumo_time.hour < 18:
                admin_msg = "PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA!"
                group_msg = "O GEDAE ESTÁ SEM ENERGIA!"
            elif cond_1:
                admin_msg = "PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA APÓS AS 18H00!"
                group_msg = f"O GEDAE ESTÁ FECHADO! Fechou às {max(last_rpi, last_pc).time()} do dia {max(last_rpi, last_pc).strftime('%d/%m/%Y')}."
            elif cond_2:
                admin_msg = "SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!"
                group_msg = "ENERGIA RESTABELECIDA NO GEDAE!"
            else:
                admin_msg = "O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!"
                menor_horario = min(first_rpi, first_pc)
                group_msg = f"O GEDAE ESTÁ ABERTO! Abriu às {menor_horario.time()} do dia {menor_horario.strftime('%d/%m/%Y')}."
        else:
            admin_msg = "PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!"
            group_msg = f"O GEDAE ESTÁ FECHADO! Fechou às {max(last_rpi, last_pc).time()} do dia {max(last_rpi, last_pc).strftime('%d/%m/%Y')}."
    
    return admin_msg, group_msg

# Função para enviar mensagens
def send_messages(bot: telebot.TeleBot, chat_ids: list, admin_msg: str, group_msg: str, 
                 last_admin_msg: str, last_group_msg: str):
    if admin_msg != last_admin_msg:
        bot.send_message(chat_id=chat_ids[0], text=admin_msg, timeout=150)
    if group_msg != last_group_msg:
        bot.send_message(chat_id=chat_ids[1], text=group_msg, timeout=150)

# Função principal de verificação
def check_system():
    global last_admin_msg, last_group_msg, execution_lock
    if not execution_lock:
        return
    execution_lock = False
    
    try:
        target_sheet, source_sheet = fetch_sheets(client, source_id, target_id)
        status = get_status_data(target_sheet, source_sheet, tz, intervalo_tempo, referencia_consumo)
        admin_msg, group_msg = determine_messages(status, last_admin_msg, last_group_msg)
        
        send_messages(bot, chat_ids, admin_msg, group_msg, last_admin_msg, last_group_msg)
        last_admin_msg, last_group_msg = admin_msg, group_msg
        
    except Exception as e:
        bot.send_message(chat_id=chat_ids[0], text=f"Erro: {str(e)}", timeout=150)

    execution_lock = True

# Configuração global
intervalo_tempo, referencia_consumo, chat_ids, bot, client, source_id, target_id, tz = setup()
last_admin_msg, last_group_msg = "", ""
execution_lock = True

# Interface Streamlit
if st.text_input('Senha: ', type="password") == st.secrets['senha']['senha']:
    # Sincroniza início nos minutos divisíveis por 5
    while True:
        now = datetime.now(tz)
        if now.minute % 5 == 0:
            break
        time.sleep(1)
    
    schedule.every(5).minutes.do(check_system)
    st.write("Robô iniciado!")
    
    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    st.write(' Digite a senha!')
