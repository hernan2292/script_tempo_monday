#!/bin/bash
DEST_FOLDER="/home/devops/script_tempo_monday"
# Descargar la carpeta de Google Drive

sudo mkdir -p $DEST_FOLDER

sudo git clone https://github.com/hernan2292/script_tempo_monday.git /home/devops

# Actualizar el sistema
yum update --skip-broken

# Instalar software necesario para Docker
yum install -y yum-utils device-mapper-persistent-data lvm2

# Agregar el repositorio para instalar Docker
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Instalar Docker
yum install docker-ce docker-ce-cli containerd.io

# Iniciar Docker y habilitar el inicio automático del servicio
sudo systemctl start docker
sudo systemctl enable docker

# Descargar la última versión de la imagen para Python
sudo docker pull python:latest

# Crea o inicia el contenedor Docker y monta la carpeta necesaria
CONTAINER_NAME="script_tempo_container"

echo "Creando y ejecutando el contenedor..."
sudo docker run -itd --name script_tempo_container -v /home/devops/script_tempo_monday:/usr/src/script python:latest

docker run -v $DEST_FOLDER:/usr/src/script python:latest
sudo docker run -itd --name $CONTAINER_NAME python:latest

# Ejecuta los comandos dentro del contenedor
sudo docker exec -it $CONTAINER_NAME bash -c "apt-get update && apt-get install python3-pip -y"
sudo docker exec -it $CONTAINER_NAME bash -c "cd /usr/src/script && pip install -r requirements.txt && python script_tempo_monday.py"

# sudo docker exec -it script_tempo_container bash -c "cd /usr/src/script && python script_tempo_monday.py"

(crontab -l 2>/dev/null; echo "0 0 * * * docker exec script_tempo_container bash -c 'cd /usr/src/script && python script_tempo_monday.py' >> /home/devops/script_tempo_monday/cron.log 2>&1") | crontab -


echo "Proceso completado."