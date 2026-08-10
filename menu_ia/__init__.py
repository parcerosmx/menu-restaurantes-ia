"""Menú para Restaurantes con IA — motor de menús impresos.

El motor NO conoce a ningún cliente. Necesita tres cosas del proyecto que lo
use, y las tres se eligen por variable de entorno:

    MENU_CARTA    paquete con el contenido: `SPREADS`, `ORDEN`, `TITULO`
    MENU_TEMAS    módulo con el diccionario `TEMAS` (identidad visual)
    MENU_FORMATO  nombre del formato de papel

Sin ellas se importa igual, y falla cuando alguien pide pintar algo — no en
tiempo de import, que es lo que impedía instalarlo en un proyecto que no fuera
Parceros.
"""
__version__ = "0.1.0"
