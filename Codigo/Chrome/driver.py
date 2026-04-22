from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from Tiempo.fechas_horas import get_timestamp

import logging
import os

def tomar_capturar(driver, ruta, prefijo):
    nombre = f"{prefijo}_{get_timestamp()}.png"
    ruta_completa = os.path.join(ruta, nombre)
    driver.save_screenshot(ruta_completa)

def abrirDriver(ruta):
    
    #-----Configuración de Chrome para Selenium -----
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--headless=new")        
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--no-sandbox')    
    chrome_options.add_argument('--disable-popup-blocking') 
    chrome_options.add_argument("--window-size=1920,1080")  
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    
    # Importante para imprimir sin Dialogo
    chrome_options.add_argument("--kiosk-printing")

    # Configuracion de descargas y preferencias
    prefs = {
        "download.default_directory": ruta,
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
        logging.info("🟡 Iniciando ChromeDriver")
        
        # Detectar si estamos en Windows o Linux para el Service
        if os.name == 'nt':
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            logging.info("🪟 Detectado Windows, usando ChromeDriverManager")
        else:
            # Ruta típica en el contenedor Docker
            ruta_chromedriver = "/usr/local/bin/chromedriver"
            if os.path.exists(ruta_chromedriver):
                service = Service(ruta_chromedriver)
                logging.info(f"🐧 Detectado Linux, usando path: {ruta_chromedriver}")
            else:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                logging.info("🐧 Detectado Linux, pero no se encontró chromedriver en /usr/local/bin, usando ChromeDriverManager")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("🟢 ChromeDriver iniciado correctamente")

    except Exception as e:
        logging.info(f"❌ Error al iniciar ChromeDriver: {e}")
        raise

    # Espera hasta que cargue el driver
    wait = WebDriverWait(driver, 60)
    return driver, wait    