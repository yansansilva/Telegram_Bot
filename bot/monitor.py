from datetime import datetime
import pandas as pd
from bot.config import logger, TZ, INTERVALO_TEMPO, REFERENCIA_CONSUMO

def get_status_data(target_sheet, source_sheet):
    now = datetime.now(TZ)

    # Datas
    rpi_dates = pd.to_datetime(target_sheet.get("DATA-RPI", []), errors="coerce").dropna()
    pc_dates  = pd.to_datetime(target_sheet.get("DATA-PC", []), errors="coerce").dropna()

    last_rpi = rpi_dates.max() if not rpi_dates.empty else None
    last_pc  = pc_dates.max() if not pc_dates.empty else None

    # Consumo
    consumo, last_consumo_time = 0, None
    if not source_sheet.empty:
        consumo_row = source_sheet[["Potência Ativa A", "Potência Ativa B", "Potência Ativa C"]].tail(1)
        consumo = consumo_row.sum(axis=1).iloc[0] if not consumo_row.empty else 0
        if "Hora" in source_sheet:
            last_consumo_time = pd.to_datetime(source_sheet["Hora"]).dropna().tail(1).iloc[0]

    return {
        "now": now,
        "last_rpi": last_rpi,
        "last_pc": last_pc,
        "consumo": consumo,
        "last_consumo_time": last_consumo_time,
        "rpi_on": last_rpi and (now.timestamp() - last_rpi.timestamp() <= INTERVALO_TEMPO),
        "pc_on": last_pc and (now.timestamp() - last_pc.timestamp() <= INTERVALO_TEMPO),
        "consumo_alto": consumo > REFERENCIA_CONSUMO,
    }

def generate_messages(status, last_admin_msg, last_group_msg):
    rpi_on, pc_on, consumo, consumo_alto = status["rpi_on"], status["pc_on"], status["consumo"], status["consumo_alto"]
    now = status["now"]

    admin_msg, group_msg = last_admin_msg, last_group_msg

    if not rpi_on and not pc_on:
        if consumo_alto:
            admin_msg = f"⚠️ Alerta: Nenhuma conexão detectada às {now:%H:%M}, mas consumo alto ({consumo}W)."
            group_msg = "Problema detectado: sem conexão, mas consumo alto."
        else:
            admin_msg = f"Sem conexão desde {now:%H:%M}, consumo baixo ({consumo}W). Provavelmente fechado."
            group_msg = f"GEDAE fechado às {now:%H:%M}."
    elif rpi_on and not pc_on:
        admin_msg = f"Apenas Raspberry conectado às {now:%H:%M}. PC offline."
        group_msg = "Problema no PC detectado."
    else:
        admin_msg = f"Sistema ok às {now:%H:%M}. RPi: {rpi_on}, PC: {pc_on}, Consumo: {consumo}W."
        group_msg = "GEDAE aberto e funcionando."

    return admin_msg, group_msg
