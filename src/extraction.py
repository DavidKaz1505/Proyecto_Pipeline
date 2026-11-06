"""
extraction.py
-------------
EXTRACCIÓN: lee los archivos originales (raw) y los carga en DataFrames.

Importante: aquí NO se modifica nada. Los archivos de data/raw quedan
intactos para cumplir con "conservación de los datos originales".
"""

import pandas as pd


def cargar_csv(ruta):
    """Lee un archivo CSV y devuelve un DataFrame."""
    df = pd.read_csv(ruta)
    print(f"Archivo cargado: {ruta}  ->  {df.shape[0]} filas, {df.shape[1]} columnas")
    return df
