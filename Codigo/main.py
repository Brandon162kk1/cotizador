# -*- coding: utf-8 -*-
# -- Froms ---
from datetime import timedelta,datetime
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from pprint import pformat
from Tiempo.fechas_horas import get_pos_fecha_dmy
from Apis.put import enviar_documento
from Apis.post import enviarCorreoGeneral
from Apis.get import codigo_compania
from Chrome.driver import tomar_capturar,abrirDriver
from Carpeta.rutas import esperar_archivos_nuevos,crear_carpeta_descargas,renombrar_carpeta
from Metodos.funciones import resolver_empresa,interactuar_combo_por_name,click_fuera,seleccionar_combo_por_flecha,escribir_input_por_name,limpiar,seleccionar_modelo_extjs
from Metodos.funciones import escribir_y_enter_combo_por_name,ingresar_fecha_extjs,click_agregar_cliente_extjs,obtener_titulo_modal_extjs,click_boton_buscar_en_modal_extjs
from Metodos.funciones import escribir_input_en_modal,click_boton_grabar_en_modal_extjs,click_tab_terceros_extjs,seleccionar_combo_extjs,set_valor_campo_extjs,abrir_combo_en_fieldset
from Metodos.funciones import responder_mensaje,aceptar_messagebox_extjs,click_boton_toolbar_extjs,click_boton_ventana
# -- Imports --
import logging
import os
import time
import sys
import io
import json

# Forzar la salida en UTF-8 para evitar UnicodeEncodeError
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- Json desde variable de entorno ---
data = json.loads(os.getenv("DATA", "{}"))

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

class Vehiculo:
    def __init__(self, data: dict):

        self.organizacion = data.get("ORGANIZACION") or ""
        self.plan = data.get("PLAN")

        self.num_rodaje = data.get("NUM_RODAJE")
        self.num_motor = data.get("NUM_MOTOR")
        self.num_serie = data.get("NUM_SERIE")

        self.modelo = data.get("MODELO_VEH")
        self.tipo = data.get("TIPO_VEH")
        self.clase = data.get("CLASE_VEH")

        self.marca = data.get("MARC_VEH")

        self.anio = safe_int(data.get("AÑO_FAB"))
        self.valor = data.get("PRECIO")
        self.uso = data.get("USO_VEHICULO")
        self.gas = data.get("GAS")
        self.ocupantes = data.get("ASIENTOS")

        self.seguro = data.get("SOAT")
        self.inspeccion = data.get("INSPECCION")

        self.localizacion = data.get("LOCALIZACION_CARRO")
        self.distrito_veh = data.get("DISTRITO_CARRO")

    def __str__(self):
        return f"{self.modelo.upper()}|{self.marca.upper()}|{self.tipo}|{self.clase}"

class Usuario:
    def __init__(self, data: dict):

        self.usuario = data.get("USUARIO")
        self.contrasena = data.get("CONTRASEÑA")
        self.rol = data.get("ROL")
        self.canal = data.get("CANAL")
        self.correo_asesor = data.get("CORREO_ASESOR")
        self.vendedor = data.get("VENDEDOR")
        self.dni = safe_int(data.get("DNI_VENDEDOR"))

class Credito:
    def __init__(self, data: dict):

        self.tiempo = data.get("TIEMPO_CREDITO")
        self.cuotas = safe_int(data.get("CUOTAS"))
        self.forma_pago = data.get("FORMA_PAGO")

class Cliente:
    def __init__(self, data: dict):

        self.cliente_nuevo = data.get("CLIENTE_NUEVO")
        self.rz_social = data.get("RAZON_SOCIAL")
        self.nombres = data.get("NOMBRES")
        self.apellido_paterno = data.get("APE_PATERNO")
        self.apellido_materno = data.get("APE_MATERNO")
        self.tipo_persona = data.get("TIP_PERSONA")
        self.tipo_doc = data.get("TIP_DOC")
        self.num_doc = data.get("NUM_DOC")
        fecha = data.get("FECHA_NAC")
        self.fecha_nac = datetime.strptime(fecha, "%d-%m-%Y").strftime("%d/%m/%Y") if fecha else None
        self.sexo = data.get("SEXO")
        self.estado_civil = data.get("ESTADO_CIVIL")
        self.celular = data.get("CELULAR")
        self.correo = data.get("CORREO")
        self.tipo_via = data.get("TIPO_VIA")
        self.nom_via = data.get("NOMBRE_VIA")
        self.num_via = data.get("NUMERO_VIA")

class CotizacionContexto:

    def __init__(self, data: dict):

        self.entorno = data.get("entorno")
        self.solicitud = data.get("SOLICITUD")
        self.id_cot = data.get("ID_COT")
        self.usuario = Usuario(data)
        self.vehiculo = Vehiculo(data)
        self.credito = Credito(data)
        self.cliente = Cliente(data)

    def __str__(self):
        return pformat({
            "usuario": self.usuario.__dict__,
            "vehiculo": self.vehiculo.__dict__,
            "credito": self.credito.__dict__,
            "cliente": self.cliente.__dict__
        })

# ------------------ USO ------------------
ctx = CotizacionContexto(data)
#------------------------------------------

def main():

    poliza = False
    cotizacion = False
    driver = None

    nom_empresa = resolver_empresa(ctx)

    ruta_carpeta = crear_carpeta_descargas(nom_empresa,ctx)

    try:

        display_num = os.getenv("DISPLAY_NUM", "0")
        os.environ["DISPLAY"] = f":{display_num}"

        driver,wait = abrirDriver(ruta_carpeta)

        driver.get(URL_SAS)
        logging.info("🔐 Iniciando sesión en RIMAC SAS")

        #logging.info(ctx)
 
        user_input = wait.until(EC.presence_of_element_located((By.ID, "CODUSUARIO")))
        user_input.clear()
        user_input.send_keys(ctx.usuario.usuario)
        logging.info("⌨️ Usuario digitando")

        time.sleep(1)
 
        pass_input = wait.until(EC.presence_of_element_located((By.ID, "CLAVE")))
        pass_input.clear()
        password = os.getenv("passwordRimac") if ctx.entorno.upper() == "LOCAL" else ctx.usuario.contrasena
        pass_input.send_keys(password)
        logging.info(f"⌨️ Password '{password}' digitado")
 
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
            raise Exception(mensaje)

        codigo = codigo_compania(url_api_cod_cot,API_KEY)

        token_input = resultado_ing

        token_input.clear()
        token_input.send_keys(codigo)
        logging.info(f"⌨️ Digitando {codigo} correctamente en 'TOKEN'")

        ingresar_btn2 = wait.until(EC.element_to_be_clickable((By.ID, "btningresar")))
        driver.execute_script("arguments[0].click();", ingresar_btn2)
        logging.info("🖱️ Clic en 'Ingresar'")

        XPATH_TRANSACCIONES = "//span[normalize-space()='Transacciones']"
        max_intentos = 3

        for intento in range(1, max_intentos + 1):

            try:

                # Espera hasta que ocurra cualquiera de las dos cosas
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

                # Si apareció un mensaje, detener el proceso
                mensajes = driver.find_elements(*mensaje_locator)
                if mensajes and mensajes[0].is_displayed():
                    mensaje = mensajes[0].text.strip()
                    if mensaje:
                        raise Exception(mensaje)

                logging.info(f"⏳ Esperando carga de SAS... Intento {intento}")
                span_transacciones = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_TRANSACCIONES)))

                driver.execute_script("arguments[0].scrollIntoView({block:'center'});",span_transacciones)
                actions = ActionChains(driver)
                actions.double_click(span_transacciones).perform()
                logging.info("🖱️ Doble clic realizado en 'Transacciones'")

                time.sleep(2)
                break

            except TimeoutException:
                driver.refresh()
                time.sleep(3)

        else:
            raise Exception("Credenciales o Token inválido / No se pudo cargar SAS")

        #----------------------------
        span_emision = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Cotizar']"))) # L
        actions.double_click(span_emision).perform()
        logging.info("🖱️ Doble clic realizado en 'Cotizar'")
        time.sleep(3)
        #----------------------------
        span_mantenimiento = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Registrar Cotización']"))) # L
        span_mantenimiento.click()
        logging.info("🖱️ Clic realizado en 'Registrar Cotización'")
        time.sleep(10)
        logging.info("------------------------------------")
        #----------------------------
        interactuar_combo_por_name(driver, wait, "iderolcanal", "CANAL NO TRADICIONAL") # ctx.usuario.rol
        logging.info(f"🖱️ Clic en ROL → 'CANAL NO TRADICIONAL'")
        time.sleep(5)
        #----------------------------
        interactuar_combo_por_name(driver, wait, "idecanal", ctx.usuario.canal.upper())
        logging.info(f"🖱️ Clic en CANAL → {ctx.usuario.canal.upper()}")
        time.sleep(3)
        #----------------------------
        click_fuera(driver)
        #----------------------------
        #texto_base = f"CANAL {nom_empresa.upper()} TR" if ctx.vehiculo.plan.upper() == "PARTICULAR" else f"CANAL {nom_empresa.upper()} - {'TAXI' if nom_empresa.upper() == 'DONGFENG' else 'TRANSPORTE DE PERSONAL'}"
        texto_base = f"CANAL {nom_empresa.upper()} TR" if ctx.vehiculo.plan.upper() == "PARTICULAR" else f"CANAL {nom_empresa.upper()} TAXI"
        seleccionar_combo_por_flecha(driver,wait,"ideplanselected",texto_base)
        logging.info(f"🖱️ Clic en PLAN → {ctx.vehiculo.plan.upper()}")
        time.sleep(3)
        #----------------------------
        click_fuera(driver)
        #----------------------------
        boton = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Generar Datos Particulares']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)
        driver.execute_script("arguments[0].click();", boton)
        logging.info("🖱️ Clic en 'Generar Datos Particulares'")
        #----------------------------
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
            logging.info("✅ Carga finalizada")
        except TimeoutException:
            raise Exception("Tiempo de espera excedido al generar datos particulares")
        #----------------------------
        escribir_input_por_name(driver, wait, "txtplaca_de_rodaje",ctx.vehiculo.num_rodaje,False)
        time.sleep(1)
        #----------------------------
        escribir_input_por_name(driver, wait, "txtnumero_de_motor",ctx.vehiculo.num_motor,False)
        time.sleep(1)
        #----------------------------
        escribir_input_por_name(driver, wait, "txtnumero_de_serie",ctx.vehiculo.num_serie,False)
        time.sleep(1)
        #----------------------------
        logging.info(f"🚗 Vehículo a buscar: {ctx.vehiculo}")
        modelo = limpiar(ctx.vehiculo.modelo)
        marca = limpiar(ctx.vehiculo.marca)
        tipo = limpiar(ctx.vehiculo.tipo)
        clase = limpiar(ctx.vehiculo.clase)
        texto_busqueda = modelo
        texto_opcion = f"{modelo}|{marca}|{tipo}|{clase}"
        seleccionar_modelo_extjs(driver,wait,texto_busqueda=texto_busqueda,texto_opcion=texto_opcion)
        time.sleep(3)
        #----------------------------
        escribir_input_por_name(driver, wait, "txtweb_anos_de_fabricacion",ctx.vehiculo.anio,False)
        time.sleep(1)
        #----------------------------
        escribir_input_por_name(driver, wait, "txtsuma_asegurada",ctx.vehiculo.valor,False)
        time.sleep(1)
        #----------------------------
        escribir_y_enter_combo_por_name(driver,wait,"selusos_de_vehiculos",ctx.vehiculo.uso,1)
        logging.info(f"🖱️ Opción seleccionada para el uso de vehículos → '{ctx.vehiculo.uso}'")
        time.sleep(3)
        #----------------------------
        gas = 'SI' if ctx.vehiculo.gas else 'NO'
        escribir_y_enter_combo_por_name(driver,wait,"selcombustible_gas",gas,1)
        logging.info(f"🖱️ Opción seleccionada para GAS → '{gas}'")
        time.sleep(3)
        #----------------------------
        escribir_input_por_name(driver, wait, "txtnro_pasajeros",ctx.vehiculo.ocupantes,False)
        time.sleep(1)
        #----------------------------
        soat = 'SI' if ctx.vehiculo.seguro else 'NO'
        escribir_y_enter_combo_por_name(driver,wait,"selprocedenciaexterna",soat,1)
        logging.info(f"🖱️ Opción seleccionada para SOAT → '{soat}'")
        time.sleep(3)
        #----------------------------
        inspeccion = 'SI' if ctx.vehiculo.inspeccion else 'NO'
        escribir_y_enter_combo_por_name(driver,wait,"selrequiereinspeccion",inspeccion,1)
        logging.info(f"🖱️ Opción seleccionada para INSPECCION → '{inspeccion}'")
        time.sleep(3)
        #----------------------------
        if ctx.vehiculo.uso == 'PARTICULAR':
            escribir_y_enter_combo_por_name(driver,wait,"seltipo_de_persona",ctx.cliente.tipo_persona,2)
            #escribir_y_enter_combo_por_name(driver,wait,"seltipo_de_persona",f"NATURAL",2)
            logging.info(f"🖱️ Opción seleccionada para Tipo de persona → '{ctx.cliente.tipo_persona}'")
            time.sleep(3)
            #----------------------------
            escribir_y_enter_combo_por_name(driver,wait,"seltiempo_de_credito",ctx.credito.tiempo,2)
            logging.info(f"🖱️ Opción seleccionada para el tiempo de crédito → '{ctx.credito.tiempo}'")
            time.sleep(3)
            #----------------------------
            escribir_input_por_name(driver, wait, "txtvendedor",ctx.usuario.vendedor,False)
            time.sleep(1)
            #----------------------------
            #localizacion = 'LIMA' if ctx.vehiculo.localizacion == 'LIMA' else 'PROVINCIAS'
            localizacion = 'LIMA' if ctx.vehiculo.localizacion in ('LIMA','CALLAO') else 'PROVINCIAS'
            escribir_y_enter_combo_por_name(driver,wait,"sellocalización",localizacion,2)
            logging.info(f"🖱️ Opción seleccionada en localización → '{localizacion}'")
            time.sleep(3)
        #----------------------------
        btn_cal = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Calcular Planes']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_cal)
        driver.execute_script("arguments[0].click();", btn_cal)
        logging.info("🖱️ Clic en 'Calcular Planes'")
        #----------------------------
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
            logging.info("✅ Carga finalizada")
        except TimeoutException:
            raise Exception("Tiempo de espera excedido al Calcular Planes")
        #----------------------------
        modal_mensaje = (By.XPATH,"//div[contains(@class,'x-window-dlg')]//span[contains(text(),'No se encontraron planes configurados')]")
        fieldset_plan = (By.XPATH,"//fieldset[.//span[normalize-space()='Plan 1']]")
        toast_error = (By.CSS_SELECTOR,"#message-div .message")
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

        if resultado.get_attribute("id") == "lblContenido":
            raise Exception(texto)
        if "Datos erróneos" in texto:
            raise Exception(texto)
        if "No se encontraron planes configurados" in texto:
            logging.warning("⚠️ Apareció modal")
            raise Exception(texto)
        else:
            logging.info("✅ Plan localizado y visible")

        #----------------------------
        # fieldset_plan = wait.until(EC.presence_of_element_located((By.XPATH, "//fieldset[.//span[normalize-space()='Plan 1']]")))
        # wait.until(EC.visibility_of(fieldset_plan))
        # logging.info("✅ Plan localizado y visible")
        #----------------------------
        boton_seleccionar = wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[normalize-space()='Seleccionar'] | .//a[normalize-space()='Seleccionar']")))
        driver.execute_script("arguments[0].click();", boton_seleccionar)
        logging.info("🖱️ Clic en Seleccionar")

        descuento = False

        if descuento :
            #----------------------------
            escribir_input_por_name(driver, wait, "recadctoppact","5",False)
            time.sleep(1)
            #----------------------------
            tomar_capturar(driver,ruta_carpeta,f"antesDESCUENTO{ctx.id_cot}")
            #----------------------------
            btn_calcular = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Calcular']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_calcular)
            driver.execute_script("arguments[0].click();", btn_calcular)
            logging.info("🖱️ Clic en 'Calcular'")
            time.sleep(5)
            #----------------------------
            # Esperar que aparezca el mensaje
            mensaje = wait.until(
                EC.visibility_of_element_located((
                    By.XPATH,
                    "//span[contains(@class,'ext-mb-text') and contains(.,'La información se grabó exitosamente.')]"
                ))
            )
            logging.info(f"✅ {mensaje.text}")
            #----------------------------
            # Esperar botón Aceptar
            btn_aceptar = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[contains(@class,'x-window-dlg')]//button[normalize-space()='Aceptar']"
                ))
            )
            btn_aceptar.click()
            logging.info("🖱️ Clic en Aceptar")
            #----------------------------
            # esperar que NO exista el overlay
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ext-el-mask")))
            logging.info("✅ Carga finalizada")
            #----------------------------
            tomar_capturar(driver,ruta_carpeta,f"despuesDESCUENTO{ctx.id_cot}")
            input("Esperar")

        time.sleep(5)
        #----------------------------
        tab_fraccionamiento = wait.until(EC.element_to_be_clickable((By.XPATH,"//span[contains(@class,'x-tab-strip-text') and normalize-space()='Fraccionamiento']")))
        tab_fraccionamiento.click()
        logging.info("🖱️ Clic en Fraccionamiento")
        #----------------------------
        time.sleep(5)
        #ingresar_fecha_extjs(driver,wait,name="fecinicertificado",fecha_ddmmyyyy="16/03/2026",texto=f"Fecha de Inicio de Certificado")
        #click_fuera(driver)
        tipo_cuenta = "Cuenta de Ahorros" if ctx.cliente.tipo_persona.upper() == "NATURAL" else "Cuenta Corriente"
        tiempo_12 = ctx.credito.tiempo == "12 MESES"
        es_juridica = ctx.cliente.tipo_persona.upper() == "JURIDICA"

        tipo_plan = "PLAN CC CNT PERSONA JURIDICA" if es_juridica else ("PLAN 2020 CC PN 0% USD 12 CUOTAS" if tiempo_12 else "PLAN CC CNT PERSONA NATURAL")

        escribir_y_enter_combo_por_name(driver, wait, "ideplanfinanciamiento",tipo_plan,2)
        logging.info(f"🖱️ Opción seleccionada para Tipo de Plan → '{tipo_plan}'")
        time.sleep(1)
        #----------------------------
        escribir_input_por_name(driver, wait, "numcuotas", ctx.credito.cuotas,False)
        time.sleep(1)
        #----------------------------
        escribir_y_enter_combo_por_name(driver, wait, "idetipotarjeta",tipo_cuenta,2)
        logging.info(f"🖱️ Clic en tipo de cuenta → {tipo_cuenta}")
        time.sleep(3)
        #----------------------------
        fecha_ddmmyyyy = (datetime.strptime(get_pos_fecha_dmy(), "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y")
        ingresar_fecha_extjs(driver,wait,name="fecprimvcto",fecha_ddmmyyyy=fecha_ddmmyyyy,texto=f"Fecha primer vencimiento")
        time.sleep(3)
        #----------------------------
        click_fuera(driver)
        #----------------------------
        btn_generar = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Generar']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_generar)
        driver.execute_script("arguments[0].click();", btn_generar)
        logging.info("🖱️ Clic en 'Generar'")
        time.sleep(5)
        #----------------------------
        btn_ing_cliente = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Ingresar Cliente']")))
        driver.execute_script("arguments[0].click();", btn_ing_cliente)
        logging.info("🖱️ Clic en 'Ingresar Cliente'")
        time.sleep(5)
        #----------------------------
        wait.until(EC.presence_of_element_located((By.XPATH,"//li[contains(@class,'x-tab-strip-active')]//span[normalize-space()='Cliente']")))
        logging.info("✅ Tab 'Cliente' activa")
        #----------------------------
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR,"div.ext-el-mask, div.ext-el-mask-msg")))
        logging.info("✅ Carga finalizada")   
        #----------------------------
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"div.x-panel-body div.x-toolbar")))
        logging.info("✅ Toolbar del grid cargado")
        #----------------------------
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR,"div.ext-el-mask, div.ext-el-mask-msg")))
        logging.info("✅ Carga finalizada")  
        #----------------------------
        click_agregar_cliente_extjs(driver)
        logging.info("🖱️ Clic en 'Agregar'")
        #----------------------------
        titulo_modal = obtener_titulo_modal_extjs(driver, wait)

        if titulo_modal is None:
            raise Exception("No apareció modal para registrar cliente")

        time.sleep(5)
        #------- MODAL NUEVO ASEGURADO PARA CAMBIAR TIPO DE PERSONA Y TIPO DE DOCUMENTO ----------------------
        try:

            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x-window[style*='visibility: visible']")))

            def escribir_combo_extjs(wait, name_hidden, texto, valor_esperado=None):

                combo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,f"input[name='{name_hidden}'] + input")))
                combo.click()
                logging.info(f"🖱️ Clic en '{name_hidden}' ")

                try:
                    combo.send_keys(Keys.CONTROL, "a")
                    logging.info(f"🖱️ Seleccionando todo el combo '{name_hidden}'")
                except:
                    pass

                try:
                    combo.clear()
                    logging.info(f"✅ Eliminando contenido del combo '{name_hidden}'")
                except:
                    pass

                combo.send_keys(texto)
                time.sleep(2)
                try:
                    combo.send_keys(Keys.ENTER)
                    logging.info("✅ El combo aceptó ENTER")
                except:
                    pass
                finally:
                    time.sleep(2)

                # if valor_esperado is not None:
                #     hidden = driver.find_element(By.NAME, name_hidden)

                #     try:
                #         wait.until(
                #             lambda d: hidden.get_attribute("value") == valor_esperado
                #         )
                #     except TimeoutException:
                #         combo.send_keys(Keys.TAB)

                #         wait.until(
                #             lambda d: hidden.get_attribute("value") == valor_esperado
                #         )

                # logging.info(f"✅ Combo '{name_hidden}' seleccionado: {texto}")

            # valor_esperado_idptipotercero = "J" if es_juridica else "N"
            escribir_combo_extjs(wait,"idptipotercero","PERSONA JURÍDICA" if es_juridica else "PERSONA NATURAL",valor_esperado="J" if es_juridica else "N")
            time.sleep(2)

            # dispatch_tipo_doc = {
            #     "RUC": "1",
            #     "DNI": "2",
            #     "PASAPORTE": "3",
            #     "C.E.": "4"
            # }

            # valor_esperado_idptipodocumento = dispatch_tipo_doc.get(ctx.cliente.tipo_doc.upper())

            # if valor_esperado_idptipodocumento is None:
            #     raise Exception(f"Tipo de documento '{ctx.cliente.tipo_doc}' no soportado en la compañía")

            escribir_combo_extjs(wait,"idptipodocumento",ctx.cliente.tipo_doc)

        except Exception as e:
            raise Exception(f"Error seleccionando tipo de tercero o documento | Motivo: {e}")
        #-----------------------------------------------------------------------------------------------------

        time.sleep(5)

        #--- Por Mientras ---
        ruc_cot_ej = os.getenv("ruc_cot")
        escribir_input_en_modal(driver,wait,"numerodoc",ruc_cot_ej if es_juridica else ctx.cliente.num_doc,True)

        time.sleep(3)

        click_boton_buscar_en_modal_extjs(driver)

        time.sleep(3)
        
        campo_nombre = wait.until(EC.presence_of_element_located((By.NAME, "nombre")))

        es_readonly = campo_nombre.get_attribute("readonly") is not None

        if es_readonly:
            logging.info("✅ El formulario quedó bloqueado (readonly), No se completan más datos.")
        else:
            logging.info("⚠️ El formulario sigue editable. Se completan los demás datos.")

            #------- MODAL PARA COMPLETAR DATOS NUEVOS DEL CLIENTE -------
            if ctx.cliente.cliente_nuevo:
                logging.warning("⚠️ El asesor marco que es cliente nuevo, pero ya existe en la BD de la compañía")

            set_valor_campo_extjs(driver, wait, "nombre", ctx.cliente.nombres)
            time.sleep(1)
            #----------------------------------------------------------------
            set_valor_campo_extjs(driver, wait, "apepaterno", ctx.cliente.apellido_paterno)
            time.sleep(1)
            #----------------------------------------------------------------
            set_valor_campo_extjs(driver, wait, "apematerno", ctx.cliente.apellido_materno)
            time.sleep(1)
            #----------------------------------------------------------------
            # ACA FALTA ESTADO CIVIL
            #----------------------------------------------------------------
            driver.execute_script("""
                var radio = document.querySelector(
                    "input[name='idpgenero'][value='" + arguments[0] + "']"
                );

                radio.checked = true;

                radio.dispatchEvent(new Event('click', {bubbles:true}));
                radio.dispatchEvent(new Event('change', {bubbles:true}));
                """, ctx.cliente.sexo)
            logging.info(f"✅ Radio 'Sexo' = '{ctx.cliente.sexo}'")
            time.sleep(2)
            #----------------------------------------------------------------
            driver.execute_script("""
            var win = Ext.WindowMgr.getActive();

            var campo = win.find("name", "fecnacimiento")[0];

            campo.setValue(arguments[0]);
            campo.fireEvent('change', campo, arguments[0]);
            """, ctx.cliente.fecha_nac)
            logging.info(f"✅ Fecha Nacimiento = '{ctx.cliente.fecha_nac}'")
            time.sleep(1)
            #----------------------------------------------------------------
            abrir_combo_en_fieldset(driver, "Direcciones", "idedistrito")
            time.sleep(1)
            #----------------------------------------------------------------
            seleccionar_combo_extjs(wait, ctx.vehiculo.distrito_veh)
            time.sleep(1)
            #----------------------------------------------------------------
            abrir_combo_en_fieldset(driver, "Direcciones", "idptipovia")
            time.sleep(1)
            #----------------------------------------------------------------
            seleccionar_combo_extjs(wait, ctx.cliente.tipo_via)
            time.sleep(1)
            #----------------------------------------------------------------
            driver.execute_script("""
                var campo = document.querySelector("input[name='nomvia']");

                if(!campo)
                    throw "No existe nomvia";

                campo.value = arguments[0];

                campo.dispatchEvent(new Event('input', {bubbles:true}));
                campo.dispatchEvent(new Event('change', {bubbles:true}));
                """, ctx.cliente.nom_via)
            logging.info(f"⌨️ Digitando Nombre de Via : {ctx.cliente.nom_via}")
            time.sleep(1)
            #----------------------------------------------------------------
            driver.execute_script("""
                var campo = document.querySelector("input[name='numcasa']");

                if(!campo)
                    throw "No existe numcasa";

                campo.value = arguments[0];

                campo.dispatchEvent(new Event('input', {bubbles:true}));
                campo.dispatchEvent(new Event('change', {bubbles:true}));
                """, ctx.cliente.num_via)
            logging.info(f"⌨️ Digitando Numero de Via : {ctx.cliente.num_via}")
            time.sleep(1)
            #----------------------------------------------------------------
            set_valor_campo_extjs(driver, wait, "numtelefcasa", ctx.cliente.celular) #numtelefmovil
            time.sleep(1)
            #----------------------------------------------------------------
            set_valor_campo_extjs(driver, wait, "emailpersonal", ctx.cliente.correo) #emailtrabajo
            #----------------------------------------------------------------
            click_boton_grabar_en_modal_extjs(driver,wait)

            mensaje = aceptar_messagebox_extjs(driver, wait)

            if "Satisfactoriamente" in mensaje:
                logging.info("✅ Operación exitosa")

                #--- PROBANDO SI ES UN CLIENTE NUEVO Y LOS DATOS SON CORRECTOS---
                try:
                    # Clic en Aceptar mediante ExtJS
                    driver.execute_script("""
                        var win = Ext.WindowMgr.getActive();

                        if(!win)
                            throw "No existe MessageBox";

                        var btn = null;

                        win.buttons.each(function(b){
                            if(b.text === "Aceptar"){
                                btn = b;
                            }
                        });

                        if(!btn)
                            throw "No existe botón Aceptar";

                        btn.fireEvent('click', btn);
                    """)

                    logging.info("🖱️ Botón Aceptar presionado -1")       
                    time.sleep(3)
                    click_boton_toolbar_extjs(driver, wait, "tb-exit")

                    logging.info("Funciono el primero OJO")
                except:

                    responder_mensaje(driver, wait, "Aceptar")

                    try:
                        # Esperar que desaparezca el MessageBox
                        wait.until(
                            EC.invisibility_of_element_located((
                                By.XPATH,
                                "//div[contains(@class,'x-window-dlg') and .//span[contains(@class,'ext-mb-text')]]"
                            ))
                        )

                        logging.info("✅ MessageBox cerrado")
                    except:
                        time.sleep(10)
                        logging.info("✅ Se espero 10 segundos")
                    #----------------------------------------------
                    try:
                        # Esperar que exista la ventana Persona Natural
                        ventana = wait.until(
                            lambda d: next(
                                (
                                    v for v in d.find_elements(By.CSS_SELECTOR, "div.x-window")
                                    if v.is_displayed()
                                    and v.find_element(
                                        By.CSS_SELECTOR,
                                        ".x-window-header-text"
                                    ).text.strip() != "Nuevo Asegurado"
                                ),
                                None
                            )
                        )

                    except:

                        titulo_esperado = f"{ctx.cliente.nombres} {ctx.cliente.apellido_paterno} {ctx.cliente.apellido_materno}".upper()

                        ventana = wait.until(
                            lambda d: next(
                                (
                                    v for v in d.find_elements(By.CSS_SELECTOR, "div.x-window")
                                    if v.is_displayed()
                                    and titulo_esperado in v.find_element(
                                        By.CSS_SELECTOR,
                                        ".x-window-header-text"
                                    ).text.upper()
                                ),
                                None
                            )
                        )

                    titulo = ventana.find_element(By.CSS_SELECTOR,".x-window-header-text").text

                    logging.info(f"✅ Ventana encontrada: {titulo}")

                    # Buscar el botón Salir SOLO dentro de esa ventana
                    boton = ventana.find_element(By.CSS_SELECTOR,"button.tb-exit")

                    wait.until(lambda d: boton.is_displayed() and boton.is_enabled())

                    driver.execute_script("arguments[0].click();", boton)

                    logging.info("🖱️ Clic en Salir")

                    logging.info("Funciono el segundo OJO")

            elif "input" in mensaje:
                raise Exception(f"{mensaje}")
            else:
      
                logging.warning(f"⚠️ Mensaje : {mensaje}")

                #if "datos fueron observados" not in mensaje:

                time.sleep(5)

                aviso = wait.until(EC.visibility_of_element_located((By.XPATH,"//div[contains(@class,'x-window')][.//span[text()='Aviso']]")))

                boton = aviso.find_element(By.XPATH,".//button[normalize-space()='Sí']")
                boton.click()
                logging.info(f"🖱️ Clic en 'Sí'")

                time.sleep(5)

                click_boton_ventana(driver,wait,"Validación de tercero","Cargar datos",ctx)
            
            #-------------------------------------------------------------

        time.sleep(10)
        click_boton_grabar_en_modal_extjs(driver,wait)
        time.sleep(5)

        btn_gen_coti = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Generar Cotización']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_gen_coti)
        driver.execute_script("arguments[0].click();", btn_gen_coti)
        logging.info("🖱️ Clic en 'Generar Cotización'")

        time.sleep(5)

        btn_si = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Sí']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_si)
        driver.execute_script("arguments[0].click();", btn_si)
        logging.info("🖱️ Clic en 'Sí'")
        #-------------------------------------------------------------------------------------
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
            logging.info("✅ Carga finalizada")
        except TimeoutException: 
            raise Exception("Tiempo de espera excedido al Generar Cotización")
        #-------------------------------------------------------------------------------------
        time.sleep(10)
        
        # Logica para eliminar los datos de un cliente si en caso no tenemos sus datos completos y queremos que la cotizacion salga sin datos del cliente
        sin_datos_cliente = es_juridica
        if sin_datos_cliente:
            try:
                click_tab_terceros_extjs(driver)
                logging.info("🖱️ Clic en Tab 'Terceros'")
            except Exception as e:
                raise Exception(f"No se encontró la pestaña Terceros | Motivo: {e}")

            time.sleep(10)

            try:

                # filas_visibles = [
                #     f for f in driver.find_elements(By.CSS_SELECTOR, ".x-grid3-row")
                #     if f.is_displayed()
                # ]

                # logging.info(f"Filas visibles: {len(filas_visibles)}")

                time.sleep(5)

                while True:

                    filas = [
                        f for f in driver.find_elements(By.CSS_SELECTOR, ".x-grid3-row")
                        if f.is_displayed()
                    ]

                    total = len(filas)
                    logging.info(f"📊 Filas visibles actuales: {total}")

                    if total == 1:
                        logging.info("✅ Ultima fila no se elimina")
                        break

                    fila = filas[0]

                    driver.execute_script("""arguments[0].scrollIntoView({block:'center'});""", fila)
                    fila.click()
                    logging.info("🖱️ Clic en la fila")

                    time.sleep(3)

                    btn_excluir = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.tb-user-del")))
                    btn_excluir.click()
                    logging.info("🖱️ Clic en Excluir")
                    time.sleep(3)

                    btn_si = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Sí']")))
                    btn_si.click()
                    logging.info("🖱️ Clic en 'Sí'")

                    # 🔥 ESPERAR A QUE CAMBIE LA TABLA (clave)
                    wait.until(lambda d: len([
                        f for f in d.find_elements(By.CSS_SELECTOR, ".x-grid3-row")
                        if f.is_displayed()
                    ]) < total)

            except Exception as e:
                raise Exception(f"Error al eliminar filas | Motivo : {e}")

        # ⏳ esperar máscara ExtJS
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))
        #logging.info("✅ Sin máscara")

        btn_imprimir = (By.XPATH, "//button[contains(@class,'tb-print') and contains(.,'Imprimir')]")
        wait.until(EC.presence_of_element_located(btn_imprimir))
        wait.until(EC.element_to_be_clickable(btn_imprimir))
        driver.find_element(*btn_imprimir).click()
        logging.info("🖱️ Clic en 'Imprimir'")

        archivos_antes = set(os.listdir(ruta_carpeta))
        cotizacion_pdf = esperar_archivos_nuevos(ruta_carpeta,archivos_antes,".pdf",cantidad=1)

        if cotizacion_pdf:
            cotizacion = True
            logging.info(f"✅ Cotización descargada exitosamente")
            ruta_original = cotizacion_pdf[0]
            ruta_final = os.path.join(ruta_carpeta, f"cot_{ctx.id_cot}.pdf")
            os.rename(ruta_original, ruta_final)
            logging.info(f"🔄 Cotización renombrado a 'ct_{ctx.id_cot}.pdf'")
        else:
            raise Exception("No se descargo ninguna cotización")

    except Exception as e:
        logging.info(f"⚠️ Conclusión: {e}")
        tomar_capturar(driver,ruta_carpeta,f"ErrorCotizando_{ctx.id_cot}")
        if ctx.entorno.upper() == "PRODUCCION" :
            enviarCorreoGeneral(ruta_carpeta,ctx)
        renombrar_carpeta(ruta_carpeta)
    finally:

        if driver:
            driver.quit()

        if cotizacion:
            archivo = os.path.join(ruta_carpeta,f"cot_{ctx.id_cot}.pdf")
            logging.info(f"⌛ Enviando Cotizacion al movimiento → {ctx.id_cot}")
            enviar_documento(ctx.id_cot,archivo,"cotizacion")

        if poliza:
            archivo = os.path.join(ruta_carpeta,f"pol_{ctx.id_cot}.pdf")
            logging.info(f"⌛ Enviando Póliza al movimiento → {ctx.id_cot}")
            enviar_documento(ctx.id_cot,archivo,"poliza")

#-------------------------------------------

if __name__ == "__main__":
    main()   