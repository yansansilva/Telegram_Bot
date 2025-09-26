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

    # Inicializa variáveis de estado persistentes no Streamlit
    if "last_admin_msg" not in st.session_state:
        st.session_state.last_admin_msg = ""
    if "last_group_msg" not in st.session_state:
        st.session_state.last_group_msg = ""

    def job():
        try:
            # Lê dados das planilhas
            target_sheet, source_sheet = fetch_sheets(
                gclient,
                st.secrets["lista_id_planilha"]["id_planilha"][0],
                st.secrets["lista_id_planilha"]["id_planilha"][1]
            )
            status = get_status_data(target_sheet, source_sheet)

            # Gera mensagens (IA + fallback fixo)
            admin_msg, group_msg = generate_messages_with_gemini(
                status,
                st.session_state.last_admin_msg,
                st.session_state.last_group_msg
            )

            # Envia mensagens
            st.session_state.last_admin_msg, st.session_state.last_group_msg = send_messages(
                admin_msg, group_msg,
                st.session_state.last_admin_msg,
                st.session_state.last_group_msg
            )

        except Exception as e:
            logger.error(f"Erro no job: {e}")

    # Sincroniza com o segundo 0 antes de iniciar
    while True:
        now = datetime.now(TZ)
        if now.second == 0:
            break
        time.sleep(0.1)

    # Executa job a cada 1 minuto
    schedule.every(1).minutes.do(job)

    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(1)

else:
    st.warning("Digite a senha!")
