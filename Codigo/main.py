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
from Carpeta.rutas import esperar_archivos_nuevos,crear_carpeta_descargas

from Metodos.funciones import escribir_input_en_modal, click_boton_buscar_en_modal_extjs
from Metodos.funciones import click_boton_grabar_en_modal_extjs,click_tab_terceros_extjs
from Metodos.funciones import escribir_y_enter_combo_por_name, seleccionar_modelo_extjs
from Metodos.funciones import escribir_input_por_name, click_fuera, seleccionar_combo_por_flecha
from Metodos.funciones import click_agregar_cliente_extjs, obtener_titulo_modal_extjs
from Metodos.funciones import ingresar_fecha_extjs,limpiar,interactuar_combo_por_name,resolver_empresa
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
    data["SOAT"] = to_bool(data.get("SOAT"))
    data["INSPECCION"] = to_bool(data.get("INSPECCION"))
    data["CLIENTE_NUEVO"] = to_bool(data.get("CLIENTE_NUEVO"))
    data["ASIENTOS"] = safe_int(data.get("ASIENTOS"))
    data["PRECIO"] = safe_float(data.get("PRECIO"))
    return data

data = normalizar_data(data)

# ------------------ CLASES ---------------

class Vehiculo:
    def __init__(self, data: dict):

        self.organizacion = data.get("ORGANIZACION")
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

        self.num_rodaje = data.get("NUM_RODAJE")
        self.num_motor = data.get("NUM_MOTOR")
        self.num_serie = data.get("NUM_SERIE")

    def __str__(self):
        return f"{self.modelo}|{self.marca}|{self.tipo}|{self.clase}"

class Usuario:
    def __init__(self, data: dict):
        self.usuario = data.get("USUARIO")
        self.contrasena = data.get("CONTRASEÑA")
        self.rol = data.get("ROL")
        self.canal = data.get("CANAL")
        #self.vendedor = data.get("VENDEDOR")

class Credito:
    def __init__(self, data: dict):
        self.tiempo = data.get("TIEMPO_CREDITO")
        self.seguro = data.get("SOAT")
        self.inspeccion = data.get("INSPECCION")

class Cliente:
    def __init__(self, data: dict):
        self.rz_social = data.get("RAZON_SOCIAL")
        self.nombres = data.get("NOMBRES")
        self.apellido_paterno = data.get("APE_PATERNO")
        self.apellido_materno = data.get("APE_MATERNO")
        self.tipo_persona = data.get("TIP_PERSONA")
        self.tipo_doc = data.get("TIP_DOC")
        self.num_doc = data.get("NOM_DOC")
        fecha = data.get("FECHA_NAC")
        self.fecha_nac = datetime.strptime(fecha, "%d-%m-%Y").strftime("%d/%m/%Y") if fecha else None
        self.sexo = data.get("SEXO")
        self.estado_civil = data.get("ESTADO_CIVIL")
        self.tipo_via = data.get("TIPOVIA")
        self.nom_via = data.get("NOMBREVIA")
        self.num_via = data.get("NUMEROVIA")
        self.cliente_nuevo = data.get("CLIENTE_NUEVO")

class CotizacionContexto:

    def __init__(self, data: dict):

        self.entorno = data.get("entorno")
        self.id_cot = data.get("ID_COT")
        self.solicitud = data.get("solicitud")
        self.usuario = Usuario(data)
        self.vehiculo = Vehiculo(data)
        self.credito = Credito(data)
        self.cliente = Cliente(data)

        self.organizacion = data.get("ORGANIZACION") or ""
        self.plan = data.get("PLAN")
        self.localizacion = data.get("LOCALIZACION_CARRO")
        self.distrito_veh = data.get("DISTRITO_CARRO")

    def __str__(self):
        return pformat({
            "usuario": self.usuario.__dict__,
            "vehiculo": self.vehiculo.__dict__,
            "credito": self.credito.__dict__,
            "cliente": self.cliente.__dict__,
            "plan": self.plan,
            "localizacion": self.localizacion,
            "organizacion": self.organizacion
        })

# ------------------ USO ------------------
ctx = CotizacionContexto(data)
#------------------------------------------

def main():

    poliza = False
    cotizacion = False
    driver = None

    nom_empresa = resolver_empresa(ctx.organizacion)

    ruta_carpeta = crear_carpeta_descargas(nom_empresa, ctx.id_cot,ctx.solicitud)

    try:

        display_num = os.getenv("DISPLAY_NUM", "0")
        os.environ["DISPLAY"] = f":{display_num}"

        driver,wait = abrirDriver(ruta_carpeta)

        driver.get(os.getenv("urlRimacSAS"))
        logging.info("🔐 Iniciando sesión en RIMAC SAS")
 
        user_input = wait.until(EC.presence_of_element_located((By.ID, "CODUSUARIO")))
        user_input.clear()
        user_input.send_keys(ctx.usuario.usuario)
        logging.info("⌨️ Usuario digitando")

        time.sleep(1)
 
        pass_input = wait.until(EC.presence_of_element_located((By.ID, "CLAVE")))
        pass_input.clear()
        password = os.getenv("passwordRimac") if ctx.entorno.upper() == "LOCAL" else ctx.usuario.contrasena
        pass_input.send_keys(password)
        logging.info(f"⌨️ Password {password} digitado")
 
        ingresar_btn = wait.until(EC.element_to_be_clickable((By.ID, "btningresar")))
        driver.execute_script("arguments[0].click();", ingresar_btn)
        logging.info("🖱️ Clic en 'Ingresar'")

        codigo_path = "/codigo_rimac_SAS/codigo.txt"
 
        logging.info("⏳ Esperando código")
        while not os.path.exists(codigo_path):
            time.sleep(2)
 
        with open(codigo_path, "r") as f:
            codigo = f.read().strip()
 
        logging.info(f"✅ Código recibido desde volumen: {codigo}")

        logging.info("⌛ Buscando input 'TOKEN'")
        token_input = wait.until(EC.presence_of_element_located((By.ID, "TOKEN")))
        token_input.clear()
        token_input.send_keys(codigo)
        logging.info(f"⌨️ Código {codigo} digitado correctamente en 'TOKEN'")

        try:
            os.remove(codigo_path)
        except FileNotFoundError:
            raise Exception(" No se encontró código al intentar eliminarlo (ya fue borrado)")
        except Exception as e:
            raise Exception(f" Error al eliminar código : {e}")

        ingresar_btn2 = wait.until(EC.element_to_be_clickable((By.ID, "btningresar")))
        driver.execute_script("arguments[0].click();", ingresar_btn2)
        logging.info("🖱️ Clic en 'Ingresar' Luego del TOKEN.")

        actions = ActionChains(driver)
        span_transacciones = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Transacciones']")))
        actions.double_click(span_transacciones).perform()
        logging.info("🖱️ Doble clic realizado en 'Transacciones'")
 
        span_emision = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Cotizar']")))
        actions.double_click(span_emision).perform()
        logging.info("🖱️ Doble clic realizado en 'Cotizar'")
 
        span_mantenimiento = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Registrar Cotización']")))
        span_mantenimiento.click()
        logging.info("🖱️ Clic realizado en 'Registrar Cotización'")

        logging.info("------------------------------------")
        time.sleep(10)
        interactuar_combo_por_name(driver, wait, "iderolcanal", "CANAL NO TRADICIONAL") # ctx.usuario.rol
        time.sleep(5)
        interactuar_combo_por_name(driver, wait, "idecanal", ctx.usuario.canal.upper())
        time.sleep(3)
        click_fuera(driver)
        time.sleep(3)

        if ctx.plan.upper() == "PARTICULAR":
            opcTaxi = "[511266] - CANAL DONGFENG TR (25-03-2026) - SAS"
        else:
            opcTaxi = "[497816] - CANAL DONGFENG - TAXI (25-03-2026) - SAS"

        seleccionar_combo_por_flecha(driver,wait,"ideplanselected",opcTaxi)
        time.sleep(3)
        click_fuera(driver)
        time.sleep(3)
        logging.info("------------------------------------")
        boton = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Generar Datos Particulares']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)
        driver.execute_script("arguments[0].click();", boton)
        logging.info("🖱️ Clic en 'Generar Datos Particulares'")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
        logging.info("✅ Carga finalizada")   
        logging.info("------------------------------------")

        escribir_input_por_name(driver, wait, "txtplaca_de_rodaje",ctx.vehiculo.num_rodaje,False)
        time.sleep(1)
        escribir_input_por_name(driver, wait, "txtnumero_de_motor",ctx.vehiculo.num_motor,False)
        time.sleep(1)
        escribir_input_por_name(driver, wait, "txtnumero_de_serie",ctx.vehiculo.num_serie,False)
        time.sleep(1)

        logging.info(f"🚗 Vehículo a buscar: {ctx.vehiculo}")

        modelo = limpiar(ctx.vehiculo.modelo)
        marca = limpiar(ctx.vehiculo.marca)
        tipo = limpiar(ctx.vehiculo.tipo)
        clase = limpiar(ctx.vehiculo.clase)

        texto_busqueda = modelo
        texto_opcion = f"{modelo}|{marca}|{tipo}|{clase}"

        seleccionar_modelo_extjs(driver,wait,texto_busqueda=texto_busqueda,texto_opcion=texto_opcion)
        time.sleep(3)
        escribir_input_por_name(driver, wait, "txtweb_anos_de_fabricacion",ctx.vehiculo.anio,False)
        time.sleep(1)
        escribir_input_por_name(driver, wait, "txtsuma_asegurada",ctx.vehiculo.valor,False)
        time.sleep(1)
        escribir_y_enter_combo_por_name(driver,wait,"selusos_de_vehiculos",ctx.vehiculo.uso,1)
        time.sleep(3)
        escribir_y_enter_combo_por_name(driver,wait,"selcombustible_gas",{'SI' if ctx.vehiculo.gas == 'GAS' else 'NO'},1)
        time.sleep(3)
        escribir_input_por_name(driver, wait, "txtnro_pasajeros",ctx.vehiculo.ocupantes,False)
        time.sleep(1)
        escribir_y_enter_combo_por_name(driver,wait,"selprocedenciaexterna",{'SI' if ctx.credito.seguro else 'NO'},1) 
        time.sleep(3)
        escribir_y_enter_combo_por_name(driver,wait,"selrequiereinspeccion",{'SI' if ctx.credito.inspeccion else 'NO'},1) 

        if ctx.vehiculo.uso == 'PARTICULAR':
            time.sleep(3)
            escribir_y_enter_combo_por_name(driver,wait,"seltipo_de_persona",ctx.cliente.tipo_persona,2)
            time.sleep(3)
            escribir_y_enter_combo_por_name(driver,wait,"seltiempo_de_credito",ctx.credito.tiempo,2)
            time.sleep(3)
            escribir_input_por_name(driver, wait, "txtvendedor", "CAMILA AGUIRRE",False)
            time.sleep(1)
            escribir_y_enter_combo_por_name(driver,wait,"sellocalización",{'LIMA' if ctx.localizacion == 'LIMA' else 'PROVINCIAS'},2)

        #-------------------------
        time.sleep(3)
        btn_cal = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Calcular Planes']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_cal)
        driver.execute_script("arguments[0].click();", btn_cal)
        logging.info("🖱️ Clic en 'Calcular Planes'")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
        logging.info("✅ Carga finalizada")

        logging.info("------------------------------------")

        fieldset_plan = wait.until(EC.presence_of_element_located((By.XPATH, "//fieldset[.//span[normalize-space()='Plan 1']]")))
        wait.until(EC.visibility_of(fieldset_plan))
        logging.info("✅ Plan localizado y visible")

        boton_seleccionar = wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[normalize-space()='Seleccionar'] | .//a[normalize-space()='Seleccionar']")))
        driver.execute_script("arguments[0].click();", boton_seleccionar)
        logging.info("🖱️ Clic en Seleccionar")

        tab_fraccionamiento = wait.until(EC.element_to_be_clickable((By.XPATH,"//span[contains(@class,'x-tab-strip-text') and normalize-space()='Fraccionamiento']")))
        tab_fraccionamiento.click()
        logging.info("🖱️ Clic en Fraccionamiento")

        # esperar que NO exista el overlay
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ext-el-mask")))

        #ingresar_fecha_extjs(driver,wait,name="fecinicertificado",fecha_ddmmyyyy="16/03/2026")

        #click_fuera(driver)

        escribir_y_enter_combo_por_name(driver, wait, "ideplanfinanciamiento", "PLAN 2020 CC PN 0% USD 12 CUOTAS",2)
        time.sleep(1)
        escribir_y_enter_combo_por_name(driver, wait, "idetipotarjeta", "Cuenta de Ahorros",2)

        fecha_ddmmyyyy = (datetime.strptime(get_pos_fecha_dmy(), "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y")
        ingresar_fecha_extjs(driver,wait,name="fecprimvcto",fecha_ddmmyyyy=fecha_ddmmyyyy)

        click_fuera(driver)

        time.sleep(3)
        btn_generar = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Generar']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_generar)
        driver.execute_script("arguments[0].click();", btn_generar)
        logging.info("🖱️ Clic en 'Generar'")

        time.sleep(5)

        btn_ing_cliente = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Ingresar Cliente']")))
        driver.execute_script("arguments[0].click();", btn_ing_cliente)
        logging.info("🖱️ Clic en 'Ingresar Cliente'")

        time.sleep(5)

        wait.until(EC.presence_of_element_located((By.XPATH,"//li[contains(@class,'x-tab-strip-active')]//span[normalize-space()='Cliente']")))
        logging.info("✅ Tab 'Cliente' activa")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR,"div.ext-el-mask, div.ext-el-mask-msg")))
        #logging.info("esperar que NO haya máscara ExtJS")

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"div.x-panel-body div.x-toolbar")))
        logging.info("✅ Toolbar del grid cargado")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR,"div.ext-el-mask, div.ext-el-mask-msg")))
        #logging.info("✅ No hay máscara ExtJS")

        click_agregar_cliente_extjs(driver)
        logging.info("🖱️ Clic en 'Agregar'")

        titulo_modal = obtener_titulo_modal_extjs(driver, wait)

        if titulo_modal is None:
            raise Exception("No apareció modal para registrar cliente")

        #logging.info(f"ℹ️ Modal '{titulo_modal}' → trabajar dentro del modal")

        time.sleep(5)

        escribir_input_en_modal(driver,wait,"numerodoc",73049468,True) #73049468 numerodoc

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
                logging.info("🖱️ Click en Excluir")
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
        enviarCorreoGeneral(str(e),ruta_carpeta,ctx.id_cot,ctx.solicitud.capitalize())
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