from bot.config import bot, TELEGRAM_ADMIN_ID, TELEGRAM_GROUP_ID, logger

def send_messages(admin_msg, group_msg, last_admin_msg, last_group_msg):
    if not bot:
        logger.error("Bot não configurado. Verifique TELEGRAM_BOT_TOKEN.")
        return last_admin_msg, last_group_msg

    if admin_msg != last_admin_msg:
        try:
            bot.send_message(chat_id=TELEGRAM_ADMIN_ID, text=admin_msg, timeout=150)
            logger.info(f"Mensagem enviada ao admin: {admin_msg}")
        except Exception as e:
            logger.error(f"Erro ao enviar ao admin: {e}")

    if group_msg != last_group_msg:
        try:
            bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=group_msg, timeout=150)
            logger.info(f"Mensagem enviada ao grupo: {group_msg}")
        except Exception as e:
            logger.error(f"Erro ao enviar ao grupo: {e}")

    return admin_msg, group_msg
