import logging
import logging.handlers
import pytz
import telebot
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import google.generativeai as genai

# ===========================
# LOGGING
# ===========================
logger = logging.getLogger("GEDAE_Monitor")
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    "gedae_monitor.log", maxBytes=5*1024*1024, backupCount=3
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# ===========================
# CONFIGURAÇÕES GERAIS
# ===========================
INTERVALO_TEMPO = 360  # segundos para considerar ativo
REFERENCIA_CONSUMO = 1350
TZ = pytz.timezone("America/Sao_Paulo")

# ===========================
# TELEGRAM
# ===========================
TELEGRAM_TOKEN = st.secrets["general"]["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ADMIN_ID = st.secrets["general"]["TELEGRAM_ADMIN_ID"]
TELEGRAM_GROUP_ID = st.secrets["general"]["TELEGRAM_GROUP_ID"]

bot = telebot.TeleBot(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

# ===========================
# GOOGLE SHEETS
# ===========================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Já vem como dict do Streamlit Secrets (sem precisar eval/json.loads)
SERVICE_ACCOUNT_INFO = st.secrets["general"]["GCP_SERVICE_ACCOUNT_JSON"]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gclient = gspread.authorize(creds)

# ===========================
# GEMINI
# ===========================
GEMINI_API_KEY = st.secrets["general"]["GEMINI_API_KEY"]
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GEMINI_STYLE = st.secrets["general"].get("GEMINI_STYLE", "tecnico")
