# ThreadReader

Web app para ver hilos de twitter de una forma mas legible. Actualmente hosteada en https://threadreader.xyz/

## Deployment local

### Requisitos:

- Python = ^3.10.x

- pip (el proyecto usa la version 22.2.2)

- (opcional) venv

- Dependencias declaradas en `thread_reader/requirements.txt`. Se pueden instalar con
  
  ```
  pip install -r requirements.txt
  ```

- Archivo `.env` con campos Bearer Token (creando una cuenta en https://developer.twitter.com/en ) y Django Secret (se puede generar en https://djecrety.ir ). Este archivo va en la ubicacion `thread_reader/thread_reader/.env` (misma carpeta donde esta el settings.py) y se compone en estilo
  
  ```
  DJANGO_SECRET=valor
  BEARER_TOKEN=valor
  ```

Para usar el modo _mock_ se necesitan archivos json que representen respuestas de tweet y thread. Estos se pueden generar usando el `mock_provider`.

## Mock provider

Este modulo nacio de la necesidad de probar casos extremos en los datos de tweet que maneja la aplicacion, ademas tiene el beneficio de permitirme probar cambios consantes sin agotar la *quota* mensual de la api.
