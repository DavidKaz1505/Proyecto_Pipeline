"""
transformation.py
-----------------
TRANSFORMACIÓN: separa fecha y hora, agrega la radiación a nivel diario y
filtra los días con poca cobertura horaria.

Todas las funciones trabajan sobre una COPIA del DataFrame, así los datos
originales nunca se modifican.
"""

import pandas as pd


def separar_fecha_hora(df):
    """
    TRANSFORMACIÓN 5: separar fecha_hora en fecha_dia (sin hora) y hora.
    Por qué: la fecha sin hora es la clave de unión entre los datasets;
    con fecha y hora solo coincidirían los registros de las 00:00.
    """
    df = df.copy()
    df["fecha_dia"] = df["fecha_hora"].dt.normalize()
    df["hora"] = df["fecha_hora"].dt.hour
    return df


def agregar_radiacion_diaria(rad):
    """
    TRANSFORMACIÓN 6: agregar la radiación de horaria a diaria.
    Devuelve una fila por día con la suma de radiación (radiacion_diaria)
    y el número de horas registradas (n_horas).
    Por qué: la temperatura es diaria; ambas variables deben estar al
    mismo nivel de detalle para poder integrarse.
    """
    rad_diaria = (
        rad.groupby("fecha_dia")["radiacion_wh_m2"]
        .agg(radiacion_diaria="sum", n_horas="count")
        .reset_index()
    )
    print(f"  Radiación agregada: {len(rad)} horas -> {len(rad_diaria)} días")
    return rad_diaria


def filtrar_cobertura(rad_diaria, min_horas):
    """
    TRANSFORMACIÓN 7: conservar solo los días con al menos min_horas horas.
    Por qué: un día incompleto suma menos radiación por datos faltantes y
    no por menos sol, lo que distorsiona la correlación.
    """
    antes = len(rad_diaria)
    rad_diaria = rad_diaria[rad_diaria["n_horas"] >= min_horas].copy()
    print(f"  Días con al menos {min_horas} horas: {len(rad_diaria)} "
          f"(se descartan {antes - len(rad_diaria)})")
    return rad_diaria