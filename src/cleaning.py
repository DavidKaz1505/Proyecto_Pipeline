"""
cleaning.py
-----------
DIAGNÓSTICO DE CALIDAD y LIMPIEZA básica.

Primero medimos los problemas (diagnóstico) y luego los corregimos.
Todas las funciones trabajan sobre una COPIA del DataFrame, así los datos
originales cargados en extraction.py nunca se modifican.
"""

import pandas as pd


# ----------------------------------------------------------------------
# DIAGNÓSTICO
# ----------------------------------------------------------------------
def diagnosticar(df, nombre, frecuencia):
    """
    Cuenta los problemas de calidad de un DataFrame crudo.
    frecuencia: "h" si los datos son horarios, "D" si son diarios.
    Devuelve un diccionario con los números para poder guardarlos.
    """
    # Convertimos la fecha en una variable temporal solo para poder medir
    fechas = pd.to_datetime(df["Fecha"], errors="coerce")

    # Cuántos registros debería haber si no faltara ningún dato
    esperados = len(pd.date_range(fechas.min(), fechas.max(), freq=frecuencia))

    resultado = {
        "dataset": nombre,
        "filas": len(df),
        "nulos_totales": int(df.isna().sum().sum()),
        "filas_duplicadas": int(df.duplicated().sum()),
        "fechas_duplicadas": int(df.duplicated(subset=["Fecha"]).sum()),
        "fechas_invalidas": int(fechas.isna().sum()),
        "tipo_columna_Fecha": str(df["Fecha"].dtype),
        "valores_negativos": int((df["Valor"] < 0).sum()),
        "fecha_inicio": str(fechas.min()),
        "fecha_fin": str(fechas.max()),
        "registros_esperados": esperados,
        "registros_faltantes": esperados - len(df),
    }

    print(f"\n--- Diagnóstico de {nombre} ---")
    for clave, valor in resultado.items():
        print(f"  {clave}: {valor}")
    return resultado


# ----------------------------------------------------------------------
# LIMPIEZA (cada función corrige un problema concreto)
# ----------------------------------------------------------------------
def convertir_fecha(df):
    """
    TRANSFORMACIÓN 1: convertir la fecha de texto a tipo fecha-hora.
    Por qué: la columna Fecha viene como texto; con ese tipo no se puede
    separar la fecha de la hora ni hacer cálculos con fechas.
    """
    df = df.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


def renombrar_columnas(df, nombre_valor):
    """
    TRANSFORMACIÓN 2: estandarizar nombres de columnas.
    Por qué: ambos archivos llaman 'Valor' a la medición, y al hacer el
    merge no sabríamos cuál es radiación y cuál es temperatura.
    """
    df = df.copy()
    df = df.rename(columns={
        "CodigoEstacion": "codigo_estacion",
        "NombreEstacion": "estacion",
        "Variable": "variable",
        "Parametro": "parametro",
        "Fecha": "fecha_hora",
        "Unidad": "unidad",
        "Valor": nombre_valor,
        "NivelAprobacion": "nivel_aprobacion",
    })
    return df


def quitar_duplicados_y_nulos(df, columna_valor):
    """
    TRANSFORMACIÓN 3: eliminar filas duplicadas y filas sin valor medido.
    Por qué: un duplicado contaría dos veces el mismo dato y un nulo
    dañaría la correlación. En estos datos el diagnóstico dio 0 de cada
    uno, pero dejamos el control para que el pipeline sea reutilizable.
    """
    df = df.copy()
    antes = len(df)
    df = df.drop_duplicates()
    df = df.dropna(subset=[columna_valor])
    print(f"  Filas eliminadas por duplicados/nulos: {antes - len(df)}")
    return df


def quitar_columnas_constantes(df, columna_valor):
    """
    TRANSFORMACIÓN 4: eliminar columnas que tienen el mismo valor en todas
    las filas (estación, unidad, nivel de aprobación, etc.).
    Por qué: no aportan información para el análisis. Antes de borrarlas
    guardamos su valor en un diccionario (metadatos) para documentarlo.
    """
    df = df.copy()
    metadatos = {}
    for columna in df.columns:
        if columna in ("fecha_hora", columna_valor):
            continue  # estas dos nunca se eliminan
        if df[columna].nunique() == 1:
            metadatos[columna] = str(df[columna].iloc[0])
            df = df.drop(columns=columna)
    return df, metadatos
