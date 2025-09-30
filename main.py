import streamlit as st
import time, schedule
from datetime import datetime
from config import logger, gclient, TZ
from sheets import fetch_sheets
from monitor import get_status_data
from ai_messages import generate_messages_with_gemini
from telegram_bot import send_messages

st.set_page_config(page_title="GEDAE Alerta Bot Telegram", page_icon="🤖", layout="wide")
st.title("GEDAE Alerta")

if st.text_input("Senha:", type="password") == st.secrets["senha"]["senha"]:
    logger.info("Senha correta. Iniciando monitoramento.")
    st.success("Robô iniciado!")

    # Inicializa variáveis persistentes
    if "last_admin_msg" not in st.session_state:
        st.session_state.last_admin_msg = ""
    if "last_group_msg" not in st.session_state:
        st.session_state.last_group_msg = ""

    def job():
        try:
            target_sheet, source_sheet = fetch_sheets(
                gclient,
                st.secrets["lista_id_planilha"]["id_planilha"][0],
                st.secrets["lista_id_planilha"]["id_planilha"][1]
            )
            status = get_status_data(target_sheet, source_sheet)

            admin_msg, group_msg = generate_messages_with_gemini(
                status,
                st.session_state.last_admin_msg,
                st.session_state.last_group_msg
            )

            st.session_state.last_admin_msg, st.session_state.last_group_msg = send_messages(
                admin_msg, group_msg,
                st.session_state.last_admin_msg,
                st.session_state.last_group_msg
            )

        except Exception as e:
            logger.error(f"Erro no job: {e}")

    # Espera sincronizar no segundo 0
    while True:
        now = datetime.now(TZ)
        if now.second == 0:
            break
        time.sleep(0.1)

    # Executa a cada 1 minuto
    schedule.every(1).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

else:
    st.warning("Digite a senha!")
