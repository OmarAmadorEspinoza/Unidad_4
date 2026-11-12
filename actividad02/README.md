# Unidad 4 – Actividad 02: RESTCONF con Python y Tkinter

- **Alumno:** Omar Manuel Amador Espinoza
- **No. de control:** 1225100271
- **No. de lista:** 3
- **Grupo:** GTIR246
- **Fecha:** 11 de noviembre de 2026
- **Rama de entrega:** `feat/unidad4_act02`

## Descripción

Cliente RESTCONF con interfaz gráfica (Tkinter) para consultar, crear/actualizar y eliminar interfaces en un router Cisco Catalyst 8000v (IOS XE 17.12.02) del DevNet Sandbox.

## Requisitos

- Python 3
- `requests` y `tkinter` (`sudo apt install python3-requests python3-tk`)
- Conexión VPN al sandbox y acceso al router

## Ejecución

```bash
python3 restconf_gui.py
```

El host, usuario y password se capturan desde la ventana (sección *Conexión*).

## Contenido

- `restconf_gui.py`: aplicación Tkinter.
- `capturas/`: evidencias de la GUI operando.

| Captura | Prueba |
|---|---|
| 01 | Ventana inicial |
| 02, 03 | Consulta de interfaces (200) |
| 04 | Creación de Loopback99 (201) |
| 05 | Error 404 (interfaz inexistente) |
| 06 | Error 401 (password incorrecto) |
| 07 | Confirmación de eliminación |
| 08 | Eliminación (204) |
