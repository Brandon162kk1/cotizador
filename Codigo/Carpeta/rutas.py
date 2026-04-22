import os
import time
import logging
import base64

from Tiempo.fechas_horas import get_timestamp,get_dia,get_mes,get_anio
from io import StringIO

#------Carpetas de Descargas y Volumen del Docker----------
nombre_carpeta_descargas = "Downloads"
download_path = f"/app/{nombre_carpeta_descargas}"

def obtener_imagenes_error(ruta_carpeta):

    imagenes_payload = []

    try:
        for archivo in os.listdir(ruta_carpeta):

            if archivo.startswith("ErrorCotizando_") and archivo.lower().endswith(".png"):

                ruta_completa = os.path.join(ruta_carpeta, archivo)

                with open(ruta_completa, "rb") as f:
                    imagen_base64 = base64.b64encode(f.read()).decode("utf-8")

                imagenes_payload.append(imagen_base64)

    except Exception as e:
        logging.error(f"❌ Error leyendo imágenes de la carpeta: {e}")

    return imagenes_payload

def esperar_archivos_nuevos(directorio, archivos_antes, extension, cantidad, timeout=180):
    """
    Espera archivos nuevos con determinada extensión.
    extension: ".zip", ".pdf", ".xlsx", etc.
    """

    inicio = time.time()

    while time.time() - inicio < timeout:
        actuales = set(os.listdir(directorio))
        nuevos = actuales - archivos_antes

        # Filtrar por extensión (case insensitive)
        nuevos = {
            f for f in nuevos
            if f.lower().endswith(extension.lower())
        }

        if len(nuevos) >= cantidad:

            # Validar que no estén en descarga (.crdownload)
            archivos_validos = []
            for f in nuevos:
                ruta = os.path.join(directorio, f)
                if not os.path.exists(ruta + ".crdownload"):
                    archivos_validos.append(ruta)

            if len(archivos_validos) >= cantidad:
                return archivos_validos

        time.sleep(1)

    return None

def crear_carpeta_descargas(organizacion,id_cot,solicitud):

    # --- 👇 CREAR UN BUFFER NUEVO POR CADA CORREO ---
    log_buffer = StringIO()
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(log_buffer)],
        force=True
    )

    # 📁 rutas
    carpeta_base = os.path.join(download_path, "Jishu_Car")
    carpeta_empresa = os.path.join(carpeta_base, organizacion)
    carpeta_solicitud = os.path.join(carpeta_empresa,solicitud.capitalize())
    carpeta_unica = os.path.join(carpeta_solicitud, f"{id_cot}_{get_dia()}-{get_mes()}-{get_anio()}_{get_timestamp()}")

    # 🏗️ crear estructura completa
    os.makedirs(carpeta_unica, exist_ok=True)

    # 📝 log dentro de la carpeta final
    ruta_log = os.path.join(carpeta_unica, f"log_{get_timestamp()}.txt")

    # Logger definitivo solo para este correo
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    file_handler = logging.FileHandler(ruta_log, mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(file_handler)

    # --- Pasar logs temporales al archivo ---
    log_buffer.seek(0)
    for line in log_buffer.readlines():
        logging.info(line.strip())

    return carpeta_unica