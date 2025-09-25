import streamlit as st

st.set_page_config(
    page_title="GEDAE Alerta Bot Telegram",
    page_icon="👋",
    layout="wide"
)

st.title("GEDAE Alerta")

st.markdown(
    """
    [FASE DE TESTES INICIAIS: COLOCAR TEXTO DEPOIS]
"""
)

import time
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import schedule
import telebot
import pytz
import pandas as pd
import logging
import logging.handlers
from typing import Tuple, Optional

# Configurações iniciais
@st.cache_resource
def setup() -> Tuple[int, int, list, telebot.TeleBot, gspread.Client, str, str, pytz.timezone]:
    # Configurar logging
    logger = logging.getLogger('GEDAE_Monitor')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        'gedae_monitor.log', maxBytes=5*1024*1024, backupCount=3
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    logger.info("Iniciando configuração do script")
    
    intervalo_tempo = 360  # 6 minutos
    referencia_consumo = 1350
    tz = pytz.timezone('America/Sao_Paulo')
    
    # Configuração do Telegram
    try:
        chave = st.secrets["lista_chave"]['list_key']
        bot = telebot.TeleBot(chave[0])
        chat_ids = [chave[1], chave[2]]
        logger.info("Autenticação com Telegram bem-sucedida")
    except Exception as e:
        logger.error(f"Falha na autenticação com Telegram: {str(e)}")
        raise
    
    # Autenticação Google Sheets
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account_3"], scopes=scope)
        client = gspread.authorize(creds)
        logger.info("Autenticação com Google Sheets bem-sucedida")
    except Exception as e:
        logger.error(f"Falha na autenticação com Google Sheets: {str(e)}")
        raise
    
    # IDs das planilhas
    try:
        planilha = st.secrets['lista_id_planilha']['id_planilha']
        source_id, target_id = planilha[0], planilha[1]
        logger.info("IDs das planilhas carregados com sucesso")
    except Exception as e:
        logger.error(f"Falha ao carregar IDs das planilhas: {str(e)}")
        raise
    
    return intervalo_tempo, referencia_consumo, chat_ids, bot, client, source_id, target_id, tz

# Função para acessar planilhas
@st.cache_data(ttl=60)
def fetch_sheets(_client: gspread.Client, source_id: str, target_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    logger = logging.getLogger('GEDAE_Monitor')
    logger.debug(f"Acessando planilhas: source_id={source_id}, target_id={target_id}")
    
    try:
        target_sheet = pd.DataFrame(_client.open_by_key(target_id).sheet1.get_all_records())
        logger.debug("Planilha de destino (target) acessada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao acessar planilha de destino: {str(e)}")
        raise
    
    try:
        source_sheet = pd.DataFrame(_client.open_by_key(source_id).sheet1.get_all_records())
        logger.debug("Planilha de origem (source) acessada com sucesso")
    except Exception as e:
        logger.warning(f"Erro ao acessar planilha de origem: {str(e)}. Retornando DataFrame vazio.")
        source_sheet = pd.DataFrame()
    
    return target_sheet, source_sheet

# Função para obter horários e consumo
def get_status_data(target_sheet: pd.DataFrame, source_sheet: pd.DataFrame, tz: pytz.timezone, 
                   intervalo_tempo: int, referencia_consumo: int) -> dict:
    logger = logging.getLogger('GEDAE_Monitor')
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
    
    logger.debug(
        f"Status do sistema: RPi_on={rpi_on}, PC_on={pc_on}, Consumo={consumo}W, "
        f"Consumo_alto={consumo_alto}, Current_time={current_time}"
    )
    
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

# Função para gerar mensagens com IA simulada
def generate_messages_with_ai(status: dict, last_admin_msg: str, last_group_msg: str) -> Tuple[str, str]:
    logger = logging.getLogger('GEDAE_Monitor')
    
    rpi_on = status['rpi_on']
    pc_on = status['pc_on']
    consumo_alto = status['consumo_alto']
    consumo = status['consumo']
    first_rpi = status['first_rpi']
    last_rpi = status['last_rpi']
    first_pc = status['first_pc']
    last_pc = status['last_pc']
    last_consumo_time = status['last_consumo_time']
    current_time = datetime.strptime(status['current_time'], '%Y-%m-%d %H:%M:%S')
    
    # Inicializa mensagens
    admin_msg = last_admin_msg
    group_msg = last_group_msg
    
    # Análise contextual (simulando IA)
    if not rpi_on and not pc_on:
        # Sistema provavelmente offline
        if consumo_alto:
            # Alto consumo sem conexão sugere problema
            admin_msg = f"Alerta: Nenhuma conexão detectada (RPi e PC offline) às {current_time.strftime('%H:%M')}, mas o consumo está elevado ({consumo}W). Verifique o GEDAE imediatamente."
            group_msg = "Problema detectado: GEDAE sem conexão, mas com consumo alto. Equipe notificada."
        else:
            # Baixo consumo e sem conexão sugere fechamento
            last_time = max(last_rpi, last_pc) if last_rpi and last_pc else (last_rpi or last_pc)
            admin_msg = f"Sem conexão com RPi ou PC desde {last_time.strftime('%H:%M')} e consumo baixo ({consumo}W). GEDAE provavelmente fechado."
            group_msg = f"GEDAE fechado às {last_time.strftime('%H:%M')} do dia {last_time.strftime('%d/%m/%Y')}."
    
    elif rpi_on and not pc_on:
        # Apenas RPi online
        admin_msg = f"Aviso: Apenas o Raspberry Pi está conectado às {current_time.strftime('%H:%M')}. O PC está offline. Consumo atual: {consumo}W. Religar o PC."
        group_msg = f"GEDAE aberto desde {first_rpi.strftime('%H:%M')} de {first_rpi.strftime('%d/%m/%Y')}. Problema no PC detectado, equipe notificada."
    
    else:
        # PC online (e possivelmente RPi)
        if consumo_alto and last_consumo_time:
            if last_consumo_time.hour < 18:
                # Alto consumo antes das 18h sugere problema
                admin_msg = f"Alerta: Consumo elevado ({consumo}W) detectado às {current_time.strftime('%H:%M')}, com RPi {'online' if rpi_on else 'offline'} e PC online. Verificar possível sobrecarga."
                group_msg = "GEDAE ativo, mas com consumo anormalmente alto. Equipe verificando."
            else:
                # Alto consumo após 18h sugere fechamento
                last_time = max(last_rpi, last_pc) if last_rpi and last_pc else (last_rpi or last_pc)
                admin_msg = f"Consumo elevado ({consumo}W) após 18h às {current_time.strftime('%H:%M')}. GEDAE possivelmente fechado. Última conexão às {last_time.strftime('%H:%M')}."
                group_msg = f"GEDAE fechado às {last_time.strftime('%H:%M')} do dia {last_time.strftime('%d/%m/%Y')}."
        else:
            # Tudo normal
            first_time = min(first_rpi, first_pc) if first_rpi and first_pc else (first_rpi or first_pc)
            admin_msg = f"Sistema funcionando normalmente às {current_time.strftime('%H:%M')}. RPi: {'online' if rpi_on else 'offline'}, PC: online, Consumo: {consumo}W."
            group_msg = f"GEDAE aberto desde {first_time.strftime('%H:%M')} de {first_time.strftime('%d/%m/%Y')}."
    
    logger.debug(f"Mensagens geradas - Admin: {admin_msg}, Grupo: {group_msg}")
    return admin_msg, group_msg

# Função para enviar mensagens
def send_messages(bot: telebot.TeleBot, chat_ids: list, admin_msg: str, group_msg: str, 
                 last_admin_msg: str, last_group_msg: str):
    logger = logging.getLogger('GEDAE_Monitor')
    
    if admin_msg != last_admin_msg:
        try:
            bot.send_message(chat_id=chat_ids[0], text=admin_msg, timeout=150)
            logger.info(f"Mensagem enviada para admin: {admin_msg}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para admin: {str(e)}")
    
    if group_msg != last_group_msg:
        try:
            bot.send_message(chat_id=chat_ids[1], text=group_msg, timeout=150)
            logger.info(f"Mensagem enviada para grupo: {group_msg}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para grupo: {str(e)}")

# Função principal de verificação
def check_system():
    logger = logging.getLogger('GEDAE_Monitor')
    logger.debug("Iniciando verificação do sistema")
    
    global last_admin_msg, last_group_msg, execution_lock
    if not execution_lock:
        logger.warning("Execução bloqueada devido a execution_lock")
        return
    execution_lock = False
    
    try:
        target_sheet, source_sheet = fetch_sheets(client, source_id, target_id)
        status = get_status_data(target_sheet, source_sheet, tz, intervalo_tempo, referencia_consumo)
        admin_msg, group_msg = generate_messages_with_ai(status, last_admin_msg, last_group_msg)
        
        send_messages(bot, chat_ids, admin_msg, group_msg, last_admin_msg, last_group_msg)
        last_admin_msg, last_group_msg = admin_msg, group_msg
        logger.debug("Verificação do sistema concluída com sucesso")
        
    except Exception as e:
        logger.error(f"Erro durante verificação do sistema: {str(e)}", exc_info=True)
        bot.send_message(chat_id=chat_ids[0], text=f"Erro: {str(e)}", timeout=150)

    execution_lock = True

# Configuração global
try:
    intervalo_tempo, referencia_consumo, chat_ids, bot, client, source_id, target_id, tz = setup()
    last_admin_msg, last_group_msg = "", ""
    execution_lock = True
except Exception as e:
    logging.getLogger('GEDAE_Monitor').error(f"Falha na inicialização global: {str(e)}", exc_info=True)
    raise

# Interface Streamlit
if st.text_input('Senha: ', type="password") == st.secrets['senha']['senha']:
    logger = logging.getLogger('GEDAE_Monitor')
    logger.info("Senha correta inserida, iniciando sincronização")
    
    # Sincroniza início no próximo segundo 00
    while True:
        now = datetime.now(tz)
        if now.second == 0:
            logger.info(f"Sincronizado no segundo 00: {now.strftime('%H:%M:%S')}")
            break
        time.sleep(0.1)  # Checa a cada 0.1 segundo para maior precisão
    
    schedule.every(5).minutes.do(check_system)
    st.write("Robô iniciado!")
    logger.info("Robô iniciado, agendamento configurado")
    
    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    st.write('Digite a senha!')
    logging.getLogger('GEDAE_Monitor').warning("Senha incorreta ou não inserida")

