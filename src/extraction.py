"""
extraction.py
-------------
EXTRACCIÓN: lee un CSV original de data/raw/ y lo devuelve como DataFrame.
 
Aquí NO se modifica nada: los archivos originales quedan intactos.
Antes de devolver los datos se hacen 4 controles. Si alguno falla, el
programa se detiene con un mensaje claro (nunca sigue con datos que no
puede interpretar).
"""
 
from pathlib import Path
 
import pandas as pd
 
# Columnas que deben traer los CSV descargados del IDEAM
COLUMNAS_ESPERADAS = {
    "CodigoEstacion", "NombreEstacion", "Variable", "Parametro",
    "Fecha", "Unidad", "Valor", "NivelAprobacion",
}
 
 
def cargar_csv(ruta):
    """Lee un CSV, comprueba que esté bien y devuelve un DataFrame."""
    ruta = Path(ruta)
 
    # Control 1: el archivo debe existir y ser un .csv
    if not ruta.is_file():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}. "
            "Verifique que esté en data/raw/ con ese nombre exacto."
        )
    if ruta.suffix.lower() != ".csv":
        raise ValueError(f"Se esperaba un archivo .csv y se recibió: {ruta.name}")
 
    # Control 2: el archivo debe poder leerse como CSV
    try:
        df = pd.read_csv(ruta)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        raise ValueError(f"No se pudo leer {ruta.name} como CSV: {error}") from error
 
    # Control 3: debe tener filas y todas las columnas esperadas
    if df.empty:
        raise ValueError(f"{ruta.name}: el archivo no contiene filas.")
    faltantes = COLUMNAS_ESPERADAS - set(df.columns)
    if faltantes:
        raise ValueError(
            f"{ruta.name}: faltan columnas {sorted(faltantes)}. "
            f"Columnas encontradas: {list(df.columns)}"
        )
 
    # Control 4: la columna Valor debe ser numérica
    if not pd.api.types.is_numeric_dtype(df["Valor"]):
        raise ValueError(
            f"{ruta.name}: la columna 'Valor' debe ser numérica y es de tipo "
            f"{df['Valor'].dtype}. Revise si hay texto mezclado con los números."
        )
 
    print(f"Archivo cargado: {ruta.name}  ->  {df.shape[0]} filas, {df.shape[1]} columnas "
          "(ruta y esquema validados)")
    return df
