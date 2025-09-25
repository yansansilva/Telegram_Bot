import google.generativeai as genai
from bot.config import logger, GEMINI_STYLE
from bot.monitor import generate_messages  # fallback

def generate_messages_with_gemini(status: dict, last_admin_msg: str, last_group_msg: str):
    estilo = {
        "tecnico": "Use um tom técnico e detalhado, fornecendo dados precisos e recomendações práticas.",
        "informal": "Use um tom simples, amigável e fácil de entender.",
        "urgente": "Use um tom de alerta rápido e enfático, destacando riscos e ações imediatas."
    }.get(GEMINI_STYLE, "Use um tom neutro e claro.")

    prompt = f"""
    Você é um sistema de monitoramento de energia chamado GEDAE.
    Sua tarefa é gerar mensagens de alerta para o Telegram.

    Situação atual:
    - Raspberry Pi online: {status['rpi_on']}
    - PC online: {status['pc_on']}
    - Consumo atual: {status['consumo']} W
    - Consumo considerado alto: {status['consumo_alto']}
    - Última leitura de consumo: {status['last_consumo_time']}

    Estilo de escrita: {estilo}

    Gere DUAS mensagens:
    1. Para o ADMIN (detalhada, indicando ações quando necessário).
    2. Para o GRUPO (resumida e adaptada ao público geral).
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        if not response or not hasattr(response, "text"):
            raise ValueError("Resposta inválida do Gemini")

        text = response.text.strip()

        parts = text.split("\n", 1)
        admin_msg = parts[0].replace("1.", "").strip() if len(parts) > 0 else text
        group_msg = parts[1].replace("2.", "").strip() if len(parts) > 1 else text

        logger.info(f"Mensagens geradas com Gemini ({GEMINI_STYLE})")
        return admin_msg, group_msg

    except Exception as e:
        logger.error(f"Erro ao gerar mensagens com Gemini: {e}")
        return generate_messages(status, last_admin_msg, last_group_msg)
