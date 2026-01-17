# Usamos una imagen ligera de Python 3.9
FROM python:3.9-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos las dependencias directamente
# - fastapi y uvicorn: Para el servidor web
# - pyjwt y cryptography: Para validar tokens RSA-256
# - requests: Para descargar la clave pública de Go
RUN pip install --no-cache-dir fastapi uvicorn pyjwt requests cryptography

# Copiamos todo el código fuente al contenedor
COPY . .

# Informamos a Docker que este contenedor escucha en el puerto 3000
EXPOSE 3000

# Comando de arranque:
# --host 0.0.0.0 es vital para que Docker escuche peticiones desde fuera
# --port 3000 define el puerto interno
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]