import streamlit as st
import time, schedule
from datetime import datetime
from bot.config import logger, gclient, TZ
from bot.sheets import fetch_sheets
from bot.monitor import get_status_data
from bot.ai_messages import generate_messages_with_gemini
from bot.telegram_bot import send_messages

st.set_page_config(page_title="GEDAE Alerta Bot Telegram", page_icon="🤖", layout="wide")
st.title("GEDAE Alerta")

if st.text_input("Senha:", type="password") == st.secrets["senha"]["senha"]:
    logger.info("Senha correta. Iniciando monitoramento.")
    st.success("Robô iniciado!")

    last_admin_msg, last_group_msg = "", ""

    def job():
        nonlocal last_admin_msg, last_group_msg
        try:
            # Lê dados das planilhas
            target_sheet, source_sheet = fetch_sheets(
                gclient,
                st.secrets["lista_id_planilha"]["id_planilha"][0],
                st.secrets["lista_id_planilha"]["id_planilha"][1]
            )
            status = get_status_data(target_sheet, source_sheet)

            # Gera mensagens (IA + fallback)
            admin_msg, group_msg = generate_messages_with_gemini(status, last_admin_msg, last_group_msg)

            # Envia mensagens (regras de envio estão em telegram_bot.py)
            last_admin_msg, last_group_msg = send_messages(admin_msg, group_msg, last_admin_msg, last_group_msg)

        except Exception as e:
            logger.error(f"Erro no job: {e}")

    # Sincroniza com o segundo 0
    while True:
        now = datetime.now(TZ)
        if now.second == 0:
            break
        time.sleep(0.1)

    # Executa job a cada 1 minuto
    schedule.every(1).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

else:
    st.warning("Digite a senha!")
