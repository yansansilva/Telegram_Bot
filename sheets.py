import pandas as pd
from config import logger

def fetch_sheets(client, source_id: str, target_id: str):
    logger.debug(f"Acessando planilhas: source={source_id}, target={target_id}")

    try:
        target_sheet = pd.DataFrame(client.open_by_key(target_id).sheet1.get_all_records())
    except Exception as e:
        logger.error(f"Erro ao acessar planilha target: {e}")
        raise

    try:
        source_sheet = pd.DataFrame(client.open_by_key(source_id).sheet1.get_all_records())
    except Exception as e:
        logger.warning(f"Erro ao acessar planilha source: {e}")
        source_sheet = pd.DataFrame()

    return target_sheet, source_sheet
