"""
main.py
-------
Punto de entrada del proyecto. Ejecuta el pipeline ETL completo en orden:

  1. Extracción      (src/extraction.py)
  2. Diagnóstico     (src/cleaning.py)
  3. Limpieza        (src/cleaning.py)
  4. Transformación  (src/transformation.py)
  5. Integración     (src/integration.py)
  6. Validación y resultados (src/validation.py)

Cómo ejecutarlo (desde cualquier carpeta):  python main.py
"""

import sys
from pathlib import Path

import pandas as pd

from src import extraction, cleaning, transformation, integration, validation

# ----------------------------------------------------------------------
# Parámetros del proyecto
# ----------------------------------------------------------------------
# Todas las rutas se construyen a partir de la ubicación de este archivo,
# así el pipeline funciona sin importar desde qué carpeta se ejecute.
BASE_DIR = Path(__file__).resolve().parent
RUTA_RADIACION = BASE_DIR / "data" / "raw" / "Radiacion.csv"
RUTA_TEMPERATURA = BASE_DIR / "data" / "raw" / "Temperatura.csv"
DIR_PROCESADOS = BASE_DIR / "data" / "processed"
DIR_SALIDAS = BASE_DIR / "outputs"
MIN_HORAS = 20  # un día de radiación se conserva solo si tiene 20 horas o más


def main():
    # Las carpetas de salida se crean si no existen (git no guarda carpetas vacías)
    DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)
    DIR_SALIDAS.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    print("\n=== 1. EXTRACCIÓN ===")
    rad_raw = extraction.cargar_csv(RUTA_RADIACION)
    temp_raw = extraction.cargar_csv(RUTA_TEMPERATURA)

    # ------------------------------------------------------------------
    print("\n=== 2. DIAGNÓSTICO DE CALIDAD (datos originales) ===")
    diag_rad = cleaning.diagnosticar(rad_raw, "Radiación", frecuencia="h")
    diag_temp = cleaning.diagnosticar(temp_raw, "Temperatura", frecuencia="D")
    pd.DataFrame([diag_rad, diag_temp]).to_csv(
        DIR_SALIDAS / "diagnostico_calidad.csv", index=False, encoding="utf-8-sig"
    )

    # ------------------------------------------------------------------
    print("\n=== 3. LIMPIEZA ===")
    rad = cleaning.convertir_fecha(rad_raw)
    temp = cleaning.convertir_fecha(temp_raw)

    rad = cleaning.renombrar_columnas(rad, "radiacion_wh_m2")
    temp = cleaning.renombrar_columnas(temp, "temp_max_c")

    print("Radiación:")
    rad = cleaning.quitar_duplicados_y_nulos(rad, "radiacion_wh_m2")
    print("Temperatura:")
    temp = cleaning.quitar_duplicados_y_nulos(temp, "temp_max_c")

    rad, meta_rad = cleaning.quitar_columnas_constantes(rad, "radiacion_wh_m2")
    temp, meta_temp = cleaning.quitar_columnas_constantes(temp, "temp_max_c")
    print("Metadatos conservados de radiación:", meta_rad)
    print("Metadatos conservados de temperatura:", meta_temp)

    # ------------------------------------------------------------------
    print("\n=== 4. TRANSFORMACIÓN ===")
    rad = transformation.separar_fecha_hora(rad)
    temp = transformation.separar_fecha_hora(temp)

    # La temperatura es diaria: comprobamos que su hora es siempre la misma
    horas_temp = temp["hora"].unique().tolist()
    print(f"  Horas distintas en temperatura: {horas_temp} "
          "(si es solo 0, la hora no aporta información en este dataset)")

    rad_diaria = transformation.agregar_radiacion_diaria(rad)
    rad_diaria = transformation.filtrar_cobertura(rad_diaria, MIN_HORAS)

    # ------------------------------------------------------------------
    print("\n=== 5. INTEGRACIÓN ===")
    datos = integration.unir_datasets(rad_diaria, temp)

    # ------------------------------------------------------------------
    print("\n=== 6. VALIDACIÓN ===")
    lineas_validacion = validation.validar_integracion(rad_diaria, temp, datos)

    # Si algún control falla o no hay datos, el pipeline se detiene: no se
    # guarda un dataset que no pasó la validación.
    fallas = [linea for linea in lineas_validacion if linea.startswith("[FALLA]")]
    if datos.empty or fallas:
        raise ValueError(
            "La validación del dataset integrado falló: "
            + ("dataset vacío. " if datos.empty else "")
            + " | ".join(fallas)
        )

    # Guardamos el primer dataset consolidado
    datos.to_csv(DIR_PROCESADOS / "datos_integrados.csv", index=False, encoding="utf-8-sig")
    print("  Dataset consolidado guardado en data/processed/datos_integrados.csv")

    # ------------------------------------------------------------------
    print("\n=== 7. RESULTADOS ===")
    pearson, spearman, lineas_resultados = validation.calcular_resultados(datos)
    validation.graficar_dispersion(datos, DIR_SALIDAS / "dispersion_temp_vs_radiacion.png")

    with open(DIR_SALIDAS / "resultados.txt", "w", encoding="utf-8") as archivo:
        archivo.write("VALIDACIÓN\n" + "\n".join(lineas_validacion) + "\n\n")
        archivo.write("RESULTADOS\n" + "\n".join(lineas_resultados) + "\n")
    print("  Resumen guardado en outputs/resultados.txt")

    print("\nPipeline terminado.")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, KeyError) as error:
        # Error explícito y código de salida distinto de 0: nunca falla en silencio
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)
