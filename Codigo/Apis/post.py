import requests
import logging
import os
import base64

from dotenv import load_dotenv
#from textwrap import dedent
from Carpeta.rutas import obtener_imagenes_error
from jinja2 import Environment, FileSystemLoader

load_dotenv("/app/variables.env")

# --- Variables de Entorno ---
#url_n8n_enviar_correo_general = os.getenv("url_n8n_enviar_correo_general")
url_n8n_base = os.getenv("url_n8n_base")
webhook_correo = os.getenv("webhook_correo")
webhook_wsp = os.getenv("webhook_wsp")

url_n8n_correo = f"{url_n8n_base}{webhook_correo}"
url_n8n_wsp = f"{url_n8n_base}{webhook_wsp}"

para_venv = os.getenv("para_jc")
para_lista = para_venv.split(",") if para_venv else []
copia_venv = os.getenv("copia_jc")
copias_lista = copia_venv.split(",") if copia_venv else []

ruta_plantilla = "/app/Codigo/Plantillas/Correo"
env = Environment(loader=FileSystemLoader(ruta_plantilla))

def enviarCorreoGeneral(ruta_carpeta,ctx):
    
    logging.info("-----------------------------")
    logging.info(f"⌛ Enviando Correo al equipo Jishu")

    template = env.get_template("plantilla.html")

    imagenes = obtener_imagenes_error(ruta_carpeta)

    nombre_completo = f"{ctx.cliente.nombres} {ctx.cliente.apellido_paterno} {ctx.cliente.apellido_materno}"

    html = template.render(
        titulo=f"⚠️ Problemas en la {ctx.solicitud.capitalize()} #{ctx.id_cot}",
        cliente=f"{nombre_completo if ctx.cliente.tipo_persona == 'NATURAL' else ctx.cliente.rz_social }",
        num_doc=ctx.cliente.num_doc,
        celular=ctx.cliente.celular,
        correo=ctx.cliente.correo,
        uso=ctx.vehiculo.uso.capitalize(),
        vehiculo=f"{ctx.vehiculo.modelo}|{ctx.vehiculo.marca.upper()}|{ctx.vehiculo.tipo}|{ctx.vehiculo.clase}",
        año=ctx.vehiculo.anio,
        precio=f"{ctx.vehiculo.valor}",
        gas='Si' if ctx.vehiculo.gas else 'No',
        asientos=ctx.vehiculo.ocupantes,
        soat='Si' if ctx.vehiculo.seguro else 'No',
        inspeccion='Si' if ctx.vehiculo.inspeccion else 'No',
        modalidad=f"{ctx.credito.forma_pago.capitalize()} en {ctx.credito.cuotas} { 'cuota' if ctx.credito.cuotas == 1 else ' cuotas'}",
        screenshot = (
            f"data:image/png;base64,{imagenes[0]}"
            if imagenes else None
        )
    )

    payload = {
        "Para": para_lista,
        "Copia": copias_lista,
        "Asunto": f"Error generando la {ctx.solicitud.capitalize()} en JishuCar",
        "Mensaje": html
    }

    try:
        response = requests.post(url_n8n_correo,json=payload,timeout=30)

        if response.status_code in (200, 201, 204):
            logging.info(f"✅ Correo enviado")
        else:
            logging.error(f"⚠️ Problemas en el envio del correo - {response.status_code} - {response.text}")

    except Exception as e:
        logging.error(f"❌ Error enviando correo por el webhook, Motivo : {e}")

def enviar_x_wsp(ctx,msj_error,tipo,archivo):

    logging.info("-----------------------------")
    logging.info(f"⌛ Enviando Notificación por WhatsApp")

    # Intentar usar el celular del ejecutivo (vendedor), y si no existe, usar el del cliente
    celular = ctx.ejecutivo.celular if ctx.ejecutivo.celular else ctx.cliente.celular
    
    if not celular or str(celular).strip().lower() == "none":
        logging.error("⚠️ No se pudo enviar WhatsApp: Teléfono del ejecutivo y cliente no están definidos")
        return

    telefono = str(celular).strip()

    if not telefono.startswith("51"):
        telefono = "51" + telefono

    payload = {
        "tipo": tipo,
        "telefono": telefono,
    }

    if tipo == "notificacion":
        motivo = msj_error if msj_error else "Problemas Técnicos del Agente"
        payload["mensaje"] = f"""Hubo problemas para realizar la cotización:
📋 Registro: {ctx.id_cot}
⚠️ Motivo: {motivo}"""

    elif tipo == "documento":

        if not archivo:
            logging.error("⚠️ No se recibió el archivo de cotización")
            return

        if not os.path.exists(archivo):
            logging.error(f"❌ No existe el archivo: {archivo}")
            return

        try:
            with open(archivo, "rb") as f:
                archivo_base64 = base64.b64encode(f.read()).decode("utf-8")

            payload["archivo"] = archivo_base64
            payload["nombreArchivo"] = os.path.basename(archivo)
            payload["mimetype"] = "application/pdf"

            payload["mensaje"] = f"""📋 Adjunto cotización del registro {ctx.id_cot}."""

        except Exception as e:
            logging.error(f"❌ Error convirtiendo PDF a Base64: {e}")
            return

    else:
        logging.error(f"❌ Tipo de mensaje no soportado: {tipo}")
        return

    try:
        response = requests.post(url_n8n_wsp,json=payload,timeout=30)

        if response.status_code in (200, 201, 204):
            logging.info(f"✅ Notificación enviada por Evolution API")
        else:
            logging.error(f"⚠️ Problemas en el envio de notificación a Evolution API - {response.status_code} - {response.text}")

    except Exception as e:
        logging.error(f"❌ Error enviando la notificación por el webhook, Motivo : {e}")