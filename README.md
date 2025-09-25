# 🤖 GEDAE Telegram Bot

Bot de monitoramento para o GEDAE que:
- Lê dados do **Google Sheets** (produção, consumo, horários).
- Analisa o status do sistema (**RPi**, **PC**, **Consumo**).
- Envia mensagens automáticas para **Telegram** (Admin e Grupo).
- Usa **IA (Gemini)** para gerar mensagens inteligentes, com **fallback** para regras fixas.
- Interface simples via **Streamlit** (com autenticação por senha).

---

## 📂 Estrutura do projeto

Telegram_Bot/
│
├── bot/
│   ├── __init__.py
│   ├── main.py          # script principal
│   ├── config.py        # tokens e configs
│   ├── handlers.py      # comandos e respostas
│   └── utils.py         # funções auxiliares
│
├── requirements.txt
├── .env                 # TELEGRAM_BOT_TOKEN=seu_token_aqui
└── README.md



---

## ⚙️ Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/Telegram_Bot.git
cd Telegram_Bot

2. Crie um ambiente virtual

python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

3. Instale dependências

pip install -r requirements.txt

------------------------------------------------------------------------
🔑 Configuração do .env

Crie um arquivo chamado .env na raiz do projeto:

# Telegram
TELEGRAM_BOT_TOKEN=seu_token_telegram
TELEGRAM_ADMIN_ID=123456789
TELEGRAM_GROUP_ID=-987654321

# Google Sheets (JSON do service account)
GCP_SERVICE_ACCOUNT_JSON={"type": "...", "project_id": "...", ...}

# Gemini
GEMINI_API_KEY=sua_chave_gemini
GEMINI_STYLE=tecnico


🔹 GEMINI_STYLE pode ser:

tecnico → mensagens detalhadas e formais
informal → mensagens amigáveis e simples
urgente → mensagens de alerta direto e enfático

------------------------------------------------------------------------
▶️ Execução local

1. Inicie o Streamlit

streamlit run bot/main.py

2. Acesse a interface

Abra http://localhost:8501 no navegador.
Digite a senha (definida em st.secrets['senha']['senha']) para iniciar o robô.

🤖 Funcionamento

2.1. O bot autentica no Google Sheets e no Telegram.

2.2. A cada 5 minutos:

Lê dados das planilhas.

Calcula status do sistema.

Gera mensagens (IA com Gemini → fallback em regras fixas).

Envia para Admin e Grupo no Telegram.

-------------------------------------
🧪 Exemplo de mensagens:

🔹 Estilo Técnico
Admin: Sistema normal às 14:32. RPi online, PC online, consumo 820W (ok).
Grupo: GEDAE funcionando normalmente desde as 08:00.

🔹 Estilo Urgente
Admin: 🚨 Consumo anormal às 17:40 → 2150W! Verificação imediata necessária.
Grupo: ⚠️ GEDAE com consumo muito alto! Equipe avisada.

------------------------------------------------------------------------
🚀 Deploy online (opcional)

Você pode rodar este bot:
- Streamlit Cloud (grátis, mas hiberna após inatividade).
- Render / Railway (hospedagem de apps Python).
- VPS (Linux) com systemd ou Docker.

------------------------------------------------------------------------
📦 Dependências principais

Streamlit
 – interface web

gspread
 – acesso Google Sheets

pyTelegramBotAPI
 – Telegram

schedule
 – agendador

google-generativeai
 – Gemini IA

pandas
 – manipulação de dados

------------------------------------------------------------------------
✨ Autor

Projeto desenvolvido pelo GEDAE/UFPA ⚡
