"""
validation.py
-------------
VALIDACIÓN Y RESULTADOS: comprueba que el dataset integrado es correcto y
calcula la relación entre temperatura máxima y radiación diaria.
"""

import matplotlib
matplotlib.use("Agg")  # backend sin ventana: funciona también en servidores
import matplotlib.pyplot as plt
from scipy import stats


def validar_integracion(rad_diaria, temp, datos):
    """
    Ejecuta los controles de calidad sobre el dataset integrado.
    Devuelve una lista de líneas de texto con [OK] o [FALLA] por control.
    """
    lineas = []

    def registrar(ok, mensaje):
        lineas.append(("[OK] " if ok else "[FALLA] ") + mensaje)

    # 1. Conteo de registros: debe ser igual al número de días en común
    esperados = len(set(rad_diaria["fecha_dia"]) & set(temp["fecha_dia"]))
    registrar(len(datos) == esperados,
              f"Registros: esperados {esperados}, obtenidos {len(datos)}")

    # 2. La clave de relación no debe repetirse
    duplicadas = int(datos["fecha_dia"].duplicated().sum())
    registrar(duplicadas == 0,
              f"Fechas duplicadas en el dataset integrado: {duplicadas}")

    # 3. Sin nulos en las variables de interés
    nulos = int(datos[["radiacion_diaria", "temp_max_c"]].isna().sum().sum())
    registrar(nulos == 0, f"Nulos en radiación o temperatura: {nulos}")

    # 4. Rangos plausibles (radiación y temperatura no negativas)
    rad_min = datos["radiacion_diaria"].min()
    t_min, t_max = datos["temp_max_c"].min(), datos["temp_max_c"].max()
    registrar(rad_min >= 0 and 0 < t_min and t_max < 50,
              f"Rangos: radiación mín {rad_min:.0f} | "
              f"temperatura mín {t_min} y máx {t_max}")

    for linea in lineas:
        print("  " + linea)
    return lineas


def _describir(r):
    """Clasifica la magnitud de un coeficiente de correlación."""
    fuerza = "fuerte" if abs(r) >= 0.6 else "moderada" if abs(r) >= 0.3 else "débil"
    signo = "positiva (si sube una, tiende a subir la otra)" if r > 0 \
        else "negativa (si sube una, tiende a bajar la otra)"
    return f"{fuerza}, {signo}"


def calcular_resultados(datos):
    """Calcula Pearson, Spearman y una regresión lineal simple."""
    x, y = datos["temp_max_c"], datos["radiacion_diaria"]
    pearson = stats.pearsonr(x, y)[0]
    spearman = stats.spearmanr(x, y)[0]
    reg = stats.linregress(x, y)

    lineas = [
        f"Días analizados: {len(datos)}",
        f"Correlación de Pearson:  {pearson:.3f} -> {_describir(pearson)}",
        f"Correlación de Spearman: {spearman:.3f} -> {_describir(spearman)}",
        f"Regresión lineal: por cada +1 °C de temperatura máxima, la "
        f"radiación diaria cambia en promedio {reg.slope:.0f} Wh/m²",
        f"R² = {reg.rvalue ** 2:.3f}: la temperatura máxima está asociada con "
        f"cerca del {reg.rvalue ** 2 * 100:.0f} % de la variación de la radiación diaria",
        "Nota: una correlación mide relación, no prueba que una variable "
        "cause la otra.",
    ]
    for linea in lineas:
        print("  " + linea)
    return pearson, spearman, lineas


def graficar_dispersion(datos, ruta_salida):
    """Dispersión temperatura máxima vs radiación diaria con recta de ajuste."""
    reg = stats.linregress(datos["temp_max_c"], datos["radiacion_diaria"])
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(datos["temp_max_c"], datos["radiacion_diaria"], alpha=0.3, s=12)
    xs = [datos["temp_max_c"].min(), datos["temp_max_c"].max()]
    ax.plot(xs, [reg.intercept + reg.slope * v for v in xs], color="red",
            label=f"Ajuste lineal (R² = {reg.rvalue ** 2:.2f})")
    ax.set_xlabel("Temperatura máxima diaria (°C)")
    ax.set_ylabel("Radiación diaria (Wh/m²)")
    ax.set_title("Temperatura máxima vs radiación solar diaria - Ibagué")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)
    print(f"  Gráfica guardada en {ruta_salida}")
