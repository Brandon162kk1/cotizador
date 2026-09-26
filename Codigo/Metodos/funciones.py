# -*- coding: utf-8 -*-
# -- Froms ---
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# -- Imports --
import logging
import time

# -- Este name tiene que se tal cual el nombre de las opciones del combo, sino no funciona
def _seleccionar_item_combo(driver, contenedor, texto):
    """
    Intenta hacer clic directo en el primer item del dropdown de ExtJS que coincida con el texto.
    Retorna True si encontró y clickeó un item, False si no había items visibles.
    """
    XPATHS_ITEM = [
        # Item exacto o parcial en x-combo-list-item
        f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto}']",
        f"//div[contains(@class,'x-combo-list-item') and contains(normalize-space(),'{texto}')]",
        # Primer item disponible (fallback)
        "//div[contains(@class,'x-combo-list-item')]",
    ]
    for xpath in XPATHS_ITEM:
        try:
            items = driver.find_elements(By.XPATH, xpath)
            for item in items:
                if item.is_displayed():
                    driver.execute_script("arguments[0].click();", item)
                    return True
        except Exception:
            continue
    return False


def interactuar_combo_por_name(driver, wait, name_hidden, texto, max_intentos=3):
    """
    Interactúa con un combo ExtJS buscando por el atributo 'name' del hidden input.
    Estrategia de selección por niveles:
      1. Clic directo en el item del dropdown (más confiable en ExtJS).
      2. ENTER sobre el input como fallback.
      3. Reintento completo del flujo desde cero (hasta max_intentos).
    """
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    for intento in range(1, max_intentos + 1):
        try:
            # Re-obtener referencias en cada intento (ExtJS puede recrear el DOM)
            hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))
            contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-field-wrap')]")
            input_visible = contenedor.find_element(By.XPATH, ".//input[contains(@class,'x-form-field')]")

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_visible)
            input_visible.click()
            time.sleep(0.3)
            input_visible.send_keys(Keys.CONTROL, "a")
            input_visible.send_keys(Keys.BACKSPACE)
            input_visible.send_keys(texto)
            logging.info(f"⌨️ Digitando {texto!r} en → '{name_hidden}' (intento {intento}/{max_intentos})")

            # Esperar que aparezca la lista desplegable con items
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-combo-list-item')]")))
            time.sleep(0.5)

            # ── Nivel 1: clic directo en el item del dropdown ──────────────────
            if _seleccionar_item_combo(driver, contenedor, texto):
                logging.info(f"🖱️ Item clickeado directamente en dropdown de '{name_hidden}'")
            else:
                # ── Nivel 2: ENTER sobre el input como fallback ────────────────
                logging.warning(f"⚠️ No se encontró item clickeable, usando ENTER en '{name_hidden}'")
                input_visible = contenedor.find_element(By.XPATH, ".//input[contains(@class,'x-form-field')]")
                time.sleep(0.5)
                input_visible.send_keys(Keys.ENTER)

            # Verificar que el hidden quedó con valor
            try:
                wait.until(lambda d: hidden.get_attribute("value"))
                logging.info(
                    f"✅ Combo '{name_hidden}' confirmado. Valor: {hidden.get_attribute('value')}"
                )
                return
            except TimeoutException:
                logging.warning(
                    f"⚠️ Intento {intento}/{max_intentos} — hidden '{name_hidden}' sigue vacío tras selección."
                )
                if intento == max_intentos:
                    logging.error(f"❌ No se pudo confirmar el combo '{name_hidden}' tras {max_intentos} intentos.")
                    raise Exception("Problemas técnicos, comunícate con el área de sistemas")
                # Cerrar dropdown si quedó abierto antes del siguiente intento
                try:
                    input_visible.send_keys(Keys.ESCAPE)
                except Exception:
                    pass
                time.sleep(1)

        except TimeoutException as e:
            logging.warning(f"⚠️ Timeout en intento {intento}/{max_intentos} del combo '{name_hidden}': {e}")
            if intento == max_intentos:
                raise Exception("Problemas técnicos, comunícate con el área de sistemas")
            time.sleep(1)

def seleccionar_combo_por_flecha(driver, wait, name_hidden, texto_opcion):

    # Esperar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # Ubicar hidden (base correcta)
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # Subir SOLO al contenedor correcto
    contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-element')]")

    # Buscar flecha dentro del mismo bloque
    flecha = contenedor.find_element(By.XPATH, ".//img[contains(@class,'x-form-arrow-trigger')]")

    # Click REAL (no JS)
    ActionChains(driver).move_to_element(flecha).click().perform()

    try:
        opcion = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            f"//div[contains(@class,'x-combo-list') and not(contains(@style,'display: none'))]"
            f"//div[contains(@class,'x-combo-list-item') and contains(normalize-space(),'{texto_opcion}')]"
        )))
    except TimeoutException as e:
        logging.exception(e)
        raise Exception(f"Plan '{texto_opcion}' no configurado en Rimac")

    try:
        opcion.click()
        logging.info("✅ Opción seleccionada")
    except:
        raise Exception(f"No se pudo seleccionar la opción '{texto_opcion}'")

    # Esperar procesamiento
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    #valor_anterior = hidden.get_attribute("value")

    # Validar que el hidden cambió
    wait.until(lambda d: hidden.get_attribute("value") != "")
    ##ait.until(lambda d: hidden.get_attribute("value") != valor_anterior)

    logging.info(f"✅ Combo '{name_hidden}' confirmado")

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

    # Esperar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))

    # Localizar hidden por NAME
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # Subir solo al contenedor de ese combo
    contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-field-wrap')]")

    # Input visible SOLO de ese combo
    input_visible = contenedor.find_element(By.XPATH, ".//input[@type='text' and contains(@class,'x-form-field')]")

    # 5️⃣ focus + click fuerte
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_visible)
    driver.execute_script("arguments[0].focus();", input_visible)
    driver.execute_script("arguments[0].click();", input_visible)

    input_visible.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
    input_visible.send_keys(texto)

    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # logging.info(f"🔎 Antes de ENTER - visible='{input_visible.get_attribute('value')}' "f"hidden='{hidden.get_attribute('value')}'")

    input_visible.send_keys(Keys.ENTER)

    # logging.info(f"🔎 Inmediatamente después - visible='{input_visible.get_attribute('value')}' "f"hidden='{hidden.get_attribute('value')}'")

    # Esperar REALMENTE que ExtJS actualice el hidden
    try:
        #wait.until(lambda d: hidden.get_attribute("value") not in (None, ""))
        wait.until(lambda d: hidden.get_attribute("value"))
        logging.info(f"✅ Combo '{name_hidden}' confirmado con ENTER. "f"Valor: {hidden.get_attribute('value')}")
        return

    except TimeoutException:

        logging.error(f"❌ ENTER no confirmó el combo '{name_hidden}'. "f"Valor hidden: '{hidden.get_attribute('value')}'")
        raise Exception("Problemas técnicos, comunícate con el área de sistemas")

def ingresar_fecha_extjs(wait, name, fecha_ddmmyyyy,texto):

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

def seleccionar_modelo_extjs(wait,texto_busqueda,texto_opcion,name_hidden="selmodelodevehiculo"):

    # Esperar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg")))

    # Hidden REAL
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # Input visible CORRECTO (anclado al hidden)
    input_visible = hidden.find_element(By.XPATH,"./ancestor::div[contains(@class,'x-form-field-wrap')]//input[@type='text']")
    input_visible.click()
    input_visible.clear()
    input_visible.send_keys(texto_busqueda)
    # 4Esperar lista
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-combo-list-inner')]")))

    # Clic en la opción
    try:
        opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto_opcion}']")))
        opcion.click()
        logging.info(f"✅ Opción '{texto_opcion}' seleccionada")
    except Exception as e:
        raise Exception(f"Vehículo '{texto_opcion}' no registrado en Rímac")

    # Validar ID numérico
    wait.until(lambda d: hidden.get_attribute("value").isdigit())

    logging.info(f"✅ Modelo seleccionado correctamente | ID={hidden.get_attribute('value')}")

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

def obtener_titulo_modal_extjs(wait):

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
        
        #Clic en si para mas adelante

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

# -- Revisar estos metodos mas adelante --

# set_valor_campo_extjs(driver, wait, "nomcompleto", ctx.cliente.rz_social)
# time.sleep(1)
# set_valor_campo_extjs(driver, wait, "nomcompletocomercial", ctx.cliente.rz_social)
# time.sleep(1)
# driver.execute_script("""
# var win = Ext.WindowMgr.getActive();

# var campo = win.find("name", "fecfundacion")[0];

# campo.setValue(arguments[0]);
# campo.fireEvent('change', campo, arguments[0]);
# """, ctx.cliente.fecha_nac)
# logging.info(f"✅ Fecha Fundación = '{ctx.cliente.fecha_nac}'")
# time.sleep(1)

def seleccionar_ciiu(driver, wait, codigoActv):

    hidden = wait.until(EC.presence_of_element_located((By.NAME, "dscacteconomica")))
    logging.info(" Perfecto 1")

    contenedor = hidden.find_element(By.XPATH,"./ancestor::div[contains(@class,'x-form-field-wrap')]")
    logging.info(" Perfecto 2")

    lupa = contenedor.find_element(By.CSS_SELECTOR,"img.x-form-search-trigger")
    logging.info(" Perfecto 3")

    ActionChains(driver).move_to_element(lupa).click().perform()
    logging.info(" Perfecto 4")

    wait.until(EC.visibility_of_element_located((By.XPATH,"//span[contains(.,'Buscar CIIU')]")))
    logging.info(" Perfecto 5")

    codigo = wait.until(EC.element_to_be_clickable((By.NAME, "codigociiu")))
    logging.info(" Perfecto 6")
    codigo.clear()
    logging.info(" Perfecto 7")
    codigo.send_keys(codigoActv)
    logging.info(" Perfecto 8")

    click_boton_buscar_en_modal_extjs(driver)
    logging.info(" Perfecto 9")

    # Mas robusto
    # fila = wait.until(
    #     EC.element_to_be_clickable((
    #         By.XPATH,
    #         f"//div[contains(@class,'x-grid3-body')]"
    #         f"//tr[.//div[normalize-space()='{codigoActv}']]"
    #     ))
    # )

    fila = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            f"//div[contains(@class,'x-grid3-body')]"
            f"//tr[td[4]//div[normalize-space()='{codigoActv}']]"
        ))
    )

    logging.info(" Perfecto 10")
    try:
        fila.click()
        logging.info(" Perfecto 11")
    except:
        ActionChains(driver).double_click(fila).perform()
        logging.info(" Perfecto 12")
                    
    def click_boton_seleccionar_en_modal_extjs(wait,driver):

        wait.until(
            lambda d: d.execute_script("return typeof Ext!='undefined'")
        )

        driver.execute_script("""
        var win = Ext.WindowMgr.getActive();

        if(!win)
            throw "No hay modal";

        var botones = win.el.dom.querySelectorAll("button.tb-view");

        for(var i=0;i<botones.length;i++){

            if(botones[i].offsetParent!==null){
                botones[i].click();
                return;
            }
        }

        throw "No se encontró el botón Seleccionar";
        """)

    click_boton_seleccionar_en_modal_extjs(wait,driver)
    logging.info(" Perfecto 13")

#seleccionar_ciiu(driver, wait, "5610")
# escribir_combo_extjs(wait,"dscacteconomica","Actividades de restaurantes y de servicio móvil de comidas")
time.sleep(1)