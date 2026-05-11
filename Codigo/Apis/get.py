# -*- coding: utf-8 -*-
import os
import requests
import logging
import time

url_api_cod_cot = os.getenv("url_api_cod_cot")
API_KEY = os.getenv("API_KEY_RIMAC")

headers = {
    "x-api-key": f"{API_KEY}"
}

def codigo_compania():

    while True:
        resp = requests.get(f"{url_api_cod_cot}",headers=headers)

        if resp.status_code == 200:
            codigo = resp.json()["codigo"]
            logging.info(f"Código recibido: {codigo}")
            break

        time.sleep(2)

    return codigo