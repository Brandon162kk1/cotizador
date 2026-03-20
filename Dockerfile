# Usar tu imagen base personalizada
FROM chromedriver:stable

WORKDIR /app

# Copiar requirements si aplica
#COPY requirements.txt /app/
COPY requirements.txt .

# Volver temporalmente a root para instalar dependencias
USER root
#RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY Codigo/ /app/Codigo

# Copiar supervisord.conf
COPY supervisord.conf /app/

# Crear carpetas necesarias
RUN mkdir -p /codigo_rimac_SAS \
    && chown -R user1:user1 /app /codigo_rimac_SAS

WORKDIR /app
USER user1

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# CMD para levantar supervisord
CMD ["supervisord", "-c", "/app/supervisord.conf"]