# -*- coding: utf-8 -*-
# -- Froms ---
from datetime import timedelta,datetime
from pandas import qcut
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import WebDriverException,TimeoutException,StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from pprint import pformat
from Tiempo.fechas_horas import get_pos_fecha_dmy
from Apis.put import enviar_documento
from Apis.post import enviarCorreoGeneral,enviar_x_wsp
from Apis.get import codigo_compania
from Chrome.driver import tomar_capturar,abrirDriver
from Carpeta.rutas import esperar_archivos_nuevos,crear_carpeta_descargas,renombrar_carpeta
from Metodos.funciones import interactuar_combo_por_name,click_fuera,seleccionar_combo_por_flecha,escribir_input_por_name,limpiar,seleccionar_modelo_extjs
from Metodos.funciones import escribir_y_enter_combo_por_name,ingresar_fecha_extjs,click_agregar_cliente_extjs,obtener_titulo_modal_extjs,click_boton_buscar_en_modal_extjs
from Metodos.funciones import escribir_input_en_modal,click_boton_grabar_en_modal_extjs,click_tab_terceros_extjs,seleccionar_combo_extjs,set_valor_campo_extjs,abrir_combo_en_fieldset
from Metodos.funciones import responder_mensaje,aceptar_messagebox_extjs,click_boton_ventana,escribir_combo_extjs
# -- Imports --
import logging
import os
import time
import sys
import io
import json

# Forzar la salida en UTF-8 para evitar UnicodeEncodeError
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging para salida inmediata en consola Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# --- Json desde variable de entorno ---
data = json.loads(os.getenv("DATA", "{}"))
entorno = os.getenv("entorno","false").strip().lower() == "true"
url_api_cod_cot = os.getenv("url_api_cod_cot")
API_KEY = os.getenv("API_KEY_RIMAC_SAS")
URL_SAS = os.getenv("urlRimacSAS")

# ------------------ HELPERS --------------
def to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y", "si")
    if isinstance(value, (int, float)):
        return value != 0
    return False

def safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default

def safe_float(value, default=0.0):
    try:
        return float(value)
    except:
        return default

# ------------------ NORMALIZACIÓN --------

def normalizar_data(data: dict):

    data["GAS"] = to_bool(data.get("GAS"))
    data["SOAT"] = to_bool(data.get("SOAT"))
    data["INSPECCION"] = to_bool(data.get("INSPECCION"))
    data["CLIENTE_NUEVO"] = to_bool(data.get("CLIENTE_NUEVO"))
    data["ASIENTOS"] = safe_int(data.get("ASIENTOS"))
    data["PRECIO"] = safe_int(data.get("PRECIO"))
    return data

data = normalizar_data(data)

# ------------------ CLASES ---------------

class BaseModel:

    def to_dict(self, ocultar=None):
        data = self.__dict__.copy()

        if ocultar:
            for campo in ocultar:
                if campo in data:
                    data[campo] = "********"

        return data

class Vehiculo(BaseModel):

    def __init__(self, data: dict):

        self.plan = data.get("plan")
        self.num_rodaje = data.get("num_rodaje")
        self.num_motor = data.get("num_motor")
        self.num_serie = data.get("num_serie")
        self.modelo = data.get("modelo")
        self.tipo = data.get("tipo")
        self.clase = data.get("clase")
        self.marca = data.get("marca")
        self.anio = safe_int(data.get("año"))
        self.valor = data.get("precio")
        self.uso = data.get("uso")
        self.gas = data.get("gas")
        self.ocupantes = data.get("asientos")
        self.seguro = data.get("soat")
        self.inspeccion = data.get("inspeccion")
        self.localizacion = data.get("localizacion")
        self.distrito = data.get("distrito")

    def __str__(self):
        return f"{self.modelo.upper()}|{self.marca.upper()}|{self.tipo}|{self.clase}"

class Asesor(BaseModel):

    def __init__(self, data: dict):

        self.nombre = data.get("asesor")
        self.correo = data.get("correo_asesor")

class Ejecutivo(BaseModel):

    def __init__(self, data: dict):

        self.nombre = data.get("ejecutivo")
        self.celular = data.get("celular_ejecutivo")

class Organizacion(BaseModel):

    def __init__(self, data: dict):

        self.nombre = data.get("nom_organizacion")
        self.sede = data.get("sede")
        self.rol = "CANAL NO TRADICIONAL"
        self.canal = data.get("canal")
        self.plan = data.get("plan_base")

class Credito(BaseModel):

    def __init__(self, data: dict):

        self.tiempo = data.get("tiempo_credito")
        self.cuotas = safe_int(data.get("cuotas"))
        self.forma_pago = data.get("forma_pago")

class Cliente(BaseModel):

    def __init__(self, data: dict):

        self.cliente_nuevo = data.get("cliente_nuevo")
        self.rz_social = data.get("razonsocial")
        self.nombres = data.get("nombres")
        self.apellido_paterno = data.get("paterno")
        self.apellido_materno = data.get("materno")
        self.tipo_persona = data.get("tipo_cliente")
        self.tipo_doc = data.get("tipo_doc")
        self.num_doc = data.get("num_doc")
        fecha = data.get("fecha_nac")
        self.fecha_nac = datetime.strptime(fecha, "%d-%m-%Y").strftime("%d/%m/%Y") if fecha else None
        self.sexo = data.get("sexo")
        self.estado_civil = data.get("estado_civil")
        self.celular = data.get("celular_cliente")
        self.correo = data.get("correo_cliente")
        self.tipo_via = data.get("tip_via")
        self.nom_via = data.get("nom_via")
        self.num_via = data.get("num_via")

class CotizacionContexto:

    def __init__(self, data: dict):

        self.movimiento = data.get("movimiento")
        self.id_cot = data.get("id")
        self.organizacion = Organizacion(data)
        self.vehiculo = Vehiculo(data)
        self.credito = Credito(data)
        self.cliente = Cliente(data)
        self.asesor = Asesor(data)
        self.ejecutivo = Ejecutivo(data)

    def __str__(self):
        return pformat({
            "Organizacion": self.organizacion.to_dict(),
            "Vehículo": self.vehiculo.to_dict(ocultar=["num_rodaje","num_motor","num_serie"]),
            "Crédito": self.credito.to_dict(),
            "Cliente": self.cliente.to_dict(ocultar=["num_doc","celular","correo","rz_social"]),
            "Asesor": self.asesor.to_dict(),
            "Ejecutivo": self.ejecutivo.to_dict(ocultar=["dni","celular"])
        })

# ------------------ USO ------------------
ctx = CotizacionContexto(data)
#------------------------------------------

# --- Redis Imports & Signal Setup ---
import signal
import redis

# Configuración de Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = safe_int(os.getenv("REDIS_PORT"), 6379)
REDIS_QUEUE = os.getenv("REDIS_QUEUE", "cola_cotizador_rimac")
REDIS_STATUS_KEY = os.getenv("REDIS_STATUS_KEY", "worker_status:cotizador")

# Flag global para control de ciclo de vida (Graceful Shutdown)
worker_running = True

def signal_handler(signum, frame):
    global worker_running
    logging.info(f"🛑 Señal recibida ({signum}). Iniciando apagado elegante del worker...")
    worker_running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def iniciar_navegador(ruta_carpeta: str):
    """Inicializa la instancia del WebDriver de Selenium."""
    display_num = os.getenv("DISPLAY_NUM", "0")
    os.environ["DISPLAY"] = f":{display_num}"

    logging.info("🚀 Iniciando navegador Selenium...")
    driver, wait = abrirDriver(ruta_carpeta)
    return driver, wait


def inicializar_sesion(driver, wait, compania_usuario=None, compania_contrasena=None):
    """
    Ejecuta el inicio de sesión único al arranque del worker en RIMAC SAS.
    Maneja credenciales, token 2FA y navegación inicial.
    """
    driver.get(URL_SAS)
    logging.info("🔐 Iniciando sesión única en RIMAC SAS")

    user_input = wait.until(EC.presence_of_element_located((By.ID, "CODUSUARIO")))
    user_input.clear()
    user_input.send_keys(os.getenv("usuarioRimac"))
    logging.info("⌨️ Usuario digitando")

    time.sleep(1)

    pass_input = wait.until(EC.presence_of_element_located((By.ID, "CLAVE")))
    pass_input.clear()
    pass_input.send_keys(os.getenv("passwordRimac"))
    logging.info("⌨️ Password digitado")

    ingresar_btn = wait.until(EC.element_to_be_clickable((By.ID, "btningresar")))
    driver.execute_script("arguments[0].click();", ingresar_btn)
    logging.info("🖱️ Clic en 'Ingresar'")

    token_locator = (By.ID, "TOKEN")
    mensaje_locator = (By.ID, "lblMensaje")

    resultado_ing = wait.until(
        EC.any_of(
            EC.visibility_of_element_located(token_locator),
            EC.visibility_of_element_located(mensaje_locator)
        )
    )

    if resultado_ing.get_attribute("id") == "lblMensaje":
        mensaje = resultado_ing.text.strip()
        raise Exception(f"Error en login: {mensaje}")

    codigo = codigo_compania(url_api_cod_cot, API_KEY)

    token_input = resultado_ing
    token_input.clear()
    token_input.send_keys(codigo)
    logging.info(f"⌨️ Digitando {codigo} en 'TOKEN'")

    try:
        logging.info("🔎 Buscando botón 'Ingresar' tras token...")
        ingresar_btn2 = wait.until(EC.element_to_be_clickable((By.ID, "btningresar")))
        try:
            driver.execute_script("arguments[0].click();", ingresar_btn2)
        except:
            ingresar_btn2.click()
        logging.info("🖱️ Clic en 'Ingresar' (token)")
    except Exception as e:
        logging.exception("❌ Error al hacer clic en 'Ingresar' con token")

    XPATH_TRANSACCIONES = "//span[normalize-space()='Transacciones']"
    max_intentos = 3

    for intento in range(1, max_intentos + 1):
        logging.info(f"⏳ Esperando carga de SAS... Intento {intento}")
        try:
            wait.until(
                lambda d: (
                    d.current_url.startswith(URL_SAS + "index.html")
                    or (
                        d.find_elements(*mensaje_locator)
                        and d.find_element(*mensaje_locator).is_displayed()
                        and d.find_element(*mensaje_locator).text.strip()
                    )
                )
            )

            mensajes = driver.find_elements(*mensaje_locator)
            if mensajes and mensajes[0].is_displayed():
                mensaje = mensajes[0].text.strip()
                if mensaje:
                    raise Exception(mensaje)

            aceptar_botones = driver.find_elements(By.XPATH, "//input[@value='Aceptar'] | //button[normalize-space()='Aceptar'] | //a[normalize-space()='Aceptar']")
            for btn in aceptar_botones:
                if btn.is_displayed():
                    logging.info("⚠️ Mensaje de validación ('Sesión con otro usuario'). Cerrándolo...")
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)

            time.sleep(2)
            break
        except TimeoutException:
            driver.refresh()
            time.sleep(3)
    else:
        raise Exception("Plataforma SAS fuera de servicio al inicializar sesión")

    logging.info("✅ Sesión inicializada con éxito (pantalla principal SAS) y lista para recibir trabajos")


def reset_session(driver, wait):
    """
    Reset Suave: Retorna la navegación a la pantalla inicial del dashboard
    sin cerrar sesión para permitir procesar el siguiente trabajo.
    """
    logging.info("🔄 Ejecutando reset suave de sesión (retornando a pantalla inicial)...")
    try:
        driver.get(URL_SAS + "index.html")
        time.sleep(3)

        aceptar_botones = driver.find_elements(By.XPATH, "//input[@value='Aceptar'] | //button[normalize-space()='Aceptar'] | //a[normalize-space()='Aceptar']")
        for btn in aceptar_botones:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
        logging.info("✅ Reset suave completado exitosamente")
    except Exception as e:
        logging.warning(f"⚠️ Error durante el reset suave: {e}")
        raise e


def asegurar_sesion(driver, wait):
    """
    Verifica si la sesión sigue activa en RIMAC SAS.
    Si la sesión expiró o redirigió al login, vuelve a ejecutar inicializar_sesion().
    """
    try:
        # Si detecta el input CODUSUARIO o la URL de login, la sesión expiró
        login_input = driver.find_elements(By.ID, "CODUSUARIO")
        if login_input and login_input[0].is_displayed():
            logging.warning("⚠️ Sesión expirada detectada. Volviendo a iniciar sesión...")
            inicializar_sesion(driver, wait)
            return

        # Si no detecta transacciones, revalida la pantalla o re-autentica
        if "index.html" not in driver.current_url:
            driver.get(URL_SAS + "index.html")
            time.sleep(2)
            login_input = driver.find_elements(By.ID, "CODUSUARIO")
            if login_input and login_input[0].is_displayed():
                logging.warning("⚠️ Sesión expirada detectada tras recargar. Re-autenticando...")
                inicializar_sesion(driver, wait)
    except Exception as e:
        logging.warning(f"⚠️ Error verificando sesión ({e}). Intentando re-autenticación preventiva...")
        try:
            inicializar_sesion(driver, wait)
        except Exception as reauth_err:
            logging.error(f"❌ Falló re-autenticación preventiva: {reauth_err}")


def procesar_job(driver, wait, payload: dict):
    """
    Ejecuta el flujo completo de cotización para un trabajo individual
    pasando la misma instancia de driver / page.
    """
    payload = normalizar_data(payload)
    ctx = CotizacionContexto(payload)
    poliza = False
    cotizacion = False
    error = False
    msj_error = None

    entorno_job = os.getenv("entorno", "false").strip().lower() == "true"
    ruta_carpeta = crear_carpeta_descargas(ctx, entorno_job)

    # 🔄 Actualizar la carpeta de descargas de Chrome para esta cotización específica
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": os.path.abspath(ruta_carpeta)
        })
    except Exception as e_cdp:
        logging.warning(f"⚠️ No se pudo actualizar downloadPath vía CDP: {e_cdp}")

    try:
        logging.info(f"📋 Procesando Cotización ID: {ctx.id_cot}")

        if not entorno_job:
            logging.info(ctx)

        # 0. Verificar y asegurar que la sesión continúe activa antes de empezar
        asegurar_sesion(driver, wait)

        # 1. Navegación en el menú: Transacciones -> Cotizar -> Registrar Cotización
        XPATH_TRANSACCIONES = "//span[normalize-space()='Transacciones']"
        try:
            span_transacciones = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_TRANSACCIONES)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", span_transacciones)
            actions = ActionChains(driver)
            actions.double_click(span_transacciones).perform()
            logging.info("🖱️ Doble clic en 'Transacciones'")
            time.sleep(2)
        except Exception as err_trans:
            logging.warning(f"⚠️ No se pudo hacer doble clic en Transacciones: {err_trans}")

        span_emision = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Cotizar']")))
        actions = ActionChains(driver)
        actions.double_click(span_emision).perform()
        logging.info("🖱️ Doble clic en 'Cotizar'")
        time.sleep(5)

        span_mantenimiento = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Registrar Cotización']")))
        span_mantenimiento.click()
        logging.info("🖱️ Clic en 'Registrar Cotización'")
        time.sleep(10)

        interactuar_combo_por_name(driver, wait, "iderolcanal", ctx.organizacion.rol.upper())
        logging.info(f"🖱️ Clic en ROL → {ctx.organizacion.rol.upper()}")
        time.sleep(5)

        interactuar_combo_por_name(driver, wait, "idecanal", ctx.organizacion.canal.upper())
        logging.info(f"🖱️ Clic en CANAL → {ctx.organizacion.canal.upper()}")
        time.sleep(5)

        click_fuera(driver)

        logging.info(f"🔎 Buscando plan: '{ctx.organizacion.plan}'")
        seleccionar_combo_por_flecha(driver, wait, "ideplanselected", ctx.organizacion.plan)
        logging.info(f"🖱️ Clic en PLAN → {ctx.organizacion.plan}")
        time.sleep(5)

        click_fuera(driver)

        max_intentos_generar = 3
        for intento_gen in range(1, max_intentos_generar + 1):
            boton = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Generar Datos Particulares']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)
            driver.execute_script("arguments[0].click();", boton)
            logging.info(f"🖱️ Clic en 'Generar Datos Particulares' (Intento {intento_gen})")

            try:
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
                logging.info("✅ Carga finalizada")
                time.sleep(3)
                wait.until(EC.presence_of_element_located((By.NAME, "txtplaca_de_rodaje")))
                break
            except (TimeoutException, Exception):
                logging.warning(f"⚠️ Reintentando formulario de Datos Particulares ({intento_gen}/{max_intentos_generar})...")
                if intento_gen < max_intentos_generar:
                    driver.refresh()
                    time.sleep(5)
                    interactuar_combo_por_name(driver, wait, "iderolcanal", ctx.organizacion.rol.upper())
                    time.sleep(5)
                    interactuar_combo_por_name(driver, wait, "idecanal", ctx.organizacion.canal.upper())
                    time.sleep(5)
                    click_fuera(driver)
                    seleccionar_combo_por_flecha(driver, wait, "ideplanselected", ctx.organizacion.plan)
                    time.sleep(5)
                    click_fuera(driver)
        else:
            raise Exception("No se pudo cargar el formulario de Datos Particulares")

        escribir_input_por_name(driver, wait, "txtplaca_de_rodaje", ctx.vehiculo.num_rodaje, False)
        time.sleep(1)

        escribir_input_por_name(driver, wait, "txtnumero_de_motor", ctx.vehiculo.num_motor, False)
        time.sleep(1)

        escribir_input_por_name(driver, wait, "txtnumero_de_serie", ctx.vehiculo.num_serie, False)
        time.sleep(1)

        logging.info(f"🚗 Vehículo: {ctx.vehiculo}")
        modelo = limpiar(ctx.vehiculo.modelo)
        marca = limpiar(ctx.vehiculo.marca)
        tipo = limpiar(ctx.vehiculo.tipo)
        clase = limpiar(ctx.vehiculo.clase)
        texto_busqueda = modelo
        texto_opcion = f"{modelo}|{marca}|{tipo}|{clase}"
        seleccionar_modelo_extjs(wait, texto_busqueda=texto_busqueda, texto_opcion=texto_opcion)
        time.sleep(3)

        escribir_input_por_name(driver, wait, "txtweb_anos_de_fabricacion", ctx.vehiculo.anio, False)
        time.sleep(1)

        escribir_input_por_name(driver, wait, "txtsuma_asegurada", ctx.vehiculo.valor, False)
        time.sleep(1)

        escribir_y_enter_combo_por_name(driver, wait, "selusos_de_vehiculos", ctx.vehiculo.uso, 1)
        time.sleep(2)

        gas = 'SI' if ctx.vehiculo.gas else 'NO'
        escribir_y_enter_combo_por_name(driver, wait, "selcombustible_gas", gas, 1)
        time.sleep(2)

        escribir_input_por_name(driver, wait, "txtnro_pasajeros", ctx.vehiculo.ocupantes, False)
        time.sleep(1)

        soat = 'SI' if ctx.vehiculo.seguro else 'NO'
        escribir_y_enter_combo_por_name(driver, wait, "selprocedenciaexterna", soat, 1)
        time.sleep(2)

        inspeccion = 'NO'
        escribir_y_enter_combo_por_name(driver, wait, "selrequiereinspeccion", inspeccion, 1)
        time.sleep(2)

        if ctx.vehiculo.uso == 'PARTICULAR':
            escribir_y_enter_combo_por_name(driver, wait, "seltipo_de_persona", ctx.cliente.tipo_persona, 2)
            time.sleep(2)
            escribir_y_enter_combo_por_name(driver, wait, "seltiempo_de_credito", ctx.credito.tiempo, 2)
            time.sleep(2)
            escribir_input_por_name(driver, wait, "txtvendedor", ctx.ejecutivo.nombre, False)
            time.sleep(1)
            localizacion = 'LIMA' if ctx.vehiculo.localizacion in ('LIMA', 'CALLAO') else 'PROVINCIAS'
            escribir_y_enter_combo_por_name(driver, wait, "sellocalización", localizacion, 2)
            time.sleep(2)

        btn_cal = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Calcular Planes']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_cal)
        driver.execute_script("arguments[0].click();", btn_cal)
        logging.info("🖱️ Clic en 'Calcular Planes'")

        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
        except TimeoutException:
            raise Exception("Tiempo de espera excedido al Calcular Planes")

        modal_mensaje = (By.XPATH, "//div[contains(@class,'x-window-dlg')]//span[contains(text(),'No se encontraron planes configurados')]")
        fieldset_plan = (By.XPATH, "//fieldset[.//span[normalize-space()='Plan 1']]")
        toast_error = (By.CSS_SELECTOR, "#message-div .message")
        modal_validacion = (By.ID, "lblContenido")

        resultado = wait.until(
            EC.any_of(
                EC.visibility_of_element_located(modal_mensaje),
                EC.visibility_of_element_located(fieldset_plan),
                EC.visibility_of_element_located(toast_error),
                EC.visibility_of_element_located(modal_validacion)
            )
        )

        texto = resultado.text.strip()
        if resultado.get_attribute("id") == "lblContenido" or "Datos erróneos" in texto or "No se encontraron planes configurados" in texto:
            raise Exception(texto)

        boton_seleccionar = wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[normalize-space()='Seleccionar'] | .//a[normalize-space()='Seleccionar']")))
        driver.execute_script("arguments[0].click();", boton_seleccionar)
        logging.info("🖱️ Clic en Seleccionar")
        time.sleep(3)

        tab_fraccionamiento = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class,'x-tab-strip-text') and normalize-space()='Fraccionamiento']")))
        tab_fraccionamiento.click()
        logging.info("🖱️ Clic en Fraccionamiento")
        time.sleep(3)

        tipo_cuenta = "Cuenta de Ahorros" if ctx.cliente.tipo_persona.upper() == "NATURAL" else "Cuenta Corriente"
        tiempo_12 = ctx.credito.tiempo == "12 MESES"
        es_juridica = ctx.cliente.tipo_persona.upper() == "JURIDICA"
        tipo_plan = "PLAN CC CNT PERSONA JURIDICA" if es_juridica else ("PLAN 2020 CC PN 0% USD 12 CUOTAS" if tiempo_12 else "PLAN CC CNT PERSONA NATURAL")

        escribir_y_enter_combo_por_name(driver, wait, "ideplanfinanciamiento", tipo_plan, 2)
        time.sleep(1)

        escribir_input_por_name(driver, wait, "numcuotas", ctx.credito.cuotas, False)
        time.sleep(1)

        escribir_y_enter_combo_por_name(driver, wait, "idetipotarjeta", tipo_cuenta, 2)
        time.sleep(2)

        fecha_ddmmyyyy = (datetime.strptime(get_pos_fecha_dmy(), "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y")
        ingresar_fecha_extjs(wait, name="fecprimvcto", fecha_ddmmyyyy=fecha_ddmmyyyy, texto="Fecha primer vencimiento")
        time.sleep(2)
        click_fuera(driver)

        btn_generar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Generar']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_generar)
        driver.execute_script("arguments[0].click();", btn_generar)
        logging.info("🖱️ Clic en 'Generar'")
        time.sleep(5)

        btn_ing_cliente = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Ingresar Cliente']")))
        driver.execute_script("arguments[0].click();", btn_ing_cliente)
        time.sleep(5)

        wait.until(EC.presence_of_element_located((By.XPATH, "//li[contains(@class,'x-tab-strip-active')]//span[normalize-space()='Cliente']")))
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))

        click_agregar_cliente_extjs(driver)
        logging.info("🖱️ Clic en 'Agregar'")

        titulo_modal = obtener_titulo_modal_extjs(wait)
        if titulo_modal is None:
            raise Exception("No apareció modal para registrar cliente")

        time.sleep(3)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x-window[style*='visibility: visible']")))

        if es_juridica:
            escribir_combo_extjs(wait, "idptipotercero", "PERSONA JURÍDICA", valor_esperado="J")
            time.sleep(2)
            escribir_combo_extjs(wait, "idptipodocumento", ctx.cliente.tipo_doc)
            time.sleep(2)

        dispatch_tipo_doc = {"RUC": "1", "DNI": "2", "PASAPORTE": "3", "C.E.": "4"}
        if ctx.cliente.tipo_doc != 'DNI':
            val_doc = dispatch_tipo_doc.get(ctx.cliente.tipo_doc.upper())
            if not val_doc:
                raise Exception(f"Tipo de documento '{ctx.cliente.tipo_doc}' no soportado")
            escribir_combo_extjs(wait, "idptipodocumento", ctx.cliente.tipo_doc, valor_esperado=val_doc)
            time.sleep(2)

        escribir_input_en_modal(driver, wait, "numerodoc", os.getenv("ruc_cot") if es_juridica else ctx.cliente.num_doc, True)
        time.sleep(2)

        click_boton_buscar_en_modal_extjs(driver)
        time.sleep(3)

        campo_nombre = wait.until(EC.presence_of_element_located((By.NAME, "nombre")))
        if not campo_nombre.get_attribute("value").strip():
            if es_juridica:
                raise Exception("No se pudo autocompletar los datos de la empresa")
            else:
                set_valor_campo_extjs(driver, wait, "nombre", ctx.cliente.nombres)
                set_valor_campo_extjs(driver, wait, "apepaterno", ctx.cliente.apellido_paterno)
                set_valor_campo_extjs(driver, wait, "apematerno", ctx.cliente.apellido_materno)
                driver.execute_script("""
                    var radio = document.querySelector("input[name='idpgenero'][value='" + arguments[0] + "']");
                    radio.checked = true;
                    radio.dispatchEvent(new Event('click', {bubbles:true}));
                    radio.dispatchEvent(new Event('change', {bubbles:true}));
                """, ctx.cliente.sexo)
                time.sleep(1)
                driver.execute_script("""
                    var win = Ext.WindowMgr.getActive();
                    var campo = win.find("name", "fecnacimiento")[0];
                    campo.setValue(arguments[0]);
                    campo.fireEvent('change', campo, arguments[0]);
                """, ctx.cliente.fecha_nac)
                time.sleep(1)

            abrir_combo_en_fieldset(driver, "Direcciones", "idedistrito")
            time.sleep(1)
            seleccionar_combo_extjs(wait, ctx.vehiculo.distrito)
            time.sleep(1)

            abrir_combo_en_fieldset(driver, "Direcciones", "idptipovia")
            time.sleep(1)
            seleccionar_combo_extjs(wait, ctx.cliente.tipo_via)
            time.sleep(1)

            driver.execute_script("""
                var campo = document.querySelector("input[name='nomvia']");
                campo.value = arguments[0];
                campo.dispatchEvent(new Event('input', {bubbles:true}));
                campo.dispatchEvent(new Event('change', {bubbles:true}));
            """, ctx.cliente.nom_via)

            driver.execute_script("""
                var campo = document.querySelector("input[name='numcasa']");
                campo.value = arguments[0];
                campo.dispatchEvent(new Event('input', {bubbles:true}));
                campo.dispatchEvent(new Event('change', {bubbles:true}));
            """, ctx.cliente.num_via)

            set_valor_campo_extjs(driver, wait, "numtelefcasa", ctx.cliente.celular)
            set_valor_campo_extjs(driver, wait, "emailpersonal", ctx.cliente.correo)

            click_boton_grabar_en_modal_extjs(driver, wait)
            mensaje = aceptar_messagebox_extjs(driver, wait)

            if "Satisfactoriamente" in mensaje:
                responder_mensaje(driver, wait, "Aceptar")
                time.sleep(3)
                try:
                    ventana = wait.until(
                        lambda d: next((v for v in d.find_elements(By.CSS_SELECTOR, "div.x-window") if v.is_displayed()), None)
                    )
                    boton = ventana.find_element(By.CSS_SELECTOR, "button.tb-exit")
                    driver.execute_script("arguments[0].click();", boton)
                except Exception as ex_win:
                    logging.warning(f"⚠️ No se pudo cerrar la ventana de asegurado: {ex_win}")

        time.sleep(5)
        click_boton_grabar_en_modal_extjs(driver, wait)
        time.sleep(3)

        btn_gen_coti = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Generar Cotización']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_gen_coti)
        driver.execute_script("arguments[0].click();", btn_gen_coti)
        time.sleep(3)

        btn_si = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Sí']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_si)
        driver.execute_script("arguments[0].click();", btn_si)
        time.sleep(5)

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))

        btn_imprimir = (By.XPATH, "//button[contains(@class,'tb-print') and contains(.,'Imprimir')]")
        wait.until(EC.presence_of_element_located(btn_imprimir))
        wait.until(EC.element_to_be_clickable(btn_imprimir))
        driver.find_element(*btn_imprimir).click()
        logging.info("🖱️ Clic en 'Imprimir'")

        archivos_antes = set(os.listdir(ruta_carpeta))
        cotizacion_pdf = esperar_archivos_nuevos(ruta_carpeta, archivos_antes, ".pdf", cantidad=1)

        if cotizacion_pdf:
            cotizacion = True
            logging.info("✅ Cotización descargada exitosamente")
            ruta_original = cotizacion_pdf[0]
            ruta_final = os.path.join(ruta_carpeta, f"cot_{ctx.id_cot}.pdf")
            os.rename(ruta_original, ruta_final)
        else:
            raise Exception("No se descargó ninguna cotización")

        return {"status": "SUCCESS", "id_cot": ctx.id_cot, "pdf": os.path.join(ruta_carpeta, f"cot_{ctx.id_cot}.pdf")}

    except WebDriverException as e:
        error = True
        logging.error("❌ Error técnico de Selenium durante el job")
        logging.exception(e)
        msj_error = "Problemas Técnicos del Agente"
        raise e
    except Exception as e:
        error = True
        logging.warning(f"⚠️ Error funcional en el job: {e}")
        msj_error = str(e)
        raise e
    finally:
        if error:
            tomar_capturar(driver, ruta_carpeta, f"ErrorCotizando_{ctx.id_cot}")
            if entorno_job:
                enviarCorreoGeneral(ruta_carpeta, ctx)
                enviar_x_wsp(ctx, msj_error, "notificacion", None)
            renombrar_carpeta(ruta_carpeta)

        if cotizacion:
            archivo = os.path.join(ruta_carpeta, f"cot_{ctx.id_cot}.pdf")
            if entorno_job:
                enviar_documento(ctx.id_cot, archivo, "cotizacion")
                enviar_x_wsp(ctx, None, "documento", archivo)


def main():
    """
    Worker Loop Principal:
    1. Inicializa el navegador y la sesión única.
    2. Conecta a Redis y escucha la cola con timeout para permitir Graceful Shutdown.
    3. Procesa trabajos individualmente manteniendo la sesión activa.
    """
    global worker_running
    driver = None
    wait = None
    r = None

    # Configuración de carpeta temporal base para capturas de inicio
    base_ruta = os.path.join(os.getcwd(), "descargas_temp")
    os.makedirs(base_ruta, exist_ok=True)

    try:
        # 1. Conexión a Redis
        logging.info(f"🔌 Conectando a Redis en {REDIS_HOST}:{REDIS_PORT}...")
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        r.ping()
        logging.info("✅ Conexión a Redis establecida.")

        # 2. Inicialización de Navegador y Sesión Única (Startup)
        driver, wait = iniciar_navegador(base_ruta)
        inicializar_sesion(driver, wait)

        # Establecer estado inicial READY
        r.set(REDIS_STATUS_KEY, "READY")
        logging.info(f"🟢 Worker listo y escuchando en la cola '{REDIS_QUEUE}' (Estado: READY)")

        # 3. Bucle de Procesamiento (Worker Loop)
        while worker_running:
            try:
                # BRPOP con timeout corto (2 segundos) para reaccionar a señales de cancelación
                pop_result = r.brpop(REDIS_QUEUE, timeout=2)

                if not pop_result:
                    continue  # Timeout transcurrido sin nuevos trabajos

                queue_name, raw_job = pop_result
                logging.info(f"📥 Nuevo trabajo recibido de la cola '{queue_name}'")

                # Parsear Payload JSON
                try:
                    job_payload = json.loads(raw_job)
                    # Desempaquetar si el orquestador envió un wrapper {"job_id":..., "payload":{...}} o {"data":{...}}
                    if isinstance(job_payload, dict):
                        if "payload" in job_payload and isinstance(job_payload["payload"], dict):
                            job_payload = job_payload["payload"]
                        elif "data" in job_payload and isinstance(job_payload["data"], dict):
                            job_payload = job_payload["data"]
                except Exception as parse_err:
                    logging.error(f"❌ Error parseando JSON del trabajo recibido: {parse_err}")
                    continue

                # Cambiar estado a BUSY
                r.set(REDIS_STATUS_KEY, "BUSY")

                try:
                    # Ejecutar automatización principal pasando la misma instancia de driver
                    res = procesar_job(driver, wait, job_payload)
                    logging.info(f"✅ Trabajo completado exitosamente: {res}")
                except Exception as job_err:
                    logging.exception(f"💥 Error al procesar el trabajo: {job_err}")
                    # Tomar captura de seguridad en caso de error no capturado dentro del job
                    try:
                        tomar_capturar(driver, base_ruta, "Error_Worker_Job")
                    except Exception:
                        pass

                # Reset Suave para retornar al Dashboard / Formulario Inicial
                try:
                    reset_session(driver, wait)
                except Exception as reset_err:
                    logging.error(f"❌ Falló el reset suave ({reset_err}). Intentando re-autenticar sesión...")
                    try:
                        inicializar_sesion(driver, wait)
                    except Exception as reauth_err:
                        logging.critical(f"💥 No se pudo recuperar la sesión: {reauth_err}")
                        break  # Salir del bucle para reiniciar el worker/contenedor si la sesión murió totalmente

                # Retornar estado a READY
                r.set(REDIS_STATUS_KEY, "READY")
                logging.info("🟢 Worker listo para la siguiente solicitud (Estado: READY)")

            except redis.RedisError as r_err:
                logging.error(f"❌ Error en la conexión con Redis: {r_err}")
                time.sleep(5)
            except Exception as loop_err:
                logging.error(f"⚠️ Excepción no esperada en el bucle del worker: {loop_err}")
                time.sleep(2)

    except Exception as startup_err:
        logging.critical(f"💥 Error fatal al arrancar el worker: {startup_err}")
    finally:
        # 4. Cierre Elegante (Graceful Shutdown)
        logging.info("🧹 Ejecutando limpieza de recursos del worker...")
        if r:
            try:
                r.set(REDIS_STATUS_KEY, "STOPPED")
                r.close()
                logging.info("✅ Conexión a Redis cerrada.")
            except Exception as e:
                logging.warning(f"⚠️ Error al cerrar Redis: {e}")

        if driver:
            try:
                driver.quit()
                logging.info("✅ Navegador Selenium cerrado de forma limpia.")
            except Exception as e:
                logging.warning(f"⚠️ Error al cerrar Selenium Driver: {e}")

        logging.info("👋 Worker finalizado.")


if __name__ == "__main__":
    main()
   