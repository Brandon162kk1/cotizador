# Imagen base con Chrome y noVNC
FROM chromedriver:stable

# Crear carpetas necesarias
RUN mkdir -p /app/Downloads

#WORKDIR /app

# Copiar requirements si aplica
#COPY requirements.txt /app/
#COPY requirements.txt .
COPY requirements.txt /app/

# Volver temporalmente a root para instalar dependencias
#USER root
RUN pip install --no-cache-dir -r /app/requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY Codigo/ /app/Codigo

# Copiar supervisord.conf
COPY supervisord.conf /app/

# Workdir
WORKDIR /app

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# CMD para levantar supervisord
CMD ["supervisord", "-c", "/app/supervisord.conf"]