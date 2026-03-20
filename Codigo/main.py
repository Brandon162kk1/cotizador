# -*- coding: utf-8 -*-
# -- Froms ---
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
# -- Imports --
import logging
import os
import time
import traceback

#------Carpetas de Descargas y Volumen del Docker----------
carpeta_descargas = "Downloads"
ruta_carpeta_descargas = f"/app/{carpeta_descargas}"

# # Forzar la salida en UTF-8 para evitar UnicodeEncodeError
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- Metodos ---
def interactuar_combo_por_name(driver, wait, name_hidden, texto):

    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # 1. Hidden
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # 2. Contenedor
    contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-field-wrap')]")

    # 3. Input visible (1ra vez)
    input_visible = contenedor.find_element(By.XPATH, ".//input[contains(@class,'x-form-field')]")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_visible)
    input_visible.click()
    input_visible.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
    input_visible.send_keys(texto)
    print("⌨️ Digitando texto")

    # 4. Esperar lista
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-combo-list')]")))

    # 5. RE-OBTENER input (ExtJS lo recrea)
    input_visible = contenedor.find_element(By.XPATH, ".//input[contains(@class,'x-form-field')]")

    # 6. Intento normal: ↓ + ENTER
    input_visible.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.2)
    input_visible.send_keys(Keys.ENTER)
    print("↵ Enter enviado")

    # 7. Validar hidden (espera corta)
    try:
        wait.until(lambda d: hidden.get_attribute("value"))
        print(f"✅ Combo '{name_hidden}' confirmado con ENTER")
        return
    except:
        print("⚠️ ENTER no confirmó, usando PLAN B (click directo)")

    # 🧨 PLAN B — click directo en la opción
    opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto}']")))
    opcion.click()
    print("🖱️ Click directo en opción")

    # 8. Validar nuevamente
    wait.until(lambda d: hidden.get_attribute("value"))
    print(f"✅ Combo '{name_hidden}' confirmado por click")

def seleccionar_combo_por_flecha(driver, wait, name_hidden, texto_opcion):

    # asegurar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # 1. hidden por NAME
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # 2. contenedor SOLO de ese combo
    contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-field-wrap')]")

    # 3. flechita (img)
    flecha = contenedor.find_element(By.XPATH, ".//img[contains(@class,'x-form-arrow-trigger')]")

    # 4. click fuerte en la flecha
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", flecha)
    driver.execute_script("arguments[0].click();", flecha)
    print("🖱️ Click en flecha del combo")

    # 5. esperar que aparezca la lista y seleccionar la opción
    opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto_opcion}']")))

    opcion.click()
    print("✅ Opción seleccionada")

    # 6. esperar que ExtJS procese
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # 7. validar que el hidden cambió
    if not hidden.get_attribute("value"):
        raise Exception(f"❌ El combo '{name_hidden}' no se confirmó")

    print(f"🎯 Combo '{name_hidden}' confirmado")

def click_fuera(driver):

    driver.find_element(By.TAG_NAME, "body").click()
    print("🖱️ Click fuera (blur)2")
    time.sleep(5)

def escribir_input_por_name(driver, wait, name, valor,booleano):

    # esperar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))

    input_el = wait.until(EC.element_to_be_clickable((By.NAME, name)))

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_el)
    driver.execute_script("arguments[0].focus();", input_el)
    driver.execute_script("arguments[0].click();", input_el)

    input_el.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
    input_el.send_keys(valor)

    if booleano:
        input_el.send_keys(Keys.TAB)
        input_el.send_keys(Keys.ENTER)

    print(f"⌨️ '{name}' ← {valor}")

def esperar_lista_extjs(wait):
    # esperar layer visible
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x-layer.x-combo-list")))
    print("Espero1")

    # esperar inner
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.x-combo-list-inner")))
    print("Espero2")

    # esperar al menos un item
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.x-combo-list-item")))
    print("Espero3")

def seleccionar_modelo_extjs(driver,wait,texto_busqueda,texto_opcion,name_hidden="selmodelodevehiculo"):

    # 1️⃣ Esperar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))

    # 2️⃣ Hidden REAL
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # 3️⃣ Input visible CORRECTO (anclado al hidden)
    input_visible = hidden.find_element(By.XPATH,"./ancestor::div[contains(@class,'x-form-field-wrap')]//input[@type='text']")

    input_visible.click()
    input_visible.clear()
    input_visible.send_keys(texto_busqueda)

    # 4️⃣ Esperar lista
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-combo-list-inner')]")))

    # 5️⃣ Click EXACTO en la opción
    opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto_opcion}']")))
    opcion.click()

    # 6️⃣ Validar ID numérico
    wait.until(lambda d: hidden.get_attribute("value").isdigit())

    print(f"✅ Modelo seleccionado correctamente | ID={hidden.get_attribute('value')}")

def setear_combo_extjs_real(driver, wait, name_hidden, texto):

    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))

    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-field-wrap')]")
    input_visible = contenedor.find_element(By.XPATH, ".//input[@type='text']")

    driver.execute_script("""
    var input = arguments[0];
    var valor = arguments[1];

    var cmp = Ext.getCmp(input.id) || Ext.ComponentMgr.all.find(function(c){
        return c.el && c.el.dom === input;
    });

    if (!cmp) {
        throw "❌ Combo ExtJS no encontrado";
    }

    cmp.setValue(valor);
    cmp.fireEvent('select', cmp, { data: valor });
    cmp.blur();
    """, input_visible, texto)

    wait.until(lambda d: hidden.get_attribute("value"))

    print(f"✅ Combo ExtJS '{name_hidden}' seteado REALMENTE")

def escribir_y_enter_combo_por_name(driver, wait, name_hidden, texto,veces):

    # 1️⃣ esperar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))

    # 2️⃣ localizar hidden por NAME
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # 3️⃣ subir solo al contenedor de ese combo
    contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-field-wrap')]")

    # 4️⃣ input visible SOLO de ese combo
    input_visible = contenedor.find_element(By.XPATH, ".//input[@type='text' and contains(@class,'x-form-field')]")

    # 5️⃣ focus + click fuerte
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_visible)
    driver.execute_script("arguments[0].focus();", input_visible)
    driver.execute_script("arguments[0].click();", input_visible)
    print("🖱️ Clic en combo")

    # 6️⃣ limpiar y escribir
    input_visible.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
    input_visible.send_keys(texto)
    print("⌨️ Digitando texto")

    # 7️⃣ esperar posibles cargas
    #wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    if veces == 1:
        
        # esperar_lista_extjs(wait)
        # print("cargo la lista")
        # time.sleep(2)
        # input("Esperar")
        # input_visible.send_keys(Keys.ARROW_DOWN)
        # print("⬇️ Flecha abajo (primera opción)")
        # time.sleep(2)
        # input_visible.send_keys(Keys.ENTER)
        # print("↵ Enter enviado")
        # time.sleep(2)


        # 7️⃣ esperar posibles cargas
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

        # 8️⃣ ENTER FUERTE
        input_visible.send_keys(Keys.ENTER)
        print("↵ Enter enviado")

    else:

        # 7️⃣ esperar posibles cargas
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

        # 8️⃣ ENTER FUERTE
        input_visible.send_keys(Keys.ENTER)
        print("↵ Enter enviado")

    # 9️⃣ PEQUEÑA ESPERA lógica (NO sleep)
    wait.until(lambda d: True)

    # 🔁 10️⃣ FALLBACK: seleccionar desde la lista si no confirmó
    if not hidden.get_attribute("value"):
        print("⚠️ Enter no confirmó, intentando selección directa")

        opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and contains(normalize-space(), '{texto.split('|')[0]}')]")))
        opcion.click()
        print("🖱️ Click directo en opción")

    # 11️⃣ validación final
    if not hidden.get_attribute("value"):
        raise Exception(f"❌ Combo '{name_hidden}' no se confirmó")

    print(f"✅ Combo '{name_hidden}' confirmado")

def abrirDriver():
    
    #-----Configuración de Chrome para Selenium -----
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--incognito")
    #chrome_options.add_argument("--headless=new")        
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--no-sandbox')    
    chrome_options.add_argument('--disable-popup-blocking') 
    chrome_options.add_argument("--window-size=1920,1080")  
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Configuracion de descargas y preferencias
    prefs = {
        "download.default_directory": ruta_carpeta_descargas,
        "download.prompt_for_download": False,              
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,        
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "download.extensions_to_open": ""
        }
    chrome_options.add_experimental_option("prefs", prefs)
    #-----------------------------------
    try:
        print("🟡 Iniciando ChromeDriver con webdriver_manager")
        # Usar el ChromeDriver que ya está instalado en el contenedor
        service = Service("/usr/local/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("🟢 ChromeDriver iniciado correctamente")

    except Exception as e:
        print(f"\n❌ Error al iniciar ChromeDriver: {e}")
        raise

    # Espera hasta que cargue el driver
    wait = WebDriverWait(driver, 60)
    return driver, wait    

def main():

    try:

        display_num = os.getenv("DISPLAY_NUM", "0")
        os.environ["DISPLAY"] = f":{display_num}"

        driver,wait = abrirDriver()

        driver.get("https://www.rimac.com.pe/SAS/")
        print("🔐 Iniciando sesión en RIMAC SAS...")
 
        user_input = wait.until(EC.presence_of_element_located((By.ID, "CODUSUARIO")))
        user_input.clear()
        user_input.send_keys("CR1MAQUINOM")
        print("⌨️ Usuario ha sido Digitando.")
 
        pass_input = wait.until(EC.presence_of_element_located((By.ID, "CLAVE")))
        pass_input.clear()
        pass_input.send_keys("Birlik2026+")
        print("⌨️ Password ha sido Digitado")
 
        ingresar_btn = wait.until(EC.element_to_be_clickable((By.ID, "btningresar")))
        driver.execute_script("arguments[0].click();", ingresar_btn)
        print("🖱️ Clic en 'Ingresar'.")

        # --- Esperar código ---
        codigo_path = "/codigo_rimac_SAS/codigo.txt"
 
        print("⏳ Esperando código...")
        while not os.path.exists(codigo_path):
            time.sleep(2)
 
        with open(codigo_path, "r") as f:
            codigo = f.read().strip()
 
        print(f"✅ Código recibido desde volumen: {codigo}")

        # --- Escribir en INPUT TOKEN ---
        print("⌛ Buscando input TOKEN...")
 
        token_input = wait.until(EC.presence_of_element_located((By.ID, "TOKEN")))
        token_input.clear()
        token_input.send_keys(codigo)
 
        print(f"⌨️ Código {codigo} digitado correctamente en TOKEN")

        # --- Eliminar el archivo después de usarlo ---
        try:
            os.remove(codigo_path)
            print("🧹 Archivo codigo.txt eliminado del volumen.")
        except FileNotFoundError:
            logging.warning("⚠️ No se encontró codigo.txt al intentar eliminarlo (ya fue borrado).")
        except Exception as e:
            logging.error(f"❌ Error al eliminar codigo.txt: {e}")

        ingresar_btn2 = wait.until(EC.element_to_be_clickable((By.ID, "btningresar")))
        driver.execute_script("arguments[0].click();", ingresar_btn2)
        print("🖱️ Clic en 'Ingresar' Luego del TOKEN.")

        actions = ActionChains(driver)
        span_transacciones = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Transacciones']")))
        actions.double_click(span_transacciones).perform()
        print("🖱️ Doble clic realizado en 'Transacciones'")
 
        span_emision = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Cotizar']")))
        actions.double_click(span_emision).perform()
        print("🖱️ Doble clic realizado en 'Cotizar'")
 
        span_mantenimiento = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Registrar Cotización']")))
        span_mantenimiento.click()
        print("🖱️ Clic realizado en 'Registrar Cotización'")

        print("------------------------------------")

        time.sleep(10)

        interactuar_combo_por_name(driver, wait, "iderolcanal", "CANAL NO TRADICIONAL")
        time.sleep(5)
        interactuar_combo_por_name(driver, wait, "idecanal", "DONFGENF MOTOR PERU S.A.C.")
        time.sleep(3)
        click_fuera(driver)
        time.sleep(3)

        taxi = False
        if taxi:
            opcTaxi = "[497816] - CANAL DONGFENG - TAXI (10-11-2025) - SAS"
        else:
            opcTaxi = "[497817] - CANAL DONGFENG TR (10-11-2025) - SAS"

        seleccionar_combo_por_flecha(driver,wait,"ideplanselected",opcTaxi)
        time.sleep(3)
        click_fuera(driver)
        time.sleep(3)

        boton = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Generar Datos Particulares']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)
        driver.execute_script("arguments[0].click();", boton)
        print("🖱️ Clic en 'Generar Datos Particulares'")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
        print("✅ Carga finalizada (mask desapareció)")
        
        print("----------------------------")

        #---------- From---------------

        escribir_input_por_name(driver, wait, "txtplaca_de_rodaje", "SIN DATO",False)
        time.sleep(1)
        escribir_input_por_name(driver, wait, "txtnumero_de_motor", "SIN DATO",False)
        time.sleep(1)
        escribir_input_por_name(driver, wait, "txtnumero_de_serie", "SIN DATO",False)
        time.sleep(1)

        seleccionar_modelo_extjs(driver,wait,texto_busqueda="SX6",texto_opcion="SX6|DONG FENG|RURAL|CAMIONETA")
        #setear_combo_extjs_real(driver,wait,"selmodelodevehiculo","SX6|DONG FENG|RURAL|CAMIONETA") #SX|MATSU|MOTO|MOTOCICLETA
        time.sleep(3)
        escribir_input_por_name(driver, wait, "txtweb_anos_de_fabricacion", "2025",False)

        time.sleep(1)
        escribir_input_por_name(driver, wait, "txtsuma_asegurada", 14990,False)
        time.sleep(1)
        # metodo uso de vehiculo
        # por defecto se pone solo
        particular = True
        valor_particular = "PARTICULAR" if particular else "COMERCIAL"
        escribir_y_enter_combo_por_name(driver,wait,"selusos_de_vehiculos",valor_particular,1)
        time.sleep(3)
        # metodo vehiculo a gas
        tiene_gas = False   # o False
        valor_combustible = "SI" if tiene_gas else "NO"
        escribir_y_enter_combo_por_name(driver,wait,"selcombustible_gas",valor_combustible,1)
        time.sleep(3)
        escribir_input_por_name(driver, wait, "txtnro_pasajeros", "5",False)
        time.sleep(1)
        # metodo continuidad de seguro
        seguro = False   # o False
        valor_seguro = "SI" if seguro else "NO"
        escribir_y_enter_combo_por_name(driver,wait,"selprocedenciaexterna",valor_seguro,1)
        time.sleep(3)
        # metodo requiere inspeccion fisica
        inspeccion = False   # o False
        valor_inspeccion = "SI" if inspeccion else "NO"
        escribir_y_enter_combo_por_name(driver,wait,"selrequiereinspeccion",valor_inspeccion,1)

        particular = True  # o False
        if particular:  # si es particular
            time.sleep(3)
            #Natural o Juridica    
            escribir_y_enter_combo_por_name(driver,wait,"seltipo_de_persona","NATURAL",2)
            time.sleep(3)
            escribir_y_enter_combo_por_name(driver,wait,"seltiempo_de_credito","12 MESES",2)
            time.sleep(3)
            escribir_input_por_name(driver, wait, "txtvendedor", "MIGUEL AQUINO",False)
            time.sleep(1)
            escribir_y_enter_combo_por_name(driver,wait,"sellocalización","LIMA",2)
        #---------- From---------------

        time.sleep(3)
        btn_cal = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Calcular Planes']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_cal)
        driver.execute_script("arguments[0].click();", btn_cal)
        print("🖱️ Clic en 'Calcular Planes'")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask-msg.x-mask-loading")))
        print("✅ Carga finalizada (mask desapareció)")

        fieldset_plan = wait.until(EC.presence_of_element_located((By.XPATH, "//fieldset[.//span[normalize-space()='Plan 1']]")))
        print("✅ Plan 1 localizado")

        wait.until(EC.visibility_of(fieldset_plan))
        print("✅ Plan 1 visible")

        boton_seleccionar = wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[normalize-space()='Seleccionar'] | .//a[normalize-space()='Seleccionar']")))
        driver.execute_script("arguments[0].click();", boton_seleccionar)
        print("✅ Clic en Seleccionar")

        descuento = False

        if descuento:
            print("Hay descuento")

        tab_fraccionamiento = wait.until(EC.element_to_be_clickable((By.XPATH,"//span[contains(@class,'x-tab-strip-text') and normalize-space()='Fraccionamiento']")))
        tab_fraccionamiento.click()
        print("✅ Clic en Fraccionamiento")

        #ingresar_fecha_extjs(driver,wait,name="fecinicertificado",fecha_ddmmyyyy="16/03/2026")

        #click_fuera(driver)

        escribir_y_enter_combo_por_name(driver, wait, "ideplanfinanciamiento", "PLAN 2020 CC PN 0% USD 12 CUOTAS",2)
        time.sleep(1)
        escribir_y_enter_combo_por_name(driver, wait, "idetipotarjeta", "Cuenta de Ahorros",2)

        #ingresar_fecha_extjs(driver,wait,name="fecprimvcto",fecha_ddmmyyyy="23/03/2026")

        click_fuera(driver)

        time.sleep(3)
        btn_generar = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Generar']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_generar)
        driver.execute_script("arguments[0].click();", btn_generar)
        print("🖱️ Clic en 'Generar'")

        time.sleep(5)

        # 1️⃣ Click en "Ingresar Cliente"
        btn_ing_cliente = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Ingresar Cliente']")))
        driver.execute_script("arguments[0].click();", btn_ing_cliente)
        print("🖱️ Clic en 'Ingresar Cliente'")

        time.sleep(5)

        wait.until(EC.presence_of_element_located((By.XPATH,"//li[contains(@class,'x-tab-strip-active')]//span[normalize-space()='Cliente']")))

        print("✅ Tab 'Cliente' activa")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR,"div.ext-el-mask, div.ext-el-mask-msg")))
        print("esperar que NO haya máscara ExtJS")

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"div.x-panel-body div.x-toolbar")))
        print("✅ Toolbar del grid cargado")

        MAX_INTENTOS = 5
        intentos = 0

        while intentos < MAX_INTENTOS:

            intentos += 1
            print(f"🔁 Intento {intentos} - Click en Agregar")
          
            wait.until(EC.invisibility_of_element_located((
                By.CSS_SELECTOR,
                "div.ext-el-mask, div.ext-el-mask-msg"
            )))
            print("✅ No hay máscara ExtJS")

            # 🔥 CLICK REAL EXTJS
            click_agregar_cliente_extjs(driver)
            print("🖱️ Click REAL en 'Agregar'")

            time.sleep(2)  # dar tiempo a que aparezca el modal

            titulo_modal = obtener_titulo_modal_extjs(driver, wait)

            if titulo_modal is None:
                print("✅ No apareció modal → continuar flujo")
                break

            if "Requisitos" in titulo_modal:
                print("⚠️ Modal de Requisitos → cerrando y reintentando")
                if cerrar_modal_extjs(driver, wait):
                    time.sleep(3)
                    continue
                else:
                    print("No se pudo cerrar el modal")
                    input("Esperar")

            print("ℹ️ Modal 'Nuevo Asegurado' → trabajar dentro del modal")
            break

        else:
            raise Exception("❌ Se alcanzó el máximo de intentos presionando Agregar")

        time.sleep(5)

        # 🔥 escribir dentro del modal Nuevo Asegurado
        escribir_input_en_modal(driver,wait,"numerodoc","72534406",True)

        time.sleep(0.5)

        # click buscar
        click_boton_buscar_en_modal_extjs(driver)

        click_boton_grabar_en_modal_extjs(driver)

        # # ⏳ esperar que el modal se cierre
        # esperar_cierre_modal_extjs(driver, wait)

        # # ⏳ esperar que no haya máscara
        # wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))
        # print("✅ Sin máscara")

        # # ⏳ esperar que termine el proceso ExtJS (SIN máscara)
        # wait.until(lambda d: d.execute_script("""
        #     var masks = document.querySelectorAll(
        #         '.x-mask, .x-mask-msg, .ext-el-mask, .ext-el-mask-msg'
        #     );

        #     for (var i = 0; i < masks.length; i++) {
        #         var style = window.getComputedStyle(masks[i]);
        #         if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
        #             return false; // todavía hay máscara activa
        #         }
        #     }
        #     return true; // ninguna máscara bloquea
        # """))
        # print("✅ ExtJS listo (sin máscara activa)")

        btn_gen_coti = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Generar Cotización']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_gen_coti)
        driver.execute_script("arguments[0].click();", btn_gen_coti)
        print("🖱️ Clic en 'Generar Cotización'")

        btn_si = wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Sí']")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_si)
        driver.execute_script("arguments[0].click();", btn_si)
        print("🖱️ Clic en 'Sí'")

        # ⏳ esperar máscara ExtJS
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))
        print("✅ Sin máscara")

        # 🖨️ Imprimir
        click_imprimir_extjs(driver,wait)
        print("🖨️ Click REAL en 'Imprimir'")

    except Exception as e:
        #print(f"⚠️ Conclusión: {e}")
        traceback.print_exc()
    finally:
        input("Esperar")
        driver.quit()

def click_imprimir_extjs(driver,wait):

    # 1️⃣ asegurarnos que no haya máscara
    wait.until(EC.invisibility_of_element_located((
        By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg"
    )))
    print("✅ Sin máscara ExtJS")

    driver.execute_script("""
        var btn = Ext.ComponentMgr.all.items.find(function(c){
            return c.text === 'Imprimir'
                && c.rendered
                && c.isVisible()
                && c.ownerCt
                && c.ownerCt.id === 'ext-comp-2663';
        });

        if (!btn) {
            throw "❌ Botón Imprimir correcto NO encontrado";
        }

        // Click REAL ExtJS
        btn.fireEvent('click', btn);
    """)

    print("🖱️ Click REAL en 'Imprimir'")

def esperar_cierre_modal_extjs(driver, wait, timeout=30):
    
    wait.until(lambda d: d.execute_script("""
        return Ext.WindowMgr.getActive() === null;
    """))

    print("✅ Modal ExtJS cerrado correctamente")

def click_boton_grabar_en_modal_extjs(driver):

    boton = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//div[contains(@class,'x-window')]//button[.//b[contains(text(),'Advertencia')]]"
        ))
    )

    boton.click()

    print("💾 Click en botón ejecutado correctamente")

def click_boton_buscar_en_modal_extjs(driver):

    driver.execute_script("""
        var win = Ext.WindowMgr.getActive();

        if (!win) {
            throw "❌ No hay modal ExtJS activo";
        }

        // buscar el botón tb-restore dentro del modal
        var btnDom = win.el.dom.querySelector("button.tb-restore");

        if (!btnDom) {
            throw "❌ Botón tb-restore NO encontrado en el modal";
        }

        // obtener el componente ExtJS desde el DOM
        var btnCmp = Ext.getCmp(btnDom.id);

        if (!btnCmp) {
            // fallback: click DOM real
            btnDom.click();
            return;
        }

        // click REAL ExtJS
        btnCmp.fireEvent('click', btnCmp);
    """)

    print("🖱️ Click REAL en botón Buscar (tb-restore)")

def escribir_input_en_modal(driver, wait, name, valor, presionar_enter):

    # 1️⃣ esperar modal visible
    modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x-window[style*='visibility: visible']")))

    # 2️⃣ buscar input DENTRO del modal
    input_el = modal.find_element(By.NAME, name)

    driver.execute_script("""
        arguments[0].scrollIntoView({block:'center'});
        arguments[0].focus();
        arguments[0].value = '';
    """, input_el)

    input_el.send_keys(valor)

    print(f"✍️ Input '{name}' escrito DENTRO del modal")

def click_agregar_cliente_extjs(driver):
    driver.execute_script("""
    var btn = null;

    Ext.ComponentMgr.all.each(function(c){
        if (
            c.text === 'Agregar' &&
            c.rendered === true &&
            c.el &&
            c.el.isVisible(true) &&
            c.ownerCt &&
            c.ownerCt.ownerCt &&
            c.ownerCt.ownerCt.title === 'Cliente'   // 🔥 FILTRO CLAVE
        ) {
            btn = c;
        }
    });

    if (!btn) {
        throw '❌ Botón Agregar del tab Cliente NO encontrado';
    }

    // 🧪 DEBUG VISUAL (para que veas que ES ESTE)
    btn.el.dom.style.outline = '4px solid red';
    btn.el.dom.scrollIntoView({block:'center'});

    // ✅ CLICK REAL EXTJS
    btn.handler.call(btn.scope || btn);
    """)

def obtener_titulo_modal_extjs(driver, wait, timeout=3):

    try:
        modal = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.x-window[style*='visibility: visible']")
            )
        )

        titulo = modal.find_element(
            By.CSS_SELECTOR, "span.x-window-header-text"
        ).text.strip()

        print(f"🪟 Modal detectado: '{titulo}'")
        return titulo

    except TimeoutException:
        print("ℹ️ No hay modal visible")
        return None

def cerrar_modal_extjs(driver, wait):

    try:
        # 1️⃣ esperar modal visible
        modal = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.x-window[style*='visibility: visible']")
            )
        )
        print("✅ Modal ExtJS visible")

        # 2️⃣ buscar la X de cerrar (ExtJS nativo)
        btn_close = modal.find_element(By.CSS_SELECTOR, "div.x-tool-close")

        time.sleep(5)

        # 3️⃣ click JS real
        driver.execute_script("""
            arguments[0].dispatchEvent(
                new MouseEvent('mousedown', {bubbles:true})
            );
            arguments[0].dispatchEvent(
                new MouseEvent('mouseup', {bubbles:true})
            );
            arguments[0].dispatchEvent(
                new MouseEvent('click', {bubbles:true})
            );
        """, btn_close)

        print("🖱️ Click en X de cierre (ExtJS)")

        # # 4️⃣ esperar que el modal desaparezca
        # wait.until(EC.staleness_of(modal))
        # print("✅ Modal cerrado correctamente")

        return True

    except TimeoutException:
        print("⚠️ No se detectó modal ExtJS")
        return False

def ingresar_fecha_extjs(driver, wait, name, fecha_ddmmyyyy):

    # 1️⃣ Esperar input por NAME (no por ID)
    input_fecha = wait.until(EC.element_to_be_clickable((By.NAME, name)))

    input_fecha.click()
    input_fecha.clear()
    input_fecha.send_keys(fecha_ddmmyyyy)

    # 2️⃣ BLUR real (ExtJS valida aquí)
    input_fecha.send_keys(Keys.TAB)

    # 3️⃣ Esperar que deje de ser inválido
    wait.until(lambda d: "x-form-invalid" not in input_fecha.get_attribute("class"))

    print(f"✅ Fecha ingresada correctamente: {fecha_ddmmyyyy}")

if __name__ == "__main__":
    main()