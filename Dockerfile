# Imagen base con Chrome y noVNC
FROM chromedriver:stable

# Crear carpetas necesarias
RUN mkdir -p /app/Downloads

# Copiar requirements.txt
COPY requirements.txt /app/

# Instalar dependencias Python
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar código del proyecto
COPY Codigo/ /app/Codigo

# Copiar supervisord.conf
COPY supervisord.conf /app/

# Workdir
WORKDIR /app

# CMD para levantar supervisord
CMD ["supervisord", "-c", "/app/supervisord.conf"]