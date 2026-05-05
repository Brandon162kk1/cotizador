import requests
import logging
import os

from dotenv import load_dotenv
from textwrap import dedent
from Carpeta.rutas import obtener_imagenes_error

load_dotenv("/app/variables.env")

# --- Variables de Entorno ---
url_n8n_enviar_correo_general = os.getenv("url_n8n_enviar_correo_general")

para_venv = os.getenv("para_jc")
para_lista = para_venv.split(",") if para_venv else []
copia_venv = os.getenv("copia_jc")
copias_lista = copia_venv.split(",") if copia_venv else []

def enviarCorreoGeneral(fallo,ruta_carpeta,ctx):
    
    imagenes = obtener_imagenes_error(ruta_carpeta)

    nombre_completo = f"{ctx.cliente.nombres} {ctx.cliente.apellido_paterno} {ctx.cliente.apellido_materno}"
    mensaje = dedent(f"""Hubo problemas al cotizar un vehículo en la compañia Rimac.

        Datos del Cliente :

        Nombre : { nombre_completo if ctx.cliente.tipo_persona == 'NATURAL' else ctx.cliente.rz_social}"
        Número de Documento : {ctx.cliente.num_doc}

        Datos del Vehículo:

        Uso : {ctx.vehiculo.uso.capitalize()}
        Vehículo : {ctx.vehiculo.marca}|{ctx.vehiculo.modelo}|{ctx.vehiculo.tipo}|{ctx.vehiculo.clase}
        Año: {ctx.vehiculo.anio}
        Precio ($): {ctx.vehiculo.valor}
        Gas : {'Si' if ctx.vehiculo.gas else 'No'}
        Asientos : {ctx.vehiculo.ocupantes}
        Soat : {'Si' if ctx.vehiculo.seguro else 'No'}
        Inspección : {'Si' if ctx.vehiculo.inspeccion else 'No'}

        Error Técnico y evidencia visual :

        {fallo}
    """)

    mensaje = "\n".join(line.strip() for line in mensaje.splitlines())

    payload = {
        "Para": para_lista,
        "Copia": copias_lista,
        "Asunto": f"Error generando la {ctx.solicitud.capitalize()} en JishuCar para el Movimiento {ctx.id_cot}",
        "Mensaje": mensaje,
        "imagen_nombre": f"Error_{ctx.id_cot}.png",
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
