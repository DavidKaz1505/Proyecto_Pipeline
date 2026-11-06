"""
integration.py
--------------
INTEGRACIÓN: une radiación diaria y temperatura en un solo dataset.

Clave de relación: fecha_dia (la fecha sin hora que creamos en transformation.py).
"""

import pandas as pd


def unir_datasets(rad_diaria, temp):
    """
    Hace el merge por fecha_dia con how="inner".
    Por qué inner: nos quedamos solo con los días que existen en AMBOS
    datasets. Un día con temperatura pero sin radiación (o al revés) no
    sirve para estudiar la relación entre las dos variables.
    """
    # Control previo: la clave debe ser del mismo tipo en los dos lados,
    # si no, el merge devuelve cero filas sin avisar.
    tipo_rad = rad_diaria["fecha_dia"].dtype
    tipo_temp = temp["fecha_dia"].dtype
    print(f"  Tipo de fecha_dia -> radiación: {tipo_rad} | temperatura: {tipo_temp}")

    datos = pd.merge(
        rad_diaria,
        temp[["fecha_dia", "temp_max_c"]],
        on="fecha_dia",
        how="inner",
    )
    print(f"  Dataset integrado: {len(datos)} filas")
    return datos
