# -*- coding: utf-8 -*-
# -- Froms ---
#from xml.etree.ElementTree import C14NWriterTarget
from selenium.webdriver.common.action_chains import ActionChains
#from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# -- Imports --
import logging
import time

# --- Metodos Funcionan ---
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
    #logging.info("⌨️ Digitando texto")

    # 4. Esperar lista
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-combo-list')]")))

    # 5. RE-OBTENER input (ExtJS lo recrea)
    input_visible = contenedor.find_element(By.XPATH, ".//input[contains(@class,'x-form-field')]")

    # 6. Intento normal: ↓ + ENTER
    input_visible.send_keys(Keys.ARROW_DOWN)
    time.sleep(1)
    input_visible.send_keys(Keys.ENTER)
    #logging.info("↵ Enter enviado")

    # 7. Validar hidden (espera corta)
    try:
        wait.until(lambda d: hidden.get_attribute("value"))
        #logging.info(f"✅ Combo '{name_hidden}' confirmado con ENTER")
        return
    except:
        logging.info("❌ ENTER no confirmó, usando PLAN B (clic directo)")
        raise Exception("Problemas técnicos, comunícate con el área de sistemas")

    # 🧨 PLAN B — click directo en la opción
    opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto}']")))
    opcion.click()
    logging.info("🖱️ Clic directo en opción")

    # 8. Validar nuevamente
    wait.until(lambda d: hidden.get_attribute("value"))
    #logging.info(f"✅ Combo '{name_hidden}' confirmado por click")

def seleccionar_combo_por_flecha(driver, wait, name_hidden, texto_opcion):

    # 🔥 1. Esperar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # 🔥 2. Ubicar hidden (base correcta)
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # 🔥 3. Subir SOLO al contenedor correcto
    contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-element')]")

    # 🔥 4. Buscar flecha dentro del mismo bloque
    flecha = contenedor.find_element(By.XPATH, ".//img[contains(@class,'x-form-arrow-trigger')]")

    # 🔥 5. click REAL (no JS)
    ActionChains(driver).move_to_element(flecha).click().perform()
    #logging.info("🖱️ Clic en flecha del combo")

    # 🔥 6. Esperar lista visible real (CLAVE)
    # opcion = wait.until(EC.element_to_be_clickable((
    #     By.XPATH,
    #     f"//div[contains(@class,'x-combo-list') and not(contains(@style,'display: none'))]"
    #     f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto_opcion}']"
    # )))

    try:
        opcion = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            f"//div[contains(@class,'x-combo-list') and not(contains(@style,'display: none'))]"
            f"//div[contains(@class,'x-combo-list-item') and contains(normalize-space(),'{texto_opcion}')]"
        )))
    except TimeoutException as e:
        raise Exception(f"Plan '{texto_opcion}' no configurado en Rimac | Motivo : {e}")

    opcion.click()
    #logging.info("✅ Opción seleccionada")

    # 🔥 7. Esperar procesamiento
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    #valor_anterior = hidden.get_attribute("value")

    # 🔥 8. Validar que el hidden cambió
    wait.until(lambda d: hidden.get_attribute("value") != "")
    ##ait.until(lambda d: hidden.get_attribute("value") != valor_anterior)

    logging.info(f"🎯 Combo '{name_hidden}' confirmado")

def click_fuera(driver):

    driver.find_element(By.TAG_NAME, "body").click()
    logging.info(f"🖱️ Clic fuera")
    time.sleep(3)

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

    logging.info(f"⌨️ Digitando {valor} en → '{name}'")

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
    #logging.info("🖱️ Clic en combo")
    # 6️⃣ limpiar y escribir
    input_visible.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
    input_visible.send_keys(texto)
    #logging.info("⌨️ Digitando texto")
    # 7️⃣ esperar posibles cargas
    #wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    if veces == 1:
        
        # esperar_lista_extjs(wait)
        # logging.info("cargo la lista")
        # time.sleep(2)
        # input("Esperar")
        # input_visible.send_keys(Keys.ARROW_DOWN)
        # logging.info("⬇️ Flecha abajo (primera opción)")
        # time.sleep(2)
        # input_visible.send_keys(Keys.ENTER)
        # logging.info("↵ Enter enviado")
        # time.sleep(2)

        # 7️⃣ esperar posibles cargas
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))
        # 8️⃣ ENTER FUERTE
        input_visible.send_keys(Keys.ENTER)
        #logging.info("↵ Enter enviado")

    else:
        # 7️⃣ esperar posibles cargas
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))
        # 8️⃣ ENTER FUERTE
        input_visible.send_keys(Keys.ENTER)
        #logging.info("↵ Enter enviado")

    # 9️⃣ PEQUEÑA ESPERA lógica (NO sleep)
    wait.until(lambda d: True)

    # 🔁 10️⃣ FALLBACK: seleccionar desde la lista si no confirmó
    if not hidden.get_attribute("value"):
        logging.info("❌ Enter no confirmó, intentando selección directa")
        raise Exception("Problemas técnicos, comunícate con el área de sistemas")

    # 11️⃣ validación final
    if not hidden.get_attribute("value"):
        raise Exception(f"❌ Combo '{name_hidden}' no se confirmó")

    logging.info(f"✅ Combo '{name_hidden}' confirmado")

def ingresar_fecha_extjs(driver, wait, name, fecha_ddmmyyyy,texto):

    # 1️⃣ Esperar input por NAME (no por ID)
    input_fecha = wait.until(EC.element_to_be_clickable((By.NAME, name)))
    input_fecha.click()
    input_fecha.clear()
    input_fecha.send_keys(fecha_ddmmyyyy)

    # 2️⃣ BLUR real (ExtJS valida aquí)
    input_fecha.send_keys(Keys.TAB)

    # 3️⃣ Esperar que deje de ser inválido
    wait.until(lambda d: "x-form-invalid" not in input_fecha.get_attribute("class"))

    logging.info(f"✅ {texto} ingresada : {fecha_ddmmyyyy}")

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

    # 5️⃣ click EXACTO en la opción
    opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto_opcion}']")))
    opcion.click()
    logging.info(f"✅ Opción '{texto_opcion}' seleccionada")

    # 6️⃣ Validar ID numérico
    wait.until(lambda d: hidden.get_attribute("value").isdigit())

    logging.info(f"✅ Modelo seleccionado correctamente | ID={hidden.get_attribute('value')}")

def resolver_empresa(ctx):
    dispatch = {
        'dongfeng': 'Dongfeng',
        'pangu': 'Pangu'
    }

    org = (ctx.vehiculo.organizacion or "").lower()

    return next((v for k, v in dispatch.items() if k in org), 'Otro')

def limpiar(texto):
   return (texto or "").strip().upper()

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

    // ✅ click REAL EXTJS
    btn.handler.call(btn.scope || btn);
    """)

def obtener_titulo_modal_extjs(driver, wait, timeout=10):

    try:
        #modal = WebDriverWait(driver, timeout).until(
        modal = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.x-window[style*='visibility: visible']")
            )
        )

        titulo = modal.find_element(
            By.CSS_SELECTOR, "span.x-window-header-text"
        ).text.strip()

        logging.info(f"🪟 Modal detectado: '{titulo}'")
        return titulo

    except TimeoutException:
        logging.info("ℹ️ No hay modal visible")
        return None

def seleccionar_combo_extjs(wait, texto):

    opciones = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".x-combo-list-item")
        )
    )

    for opcion in opciones:
        if opcion.is_displayed() and opcion.text.strip().upper() == texto.strip().upper():
            opcion.click()
            logging.info(f"🖱️ Clic en '{texto}'")
            return

    raise Exception(f"No se encontró la opción '{texto}' en el combo")

def esperar_ventana_extjs(wait, titulo):

    xpath = f"""
    //div[contains(@class,'x-window') and not(contains(@style,'display: none'))]
        [.//span[contains(@class,'x-window-header-text')
        and normalize-space()='{titulo}']]
    """

    ventana = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))

    logging.info(f"✅ Ventana '{titulo}' encontrada")
    return ventana

def click_boton_ventana(driver, wait, titulo_ventana, texto_boton,ctx):

    ventana = esperar_ventana_extjs(wait, titulo_ventana)

    if ventana:

        boton1 = ventana.find_element(By.XPATH,f".//button[normalize-space()='{texto_boton}']")
        wait.until(lambda d: boton1.is_enabled())
        driver.execute_script("arguments[0].click();", boton1)
        logging.info(f"🖱️ Clic en '{texto_boton}'")
        time.sleep(10)
        #----------------------------------------------
        click_boton_grabar_en_modal_extjs(driver,wait)
        time.sleep(10)
        #----------------------------------------------

        # def responder_mensaje(driver, wait, nomboton):

        #     # Esperar el MessageBox visible
        #     ventana = wait.until(
        #         EC.visibility_of_element_located((
        #             By.XPATH,
        #             "//div[contains(@class,'x-window-dlg') and not(contains(@style,'display: none'))]"
        #         ))
        #     )

        #     # Obtener el texto del mensaje
        #     mensaje = ventana.find_element(By.CSS_SELECTOR,".ext-mb-text").text.strip()

        #     #Al parecer existen casos de homonimia con el nombre y los apellidos que ha ingresado. ?Desea visualizarlos?
        #     if mensaje != "La transacción fue procesada Satisfactoriamente.":
        #         raise Exception(mensaje)

        #     logging.info(f"⚠️ Mensaje : {mensaje}")

        #     # Buscar el botón dentro de ESA ventana
        #     btn = ventana.find_element(By.XPATH,f".//button[normalize-space()='{nomboton}']")

        #     # Esperar a que esté habilitado
        #     wait.until(lambda d: btn.is_enabled())

        #     # Scroll por si acaso
        #     driver.execute_script("arguments[0].scrollIntoView(true);", btn)

        #     # Intentar click normal
        #     try:
        #         btn.click()
        #     except:
        #         driver.execute_script("arguments[0].click();", btn)

        #     logging.info(f"🖱️ Clic en '{nomboton}")

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
                        
    else:
        raise Exception(f"No se encontró la ventana '{titulo_ventana}'")

def set_valor_campo_extjs(driver, wait, nombre_campo, valor):

    wait.until(
        EC.element_to_be_clickable((By.NAME, nombre_campo))
    )

    driver.execute_script("""
    var win = Ext.WindowMgr.getActive();

    if (!win)
        throw "No existe un modal activo";

    var campo = win.find("name", arguments[0])[0];

    if (!campo)
        throw "No se encontró el campo: " + arguments[0];

    campo.setValue(arguments[1]);
    campo.fireEvent('change', campo, arguments[1]);
    """, nombre_campo, valor)

    logging.info(f"✅ '{valor}' ingresado en el campo '{nombre_campo}'")

def abrir_combo_en_fieldset(driver, titulo_fieldset, hidden_name, indice=0):

    driver.execute_script("""
    var titulo = arguments[0];
    var hiddenName = arguments[1];
    var indice = arguments[2];

    var fs = null;

    document.querySelectorAll("fieldset.x-fieldset").forEach(function(f){

        var legend = f.querySelector(".x-fieldset-header-text");

        if(legend && legend.innerText.trim() === titulo){
            fs = f;
        }
    });

    if(!fs)
        throw "No existe el fieldset";

    var hidden = fs.querySelector("input[name='" + hiddenName + "']");

    if(!hidden)
        throw "No existe el campo";

    var triggers = hidden.parentElement.querySelectorAll(".x-form-trigger");

    if(triggers.length == 0)
        throw "No existen triggers para " + hiddenName;

    if(indice >= triggers.length)
        throw "Trigger inexistente";

    triggers[indice].click();

    """, titulo_fieldset, hidden_name, indice)

    logging.info(f"✅ Combo '{hidden_name}' abierto")

def aceptar_messagebox_extjs(driver, wait):

    # Esperar a que aparezca el MessageBox
    wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "div.x-window-dlg")
        )
    )

    # Obtener el texto
    mensaje = driver.find_element(
        By.CSS_SELECTOR,
        "div.x-window-dlg .ext-mb-text"
    ).text.strip()

    return mensaje

def responder_mensaje(driver, wait, nomboton):

    # Esperar el MessageBox visible
    ventana = wait.until(
        EC.visibility_of_element_located((
            By.XPATH,
            "//div[contains(@class,'x-window-dlg') and not(contains(@style,'display: none'))]"
        ))
    )

    # Obtener el texto del mensaje
    mensaje = ventana.find_element(By.CSS_SELECTOR,".ext-mb-text").text.strip()

    #Al parecer existen casos de homonimia con el nombre y los apellidos que ha ingresado. ?Desea visualizarlos?
    if mensaje != "La transacción fue procesada Satisfactoriamente.":
        raise Exception(mensaje)

    logging.info(f"⚠️ Mensaje : {mensaje}")

    # Buscar el botón dentro de ESA ventana
    btn = ventana.find_element(By.XPATH,f".//button[normalize-space()='{nomboton}']")

    # Esperar a que esté habilitado
    wait.until(lambda d: btn.is_enabled())

    # Scroll por si acaso
    driver.execute_script("arguments[0].scrollIntoView(true);", btn)

    # Intentar click normal
    try:
        btn.click()
    except:
        driver.execute_script("arguments[0].click();", btn)

    logging.info(f"🖱️ Clic en '{nomboton}")

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

    logging.info("🖱️ Clic en botón Buscar (tb-restore)")

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

    logging.info(f"✍️ '{valor}' ingresado en el input '{name}' dentro del modal")

def click_boton_grabar_en_modal_extjs(driver,wait):

    # Esperar a que ExtJS esté listo
    #WebDriverWait(driver, 15).until(
    wait.until(
        lambda d: d.execute_script("return typeof Ext !== 'undefined'")
    )

    driver.execute_script("""
    var win = Ext.WindowMgr.getActive();

    if (!win) {
        throw "❌ No hay modal activo";
    }

    var botones = win.el.dom.querySelectorAll("button.tb-save");

    var btnDom = null;

    botones.forEach(function(b) {
        if (b.offsetParent !== null) { // visible
            btnDom = b;
        }
    });

    if (!btnDom) {
        throw "❌ Botón tb-save visible no encontrado";
    }

    var btnCmp = Ext.getCmp(btnDom.id);

    if (btnCmp) {
        btnCmp.fireEvent('click', btnCmp);
    } else {
        btnDom.click();
    }
""")

    logging.info("🖱️ Clic en botón Grabar (tb-save)")

def click_tab_terceros_extjs(driver):

    driver.execute_script("""
    var tabs = document.querySelectorAll('span.x-tab-strip-text');

    var tab = null;

    tabs.forEach(function(el){
        if (el.innerText.trim() === 'Terceros') {
            tab = el;
        }
    });

    if (!tab) {
        throw '❌ Tab Terceros NO encontrado en DOM';
    }

    var li = tab.closest('li');

    if (!li) {
        throw '❌ No se pudo obtener el LI del tab';
    }

    // 🧪 DEBUG VISUAL
    li.style.outline = '4px solid red';
    li.scrollIntoView({block:'center'});

    // 🔥 click REAL (tipo usuario)
    var evtDown = new MouseEvent('mousedown', {bubbles: true});
    var evtUp = new MouseEvent('mouseup', {bubbles: true});
    var evtclick = new MouseEvent('click', {bubbles: true});

    li.dispatchEvent(evtDown);
    li.dispatchEvent(evtUp);
    li.dispatchEvent(evtclick);
    """)

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