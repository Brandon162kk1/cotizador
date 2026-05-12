# -*- coding: utf-8 -*-
# -- Froms ---
from datetime import timedelta,datetime
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from pprint import pformat
from Tiempo.fechas_horas import get_pos_fecha_dmy
from Apis.put import enviar_documento
from Apis.post import enviarCorreoGeneral
from Chrome.driver import tomar_capturar,abrirDriver
from Carpeta.rutas import esperar_archivos_nuevos,crear_carpeta_descargas,renombrar_carpeta

from Metodos.funciones import resolver_empresa,interactuar_combo_por_name,click_fuera,seleccionar_combo_por_flecha,escribir_input_por_name,limpiar,seleccionar_modelo_extjs
from Metodos.funciones import escribir_y_enter_combo_por_name,ingresar_fecha_extjs,click_agregar_cliente_extjs,obtener_titulo_modal_extjs,click_boton_buscar_en_modal_extjs
from Metodos.funciones import escribir_input_en_modal,click_boton_grabar_en_modal_extjs,click_tab_terceros_extjs

from Apis.get import codigo_compania

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

        if self.organizacion and "dongfeng" in self.organizacion.lower():
            self.marca = "DONG FENG"
        else:
            self.marca = "PANGU"

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
        return f"{self.modelo}|{self.marca}|{self.tipo}|{self.clase}"

class Usuario:
    def __init__(self, data: dict):

        self.usuario = data.get("USUARIO")
        self.contrasena = data.get("CONTRASEÑA")
        self.rol = data.get("ROL")
        self.canal = data.get("CANAL")
        self.correo_asesor = data.get("CORREO_ASESOR")

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

        driver.get(os.getenv("urlRimacSAS"))
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

        codigo = codigo_compania()

        token_input = wait.until(EC.presence_of_element_located((By.ID, "TOKEN")))
        token_input.clear()
        token_input.send_keys(codigo)
        logging.info(f"⌨️ Digitando {codigo} correctamente en 'TOKEN'")

        ingresar_btn2 = wait.until(EC.element_to_be_clickable((By.ID, "btningresar")))
        driver.execute_script("arguments[0].click();", ingresar_btn2)
        logging.info("🖱️ Clic en 'Ingresar'")

        #----------------------------
        actions = ActionChains(driver)
        span_transacciones = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Transacciones']")))
        actions.double_click(span_transacciones).perform()
        logging.info("🖱️ Doble clic realizado en 'Transacciones'")
        time.sleep(3)
        #----------------------------
        span_emision = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Cotizar']")))
        actions.double_click(span_emision).perform()
        logging.info("🖱️ Doble clic realizado en 'Cotizar'")
        time.sleep(3)
        #----------------------------
        span_mantenimiento = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Registrar Cotización']")))
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
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
        logging.info("✅ Carga finalizada")   
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
        logging.info(f"🖱️ Opción seleccionada para el uso de vehiculos → '{ctx.vehiculo.uso}'")
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
            logging.info(f"🖱️ Opción seleccionada para Tipo de persona → '{ctx.cliente.tipo_persona}'")
            time.sleep(3)
            #----------------------------
            escribir_y_enter_combo_por_name(driver,wait,"seltiempo_de_credito",ctx.credito.tiempo,2)
            logging.info(f"🖱️ Opción seleccionada para el tiempo de credito → '{ctx.credito.tiempo}'")
            time.sleep(3)
            #----------------------------
            escribir_input_por_name(driver, wait, "txtvendedor", "CAMILA AGUIRRE",False)
            time.sleep(1)
            #----------------------------
            localizacion = 'LIMA' if ctx.vehiculo.localizacion == 'LIMA' else 'PROVINCIAS'
            escribir_y_enter_combo_por_name(driver,wait,"sellocalización",localizacion,2)
            logging.info(f"🖱️ Opción seleccionada en localización → '{localizacion}'")
            time.sleep(3)
        #----------------------------
        btn_cal = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Calcular Planes']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_cal)
        driver.execute_script("arguments[0].click();", btn_cal)
        logging.info("🖱️ Clic en 'Calcular Planes'")
        #----------------------------
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
        logging.info("✅ Carga finalizada")
        #----------------------------
        fieldset_plan = wait.until(EC.presence_of_element_located((By.XPATH, "//fieldset[.//span[normalize-space()='Plan 1']]")))
        wait.until(EC.visibility_of(fieldset_plan))
        logging.info("✅ Plan localizado y visible")
        #----------------------------
        boton_seleccionar = wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[normalize-space()='Seleccionar'] | .//a[normalize-space()='Seleccionar']")))
        driver.execute_script("arguments[0].click();", boton_seleccionar)
        logging.info("🖱️ Clic en Seleccionar")
        #----------------------------
        tab_fraccionamiento = wait.until(EC.element_to_be_clickable((By.XPATH,"//span[contains(@class,'x-tab-strip-text') and normalize-space()='Fraccionamiento']")))
        tab_fraccionamiento.click()
        logging.info("🖱️ Clic en Fraccionamiento")
        #----------------------------
        # esperar que NO exista el overlay
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ext-el-mask")))
        logging.info("✅ Carga finalizada")   
        #----------------------------
        #ingresar_fecha_extjs(driver,wait,name="fecinicertificado",fecha_ddmmyyyy="16/03/2026",texto=f"Fecha de Inicio de Certificado")
        #click_fuera(driver)
        tipo_cuenta = "Cuenta de Ahorros" if ctx.cliente.tipo_persona.upper() == "NATURAL" else "Cuenta Corriente"
        tiempo_12 = ctx.credito.tiempo == "12 MESES"
        es_juridica = ctx.cliente.tipo_persona.upper() == "JURIDICA"

        if es_juridica:
            tipo_plan = "PLAN CC CNT PERSONA JURIDICA"
        else:
            tipo_plan = (
                "PLAN 2020 CC PN 0% USD 12 CUOTAS"
                if tiempo_12
                else "PLAN CC CNT PERSONA NATURAL"
            )

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
        #--------------------------
        # from Metodos.funciones import cambiar_tipo_persona
        # cambiar_tipo_persona(driver, wait, texto="PERSONA JURÍDICA")
        #--------------------------
        # try:

        #     #modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x-window[style*='visibility: visible']")))
        #     from Metodos.funciones import cambiar_tipo_persona
        #     #seleccionar_combo_extjs(driver, wait, "idptipotercero",f"PERSONA {ctx.cliente.tipo_persona.upper()}")
        #     #seleccionar_combo_extjs(driver, wait, "idptipotercero")
        #     #cambiar_tipo_persona(driver, wait,texto=f"PERSONA {ctx.cliente.tipo_persona.upper()}")
        #     cambiar_tipo_persona(driver, wait, texto="PERSONA JURIDICA")

        #     input("Esperar")
        #     # escribir_y_enter_combo_por_name(driver,wait,"idptipotercero",f"PERSONA {ctx.cliente.tipo_persona.upper()}",1)
        #     # time.sleep(1)
        #     # escribir_y_enter_combo_por_name(driver,wait,"idptipodocumento",f"PERSONA {ctx.cliente.tipo_doc.upper()}",1)
        #     # time.sleep(1)
        # except Exception as e:
        #     raise Exception(f"Error seleccionando tipo de tercero o documento | Motivo: {e}")
        # #--------------------------

        time.sleep(5)
        dni_cot_ej = os.getenv("dni_cot")
        #ruc_cot_ej = os.getenv("ruc_cot")
        #escribir_input_en_modal(driver,wait,"numerodoc",{ruc_cot_ej if ctx.cliente.tipo_doc.upper() == 'RUC' else dni_cot_ej},True)
        escribir_input_en_modal(driver,wait,"numerodoc",dni_cot_ej,True)

        time.sleep(3)

        click_boton_buscar_en_modal_extjs(driver)

        time.sleep(3)

        #-------- POR AHORA ---------
        click_boton_grabar_en_modal_extjs(driver)
        #---------------------
     
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

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
        logging.info("✅ Carga finalizada") 
        #-------- ELIMINAR DATOS DEL DNI PARA QUE SALGA SIN DATOS EN LA COTIZACION -----------

        time.sleep(10)
    
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
            #logging.warning(f"No se pudo eliminar las filas | Motivo: {e}")

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
        enviarCorreoGeneral(str(e),ruta_carpeta,ctx)
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