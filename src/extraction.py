"""
extraction.py
-------------
EXTRACCIÓN: lee los archivos originales (raw) y los carga en DataFrames.

Importante: aquí NO se modifica nada. Los archivos de data/raw quedan
intactos para cumplir con "conservación de los datos originales".

Antes de devolver el DataFrame se validan la ruta y el esquema (columnas y
tipo de la medición). Si algo falla se lanza un error con un mensaje claro:
el pipeline nunca continúa con datos que no puede interpretar.
"""

from pathlib import Path

import pandas as pd

# Columnas que deben traer los CSV descargados del IDEAM
COLUMNAS_ESPERADAS = {
    "CodigoEstacion", "NombreEstacion", "Variable", "Parametro",
    "Fecha", "Unidad", "Valor", "NivelAprobacion",
}


def validar_ruta(ruta):
    """Comprueba que la ruta exista, sea un archivo y sea un CSV."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}. "
            "Verifique que esté en data/raw/ con ese nombre exacto."
        )
    if not ruta.is_file():
        raise ValueError(f"La ruta no es un archivo: {ruta}")
    if ruta.suffix.lower() != ".csv":
        raise ValueError(f"Se esperaba un archivo .csv y se recibió: {ruta.name}")
    return ruta


def validar_esquema(df, nombre):
    """Comprueba que el DataFrame tenga las columnas y tipos esperados."""
    if df.empty:
        raise ValueError(f"{nombre}: el archivo no contiene filas.")

    faltantes = COLUMNAS_ESPERADAS - set(df.columns)
    if faltantes:
        raise ValueError(
            f"{nombre}: faltan columnas {sorted(faltantes)}. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    if not pd.api.types.is_numeric_dtype(df["Valor"]):
        raise ValueError(
            f"{nombre}: la columna 'Valor' debe ser numérica y es de tipo "
            f"{df['Valor'].dtype}. Revise si hay texto mezclado con los números."
        )


def cargar_csv(ruta):
    """Valida la ruta, lee un CSV, valida su esquema y devuelve un DataFrame."""
    ruta = validar_ruta(ruta)
    try:
        df = pd.read_csv(ruta)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        raise ValueError(f"No se pudo leer {ruta.name} como CSV: {error}") from error

    validar_esquema(df, ruta.name)
    print(f"Archivo cargado: {ruta.name}  ->  {df.shape[0]} filas, {df.shape[1]} columnas "
          "(ruta y esquema validados)")
    return df
