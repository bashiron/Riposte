# Riposte

Web app para ver conversaciones de twitter de una forma mas legible. Actualmente hosteada en https://riposte.one/

## Tecnologias

El servidor esta hosteado en Ubuntu 22.04.1 LTS usando Apache2 y el certificado Let's Encrypt.

Uso Django como framework pero no hago persistencia de datos.

El comportamiento del html esta dictado por javascript puro, con las librerias Jquery y Bootstrap.

Para el templating se usa DjangoHTML.

El codigo del controller (views.py), sus modulos auxiliares, la configuracion del servidor frontend y el routing estan implementados en Python.

## Deployment local

### Requisitos:

- Python = ^3.10.x

- pip (el proyecto usa la version 22.2.2)

- (opcional) venv

- Dependencias declaradas en `riposte/requirements.txt`. Se pueden instalar con
  
  ```bash
  pip install -r requirements.txt
  ```

- Archivo `.env` con campos Bearer Token (creando una cuenta en https://developer.twitter.com/en ) y Django Secret (se puede generar en https://djecrety.ir ). Este archivo va en la ubicacion `riposte/.env` (misma carpeta donde esta el settings.py) y se compone en estilo
  
  ```
  DJANGO_SECRET=valor
  BEARER_TOKEN=valor
  ```

Para usar el modo _mock_ se necesitan archivos json que representen respuestas de tweet y chat. Estos se pueden generar usando el `mock_provider`.

## Mock provider

Este modulo, que podria considerarse una aplicacion aparte, nacio de la necesidad de probar casos extremos en los datos de tweet que maneja la aplicacion, ademas tiene el beneficio de permitirme probar cambios consantes sin agotar la *quota* mensual de la api.

Iconos provistos por [fontawesome](https://fontawesome.com/)
