import requests
import logging
import os

from dotenv import load_dotenv
from Carpeta.rutas import obtener_imagenes_error

load_dotenv("/app/variables.env")

# --- Variables de Entorno ---
url_n8n_er_cotizador = os.getenv("url_n8n_error_cotizador")
url_n8n_enviar_correo_general = os.getenv("url_n8n_enviar_correo_general")

para_venv = os.getenv("para")
para_lista = para_venv.split(",") if para_venv else []
copia_venv = os.getenv("copia_cuotas")
copias_lista = copia_venv.split(",") if copia_venv else []

def enviarCorreoGeneral(mensaje,ruta_carpeta,id,solicitud):
    
    imagenes = obtener_imagenes_error(ruta_carpeta)

    payload = {
        "Para": para_lista,
        "Copia": copias_lista,
        "Asunto": f"Error generando la {solicitud} en JishuCar para el Movimiento {id}",
        "Mensaje": f"""Hubo problemas al realizar la automatización.\n\nDetalles del error :\n\n{mensaje}""",
        "imagen_nombre": f"Error_{id}.png",
        "imagen_base64": imagenes[0] if imagenes else None
    }

    try:
        response = requests.post(url_n8n_enviar_correo_general,json=payload,timeout=30)

        if response.status_code in (200, 201, 204):
            logging.info(f"✅ Correo enviado")
        else:
            logging.error(f"❌ Problemas en el envio del correo - {response.status_code} - {response.text}")

    except Exception as e:
        logging.error(f"❌ Error enviando correo por el webhook, Motivo : {e}")

def enviar_error_interno(tipo_error,detalle_error):
    
    # Mas adelante pedir correo del ejecutivo responsable de la organizacion, foto , etc
    #imagenes = obtener_imagenes_error(ruta_carpeta, const)

    payload = {
        "Para": f"brandon.rodriguez@jishu.com.pe",
        "Asunto": f"Problemas en cotizar el vehiculo",
        "Tipo de Error": tipo_error,
        "Detalle de Error": str(detalle_error)
    }

    try:
        response = requests.post(url_n8n_er_cotizador,json=payload,timeout=30)

        if response.status_code in (200, 201, 204):
            logging.info(f"✅ Notificación enviada al equipo Jishu")
        else:
            logging.error(f"❌ Problemas en el envio de notificación al equipo Jishu - {response.status_code} - {response.text}")

    except Exception as e:
        logging.error(f"❌ Error enviando la notificación por el webhook, Motivo : {e}")
