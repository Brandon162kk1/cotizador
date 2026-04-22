# -*- coding: utf-8 -*-
# -- Froms ---
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# -- Imports --
import logging
import time

# --- Metodos ---

def resolver_empresa(organizacion: str) -> str:
    dispatch = {
        'dongfeng': 'Dongfeng',
        'pangu': 'Pangu'
    }

    org = (organizacion or "").lower()

    return next((v for k, v in dispatch.items() if k in org), 'Otro')

def registrar_cliente_nuevo(driver,wait,ctx):
      
    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "x-window")))
    logging.info("Ventana visible")

    # iframes = driver.find_elements(By.TAG_NAME, "iframe")
    # logging.info(f"Cantidad iframes:  {len(iframes)}")

    input_doc = wait.until(EC.presence_of_element_located((By.NAME, "numerodoc")))
    logging.info("Input encontrado")

    try:

        driver.execute_script("""
        arguments[0].focus();

        // Simular ENTER real
        var event = new KeyboardEvent('keydown', {
            key: 'Enter',
            keyCode: 13,
            which: 13,
            bubbles: true
        });

        arguments[0].dispatchEvent(event);
        """, input_doc)
        logging.info("enter")
    except :
        driver.execute_script("""
        document.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Enter',
            keyCode: 13,
            which: 13,
            bubbles: true
        }));
        """)
        logging.info("enter2")

    time.sleep(5)

    input("Esperar")

    # 🔧 FUNCIONES BASE EXTJS

    def esperar_extjs_ready(driver, timeout=20):
        wait.until(
            lambda d: (
                len(d.find_elements(By.CLASS_NAME, "ext-el-mask")) == 0 and
                d.execute_script("return document.readyState") == "complete"
            )
        )

    def select_extjs_combo(driver, input_css, value):
        wait = WebDriverWait(driver, 10)

        # 1. ubicar input visible
        input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, input_css)))

        # 2. hacer scroll + click real
        driver.execute_script("arguments[0].scrollIntoView(true);", input_box)
        driver.execute_script("arguments[0].click();", input_box)

        # 🔥 3. usar JS para escribir (NO send_keys directo)
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
        """, input_box, value)

        # 4. esperar lista desplegable REAL
        option = wait.until(EC.visibility_of_element_located((
            By.XPATH, f"//div[contains(@class,'x-combo-list-item') and contains(., '{value}')]"
        )))

        # 5. click real
        driver.execute_script("arguments[0].click();", option)
            
    def force_input(driver, element, value):
        driver.execute_script("""
            arguments[0].focus();
            arguments[0].value = '';
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
        """, element, value)

    def set_extjs_textfield(driver, name, value):
        driver.execute_script("""
            var inputs = document.getElementsByName('nombre');

            for (var i = 0; i < inputs.length; i++) {
                var el = inputs[i];
    
                if (el.offsetParent !== null) {  // 🔥 visible
                    el.focus();
                    el.value = arguments[0];

                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('blur', { bubbles: true }));
        
                    break;
                }
            }
            """, "JUAN PEREZ")

    def set_extjs_date(driver, name, value):
        driver.execute_script("""
        var input = document.querySelector("input[name='" + arguments[0] + "']");
        if (input) {
            input.removeAttribute('readonly');
            input.value = arguments[1];

            // eventos que ExtJS sí escucha
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new Event('blur', { bubbles: true }));
        } else {
            console.log("No se encontró el campo fecha");
        }
        """, name, value)

    def set_extjs_value(driver, query, value):
        driver.execute_script(f"""
            var field = Ext.ComponentQuery.query('{query}')[0];
            if (field) {{
                field.setValue('{value}');
                field.fireEvent('change', field, '{value}');
            }}
        """)

    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "x-window")))

    logging.info("-------------------------------------------------------")
    logging.info("✅ Se esperó todos los labels que vamos a ingresar data")

    # 1. Esperar que ExtJS esté listo
    esperar_extjs_ready(driver)

    # 2. Setear NOMBRE usando ExtJS
    driver.execute_script("""
    var field = Ext.ComponentQuery.query('textfield[name=nombre]')[0];
    if (field) {
        field.setValue('JUAN PEREZ');
        field.fireEvent('change', field, 'JUAN PEREZ');
    }
    """)
    logging.info("✅ Nombre seteado con ExtJS")

    # 3. Esperar otra vez (ExtJS suele procesar internamente)
    esperar_extjs_ready(driver)

    # 4. Setear FECHA
    driver.execute_script("""
    var field = Ext.ComponentQuery.query('datefield[name=fecnacimiento]')[0];
    if (field) {
        field.setValue('01/01/1990');
        field.fireEvent('select', field, field.getValue());
        field.fireEvent('change', field, field.getValue());
    }
    """)
    logging.info("✅ Fecha seteada con ExtJS")

    # 5. Esperar nuevamente
    esperar_extjs_ready(driver)

    input("Esperar")

    time.sleep(3)
    # 🧾 APELLIDOS (estos sí funcionan normal)
    try:
        ape_paterno = wait.until(EC.presence_of_element_located((By.NAME, "apepaterno")))
        ape_paterno.clear()
        ape_paterno.send_keys(ctx.cliente.apellido_paterno)

        ape_materno = wait.until(EC.presence_of_element_located((By.NAME, "apematerno")))
        ape_materno.clear()
        ape_materno.send_keys(ctx.cliente.apellido_materno)

        logging.info("✅ Apellidos ingresados")
    except Exception as e:
        logging.error(f"❌ Error apellidos: {e}")

    time.sleep(3)
    # 🚻 SEXO
    try:
        if ctx.cliente.sexo.upper() == "M":
            genero = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='idpgenero' and @value='M']")))
        else:
            genero = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='idpgenero' and @value='F']")))

        genero.click()
        logging.info(f"✅ Sexo: {ctx.cliente.sexo.upper()}")
    except Exception as e:
        logging.error(f"❌ Error sexo: {e}")

    time.sleep(3)
    # 📅 FECHA
    try:
        set_extjs_date(driver, "fecnacimiento", ctx.cliente.fecha_nac)
        logging.info(f"✅ Fecha: {ctx.cliente.fecha_nac}")
    except Exception as e:
        logging.error(f"❌ Error fecha: {e}")

    time.sleep(3)
    # 🏙️ DISTRITO
    try:
        select_extjs_combo(
            driver,
            "input[name='idedistrito'] + input",
            "LA MOLINA"
        )
        logging.info("✅ Distrito seleccionado")
    except Exception as e:
        logging.error(f"❌ Error distrito: {e}")

    time.sleep(3)
    # 🛣️ TIPO VIA
    try:
        select_extjs_combo(
            driver,
            "input[name='idptipovia'] + input",
            "AV"
        )
        logging.info("✅ Tipo vía seleccionado")
    except Exception as e:
        logging.error(f"❌ Error tipo vía: {e}")

    time.sleep(3)
    # 🏠 NOMBRE VIA
    try:
        nom_via = wait.until(EC.presence_of_element_located((By.NAME, "nomvia")))
        driver.execute_script("arguments[0].scrollIntoView(true);", nom_via)
        driver.execute_script("arguments[0].click();", nom_via)

        force_input(driver, nom_via, "AREQUIPA")
        logging.info("✅ Nombre vía")
    except Exception as e:
        logging.error(f"❌ Error nombre vía: {e}")

    time.sleep(3)
    # 🔢 NUMERO
    try:
        num_via = wait.until(EC.presence_of_element_located((By.NAME, "numcasa")))
        num_via.clear()
        num_via.send_keys("123")
        logging.info("✅ Número vía")
    except Exception as e:
        logging.error(f"❌ Error número vía: {e}")

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
    logging.info("⌨️ Digitando texto")

    # 4. Esperar lista
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-combo-list')]")))

    # 5. RE-OBTENER input (ExtJS lo recrea)
    input_visible = contenedor.find_element(By.XPATH, ".//input[contains(@class,'x-form-field')]")

    # 6. Intento normal: ↓ + ENTER
    input_visible.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.2)
    input_visible.send_keys(Keys.ENTER)
    logging.info("↵ Enter enviado")

    # 7. Validar hidden (espera corta)
    try:
        wait.until(lambda d: hidden.get_attribute("value"))
        logging.info(f"✅ Combo '{name_hidden}' confirmado con ENTER")
        return
    except:
        logging.info("⚠️ ENTER no confirmó, usando PLAN B (click directo)")

    # 🧨 PLAN B — click directo en la opción
    opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto}']")))
    opcion.click()
    logging.info("🖱️ Click directo en opción")

    # 8. Validar nuevamente
    wait.until(lambda d: hidden.get_attribute("value"))
    logging.info(f"✅ Combo '{name_hidden}' confirmado por click")

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

    // 🔥 CLICK REAL (tipo usuario)
    var evtDown = new MouseEvent('mousedown', {bubbles: true});
    var evtUp = new MouseEvent('mouseup', {bubbles: true});
    var evtClick = new MouseEvent('click', {bubbles: true});

    li.dispatchEvent(evtDown);
    li.dispatchEvent(evtUp);
    li.dispatchEvent(evtClick);
    """)       

def seleccionar_combo_por_flecha(driver, wait, name_hidden, texto_opcion):

    # # asegurar que no haya máscara
    # wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # # 1. hidden por NAME
    # hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # # 2. contenedor SOLO de ese combo
    # contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-field-wrap')]")

    # # 3. flechita (img)
    # flecha = contenedor.find_element(By.XPATH, ".//img[contains(@class,'x-form-arrow-trigger')]")

    # # 4. click fuerte en la flecha
    # driver.execute_script("arguments[0].scrollIntoView({block:'center'});", flecha)
    # driver.execute_script("arguments[0].click();", flecha)
    # logging.info("🖱️ Click en flecha del combo")

    # # 5. esperar que aparezca la lista y seleccionar la opción
    # #opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto_opcion}']")))

    # opcion = wait.until(EC.element_to_be_clickable((
    #     By.XPATH,
    #     f"//div[contains(@class,'x-combo-list') and not(contains(@style,'display: none')) and not(contains(@style,'visibility: hidden'))]"
    #     f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto_opcion}']"
    # )))

    # opcion.click()
    # logging.info("✅ Opción seleccionada")

    # # 6. esperar que ExtJS procese
    # wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # # 7. validar que el hidden cambió
    # if not hidden.get_attribute("value"):
    #     raise Exception(f"❌ El combo '{name_hidden}' no se confirmó")

    # logging.info(f"🎯 Combo '{name_hidden}' confirmado")

    #---------------------------------------------------------
    from selenium.webdriver.common.action_chains import ActionChains
    # 🔥 1. Esperar que no haya máscara
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # 🔥 2. Ubicar hidden (base correcta)
    hidden = wait.until(EC.presence_of_element_located((By.NAME, name_hidden)))

    # 🔥 3. Subir SOLO al contenedor correcto
    contenedor = hidden.find_element(By.XPATH, "./ancestor::div[contains(@class,'x-form-element')]")

    # 🔥 4. Buscar flecha dentro del mismo bloque
    flecha = contenedor.find_element(By.XPATH, ".//img[contains(@class,'x-form-arrow-trigger')]")

    # 🔥 5. Click REAL (no JS)
    ActionChains(driver).move_to_element(flecha).click().perform()
    logging.info("🖱️ Click en flecha del combo")

    # 🔥 6. Esperar lista visible real (CLAVE)
    opcion = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        f"//div[contains(@class,'x-combo-list') and not(contains(@style,'display: none'))]"
        f"//div[contains(@class,'x-combo-list-item') and normalize-space()='{texto_opcion}']"
    )))

    opcion.click()
    logging.info("✅ Opción seleccionada")

    # 🔥 7. Esperar procesamiento
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

    # 🔥 8. Validar que el hidden cambió
    wait.until(lambda d: hidden.get_attribute("value") != "")

    logging.info(f"🎯 Combo '{name_hidden}' confirmado")

def click_fuera(driver):

    driver.find_element(By.TAG_NAME, "body").click()
    logging.info("🖱️ Click fuera (blur)2")
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

    logging.info(f"⌨️ '{name}' ← {valor}")

def esperar_lista_extjs(wait):
    # esperar layer visible
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x-layer.x-combo-list")))
    logging.info("Espero1")

    # esperar inner
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.x-combo-list-inner")))
    logging.info("Espero2")

    # esperar al menos un item
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.x-combo-list-item")))
    logging.info("Espero3")

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

    logging.info(f"✅ Modelo seleccionado correctamente | ID={hidden.get_attribute('value')}")

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

    logging.info(f"✅ Combo ExtJS '{name_hidden}' seteado REALMENTE")

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
    logging.info("🖱️ Clic en combo")

    # 6️⃣ limpiar y escribir
    input_visible.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
    input_visible.send_keys(texto)
    logging.info("⌨️ Digitando texto")

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
        logging.info("↵ Enter enviado")

    else:

        # 7️⃣ esperar posibles cargas
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ext-el-mask")))

        # 8️⃣ ENTER FUERTE
        input_visible.send_keys(Keys.ENTER)
        logging.info("↵ Enter enviado")

    # 9️⃣ PEQUEÑA ESPERA lógica (NO sleep)
    wait.until(lambda d: True)

    # 🔁 10️⃣ FALLBACK: seleccionar desde la lista si no confirmó
    if not hidden.get_attribute("value"):
        logging.info("⚠️ Enter no confirmó, intentando selección directa")

        opcion = wait.until(EC.element_to_be_clickable((By.XPATH,f"//div[contains(@class,'x-combo-list-item') and contains(normalize-space(), '{texto.split('|')[0]}')]")))
        opcion.click()
        logging.info("🖱️ Click directo en opción")

    # 11️⃣ validación final
    if not hidden.get_attribute("value"):
        raise Exception(f"❌ Combo '{name_hidden}' no se confirmó")

    logging.info(f"✅ Combo '{name_hidden}' confirmado")

def click_boton_extjs(driver, wait, texto_boton, timeout=30):

    # 1️⃣ esperar que desaparezca máscara
    wait.until(EC.invisibility_of_element_located((
        By.CSS_SELECTOR, "div.ext-el-mask, div.ext-el-mask-msg"
    )))
    logging.info("✅ Sin máscara ExtJS")

    # 2️⃣ esperar que Ext esté completamente listo 🔥
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("""
            return (
                typeof window.Ext !== 'undefined' &&
                Ext.ComponentQuery &&
                Ext.ComponentQuery.query &&
                Ext.ComponentMgr &&
                Ext.ComponentMgr.all &&
                Ext.ComponentMgr.all.items.length > 0
            );
        """)
    )
    logging.info("✅ ExtJS completamente cargado")

    # 3️⃣ esperar botón visible REAL
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script(f"""
            try {{
                var botones = Ext.ComponentQuery.query('button') || [];
                return botones.some(b =>
                    (b.text || '').trim() === '{texto_boton}' &&
                    b.rendered &&
                    b.isVisible()
                );
            }} catch(e) {{
                return false;
            }}
        """)
    )
    logging.info(f"✅ Botón '{texto_boton}' disponible")

    # 4️⃣ click real
    driver.execute_script(f"""
        var botones = Ext.ComponentQuery.query('button') || [];

        var btn = botones.find(b =>
            (b.text || '').trim() === '{texto_boton}' &&
            b.rendered &&
            b.isVisible()
        );

        if (!btn) {{
            throw "❌ Botón {texto_boton} NO encontrado";
        }}

        btn.fireEvent('click', btn);
    """)

    logging.info(f"🖱️ Click REAL en '{texto_boton}'")

def esperar_cierre_modal_extjs(driver, wait, timeout=30):
    
    wait.until(lambda d: d.execute_script("""
        return Ext.WindowMgr.getActive() === null;
    """))

    logging.info("✅ Modal ExtJS cerrado correctamente")

def click_boton_grabar_en_modal_extjs(driver):

    # Esperar a que ExtJS esté listo
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return typeof Ext !== 'undefined'")
    )

    # driver.execute_script("""
    #     var win = Ext.WindowMgr.getActive();

    #     if (!win) {
    #         throw "❌ No hay modal activo";
    #     }

    #     // ✅ BOTÓN CORRECTO
    #     var btnDom = win.el.dom.querySelector("button.tb-save");

    #     if (!btnDom) {
    #         throw "❌ Botón tb-save (Grabar) no encontrado";
    #     }

    #     var btnCmp = Ext.getCmp(btnDom.id);

    #     if (btnCmp) {
    #         btnCmp.fireEvent('click', btnCmp);
    #     } else {
    #         btnDom.click();
    #     }
    # """)

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

    logging.info(f"✍️ Input '{name}' escrito DENTRO del modal")

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

def obtener_titulo_modal_extjs(driver, wait, timeout=10):

    try:
        modal = WebDriverWait(driver, timeout).until(
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

def cerrar_modal_extjs(driver, wait):

    try:
        # 1️⃣ esperar modal visible
        modal = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.x-window[style*='visibility: visible']")
            )
        )
        logging.info("✅ Modal ExtJS visible")

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

        logging.info("🖱️ Click en X de cierre (ExtJS)")

        # # 4️⃣ esperar que el modal desaparezca
        # wait.until(EC.staleness_of(modal))
        # logging.info("✅ Modal cerrado correctamente")

        return True

    except TimeoutException:
        logging.info("⚠️ No se detectó modal ExtJS")
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

    logging.info(f"✅ Fecha ingresada correctamente: {fecha_ddmmyyyy}")

def limpiar(texto):
   return (texto or "").strip().upper()
#-------------------------------------------