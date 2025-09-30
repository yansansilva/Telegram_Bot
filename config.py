import logging
import logging.handlers
import pytz
import telebot
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import google.generativeai as genai

# Setup logging
logger = logging.getLogger("GEDAE_Monitor")
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    "gedae_monitor.log", maxBytes=5*1024*1024, backupCount=3
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Configurações gerais
INTERVALO_TEMPO = 360  # segundos
REFERENCIA_CONSUMO = 1350
TZ = pytz.timezone("America/Sao_Paulo")

# Telegram
TELEGRAM_TOKEN = st.secrets["general"]["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ADMIN_ID = st.secrets["general"]["TELEGRAM_ADMIN_ID"]
TELEGRAM_GROUP_ID = st.secrets["general"]["TELEGRAM_GROUP_ID"]
bot = telebot.TeleBot(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

# Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_INFO = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]

print(SERVICE_ACCOUNT_INFO)

creds = Credentials.from_service_account_info(eval(SERVICE_ACCOUNT_INFO), scopes=SCOPES)
gclient = gspread.authorize(creds)

# Gemini
GEMINI_API_KEY = st.secrets["general"]["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_STYLE = st.secrets["general"].get("GEMINI_STYLE", "tecnico")
