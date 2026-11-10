"""
validation.py
-------------
VALIDACIÓN Y RESULTADOS: comprueba que el dataset integrado es correcto y
calcula la relación entre temperatura máxima y radiación diaria.

    validar_integracion(rad_diaria, temp, datos)  -> list[str]  (10 controles)
    calcular_resultados(datos)                    -> (pearson, spearman, list[str])
    graficar_dispersion(datos, ruta_salida)
    graficar_serie_temporal(datos, ruta_salida)
    ejecutar_validacion_y_resultados(...)         -> todo lo anterior + informe .txt

Autoprueba con datos sintéticos:  python validation.py
"""

from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sin ventana: funciona también en servidores
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


class ValidacionError(Exception):
    """Datos que impiden continuar (columnas ausentes, muestra insuficiente...)."""


@dataclass(frozen=True)
class Config:
    col_fecha: str = "fecha_dia"
    col_rad: str = "radiacion_diaria"
    col_temp: str = "temp_max_c"
    rad_max: float = 12000.0        # Wh/m² por día
    temp_min: float = 0.0           # °C (exclusivo)
    temp_max: float = 50.0          # °C (exclusivo)
    min_registros: int = 30
    max_pct_faltantes: float = 10.0
    min_cobertura: float = 90.0
    max_pct_atipicos: float = 5.0
    max_racha: int = 7
    confianza: float = 0.95


# ---------------------------------------------------------------- utilidades

def _fechas(s):
    f = pd.to_datetime(s, errors="coerce")
    if f.dt.tz is not None:
        f = f.dt.tz_localize(None)
    return f.dt.normalize()


def _num(s):
    return pd.to_numeric(s, errors="coerce").to_numpy(dtype="float64", na_value=np.nan)


def _atipicos(v):
    q1, q3 = np.percentile(v, [25, 75])
    i = q3 - q1
    return int(((v < q1 - 1.5 * i) | (v > q3 + 1.5 * i)).sum())


def _racha(s):
    return int(s.groupby((s != s.shift()).cumsum()).size().max())


def _p(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def _prep(datos, cfg):
    """DataFrame limpio (x=temperatura, y=radiación, fecha), ordenado por fecha."""
    faltan = [c for c in (cfg.col_temp, cfg.col_rad) if c not in datos.columns]
    if faltan:
        raise ValidacionError(f"Faltan columnas: {', '.join(faltan)}")
    df = pd.DataFrame({"x": _num(datos[cfg.col_temp]), "y": _num(datos[cfg.col_rad])})
    df["fecha"] = (_fechas(datos[cfg.col_fecha]).to_numpy()
                   if cfg.col_fecha in datos.columns else pd.NaT)
    df = (df.replace([np.inf, -np.inf], np.nan).dropna(subset=["x", "y"])
            .sort_values("fecha", kind="stable").reset_index(drop=True))
    if len(df) < 3 or df["x"].nunique() < 2 or df["y"].nunique() < 2:
        raise ValidacionError("Muestra insuficiente o variable constante: "
                              "no se puede calcular la correlación")
    return df


def _guardar(fig, ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    print(f"  Gráfica guardada en {ruta}")


# ---------------------------------------------------------------- validación

def validar_integracion(rad_diaria, temp, datos, cfg=None, verbose=True):
    """
    Ejecuta 10 controles de calidad. Devuelve líneas con [OK], [ALERTA]
    (revisar, no invalida) o [FALLA] (invalida el dataset integrado).
    """
    cfg = cfg or Config()
    out = []

    def chk(ok, msg, sev="FALLA"):
        out.append(f"[{'OK' if ok else sev}] {msg}")

    def fin():
        if verbose:
            print("\n".join("  " + linea for linea in out))
        return out

    # 1. Estructura
    faltan = [f"{n}.{c}" for n, df, cols in (
        ("rad_diaria", rad_diaria, [cfg.col_fecha]), ("temp", temp, [cfg.col_fecha]),
        ("datos", datos, [cfg.col_fecha, cfg.col_rad, cfg.col_temp]))
        for c in cols if c not in df.columns]
    if faltan or datos.empty:
        chk(False, "Estructura: " + (f"faltan columnas {', '.join(faltan)}"
                                     if faltan else "el dataset integrado está vacío"))
        return fin()
    chk(True, f"Estructura: columnas presentes, {len(datos)} registros")

    fr, ft, fd = (_fechas(d[cfg.col_fecha]) for d in (rad_diaria, temp, datos))

    # 2. Fechas interpretables
    inv = [int(f.isna().sum()) for f in (fd, fr, ft)]
    chk(sum(inv) == 0, f"Fechas no interpretables: integrado {inv[0]}, "
        f"radiación {inv[1]}, temperatura {inv[2]}", "FALLA" if inv[0] else "ALERTA")

    # 3. Registros = días en común
    sr, st = set(fr.dropna()), set(ft.dropna())
    comun = len(sr & st)
    chk(len(datos) == comun, f"Registros: esperados {comun}, obtenidos {len(datos)}")

    # 4. Fechas duplicadas
    dup = [int(f.dropna().duplicated().sum()) for f in (fd, fr, ft)]
    chk(sum(dup) == 0, f"Fechas duplicadas: integrado {dup[0]}, radiación {dup[1]}, "
        f"temperatura {dup[2]}", "FALLA" if dup[0] else "ALERTA")

    # 5. Cobertura
    base = min(len(sr), len(st))
    cob = 100 * comun / base if base else 0
    chk(cob >= cfg.min_cobertura, f"Cobertura: {cob:.1f} % de los días de la "
        f"fuente más corta están en el integrado", "ALERTA")

    # 6. Nulos e infinitos
    t = pd.DataFrame({"f": fd.to_numpy(), "rad": _num(datos[cfg.col_rad]),
                      "temp": _num(datos[cfg.col_temp])}).sort_values("f", kind="stable")
    nulos = int(t[["rad", "temp"]].isna().sum().sum())
    inf = int(np.isinf(t[["rad", "temp"]]).sum().sum())
    chk(nulos == 0 and inf == 0, f"Valores: nulos o no numéricos {nulos}, infinitos {inf}")
    t = t.replace([np.inf, -np.inf], np.nan)
    r, tp = t["rad"].dropna(), t["temp"].dropna()
    if r.empty or tp.empty:
        chk(False, "Rangos: no hay valores numéricos válidos")
        return fin()

    # 7. Rangos plausibles
    chk(0 <= r.min() and r.max() <= cfg.rad_max
        and cfg.temp_min < tp.min() and tp.max() < cfg.temp_max,
        f"Rangos: radiación {r.min():.0f}-{r.max():.0f} Wh/m², "
        f"temperatura {tp.min()}-{tp.max()} °C")

    # 8. Muestra y variabilidad
    var = r.nunique() > 1 and tp.nunique() > 1
    n = len(t[["rad", "temp"]].dropna())
    chk(n >= cfg.min_registros and var, f"Muestra: {n} pares válidos (mínimo "
        f"{cfg.min_registros}), variabilidad {'sí' if var else 'NO'}",
        "ALERTA" if var else "FALLA")

    # 9. Continuidad temporal
    fu = t["f"].dropna().drop_duplicates()
    if len(fu) > 1:
        dias = (fu.max() - fu.min()).days + 1
        falt = dias - len(fu)
        chk(100 * falt / dias <= cfg.max_pct_faltantes,
            f"Continuidad: {falt} días sin dato entre {fu.min():%Y-%m-%d} "
            f"y {fu.max():%Y-%m-%d}", "ALERTA")

    # 10. Atípicos (IQR) y valores idénticos consecutivos
    at = [_atipicos(v) for v in (r, tp)]
    racha = max(_racha(t["rad"]), _racha(t["temp"]))
    chk(max(100 * a / len(v) for a, v in zip(at, (r, tp))) <= cfg.max_pct_atipicos
        and racha < cfg.max_racha, f"Atípicos (IQR): radiación {at[0]}, temperatura "
        f"{at[1]}; valores idénticos consecutivos máx {racha}", "ALERTA")
    return fin()


# ---------------------------------------------------------------- resultados

def _describir(r):
    """Clasifica la magnitud de un coeficiente de correlación."""
    fuerza = "fuerte" if abs(r) >= 0.6 else "moderada" if abs(r) >= 0.3 else "débil"
    signo = "positiva (si sube una, tiende a subir la otra)" if r > 0 \
        else "negativa (si sube una, tiende a bajar la otra)"
    return f"{fuerza}, {signo}"


def calcular_resultados(datos, cfg=None, verbose=True):
    """Pearson (con IC), Spearman y regresión lineal simple.
    Devuelve (pearson, spearman, lineas)."""
    cfg = cfg or Config()
    df = _prep(datos, cfg)
    x, y, n = df["x"].to_numpy(), df["y"].to_numpy(), len(df)
    r, p_r = stats.pearsonr(x, y)
    rho, p_s = stats.spearmanr(x, y)
    reg = stats.linregress(x, y)
    nc, alfa = int(cfg.confianza * 100), 1 - cfg.confianza

    ic = (np.tanh(np.arctanh(r) + np.array([-1, 1]) * stats.norm.ppf(1 - alfa / 2)
                  / np.sqrt(n - 3)) if n > 3 and abs(r) < 1 else (np.nan, np.nan))
    tc = stats.t.ppf(1 - alfa / 2, n - 2)
    resid = y - (reg.intercept + reg.slope * x)
    rmse = np.sqrt(np.mean(resid ** 2))
    rho1 = (np.corrcoef(resid[:-1], resid[1:])[0, 1]
            if df["fecha"].notna().all() and resid.std() > 0 else np.nan)

    lineas = [
        f"Días analizados: {n}",
        f"Correlación de Pearson:  {r:.3f} (IC {nc} %: [{ic[0]:.3f}, {ic[1]:.3f}], "
        f"{_p(p_r)}) -> {_describir(r)}",
        f"Correlación de Spearman: {rho:.3f} ({_p(p_s)}) -> {_describir(rho)}",
        f"Regresión lineal: por cada +1 °C de temperatura máxima, la radiación "
        f"diaria cambia en promedio {reg.slope:.0f} Wh/m² (IC {nc} %: "
        f"[{reg.slope - tc * reg.stderr:.0f}, {reg.slope + tc * reg.stderr:.0f}])",
        f"R² = {reg.rvalue ** 2:.3f}: la temperatura máxima está asociada con "
        f"cerca del {reg.rvalue ** 2 * 100:.0f} % de la variación de la radiación diaria",
        f"Error del ajuste (RMSE): {rmse:.0f} Wh/m²",
    ]
    if rho1 > 0.3:
        lineas.append(f"Aviso: los residuos de días consecutivos están correlacionados "
                      f"(lag-1 = {rho1:.2f}); los p-valores y los intervalos son "
                      f"optimistas (n efectivo aprox. {n * (1 - rho1) / (1 + rho1):.0f}).")
    lineas.append("Nota: una correlación mide relación, no prueba que una "
                  "variable cause la otra.")
    if verbose:
        print("\n".join("  " + linea for linea in lineas))
    return r, rho, lineas


# ------------------------------------------------------------------ gráficas

def graficar_dispersion(datos, ruta_salida, cfg=None, ciudad="Ibagué"):
    """Dispersión temperatura máxima vs radiación diaria, con recta y su IC."""
    cfg = cfg or Config()
    df = _prep(datos, cfg)
    x, y, n = df["x"].to_numpy(), df["y"].to_numpy(), len(df)
    reg = stats.linregress(x, y)
    xs = np.linspace(x.min(), x.max(), 100)
    ys = reg.intercept + reg.slope * xs
    s = np.sqrt(np.sum((y - reg.intercept - reg.slope * x) ** 2) / (n - 2))
    se = s * np.sqrt(1 / n + (xs - x.mean()) ** 2 / np.sum((x - x.mean()) ** 2))
    tc = stats.t.ppf(1 - (1 - cfg.confianza) / 2, n - 2)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(x, y, alpha=float(np.clip(500 / n, 0.1, 0.6)), s=12)
    ax.plot(xs, ys, color="red", label=f"Ajuste lineal (R² = {reg.rvalue ** 2:.2f})")
    ax.fill_between(xs, ys - tc * se, ys + tc * se, color="red", alpha=0.15,
                    label=f"IC {int(cfg.confianza * 100)} % de la recta")
    ax.set(xlabel="Temperatura máxima diaria (°C)", ylabel="Radiación diaria (Wh/m²)",
           title=f"Temperatura máxima vs radiación solar diaria - {ciudad}")
    ax.legend()
    _guardar(fig, ruta_salida)


def graficar_serie_temporal(datos, ruta_salida, cfg=None, ciudad="Ibagué", ventana=30):
    """Radiación y temperatura en el tiempo, con media móvil."""
    cfg = cfg or Config()
    df = _prep(datos, cfg).dropna(subset=["fecha"]).set_index("fecha")
    if df.empty:
        raise ValidacionError("No hay fechas válidas para la serie temporal")
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for ax, col, nombre, color in ((axes[0], "y", "Radiación diaria (Wh/m²)", "tab:orange"),
                                   (axes[1], "x", "Temperatura máxima (°C)", "tab:red")):
        ax.plot(df.index, df[col], color=color, alpha=0.35, lw=0.8, label="Dato diario")
        m = df[col].rolling(f"{ventana}D", min_periods=max(1, ventana // 3)).mean()
        ax.plot(m.index, m.to_numpy(), color=color, lw=2, label=f"Media móvil {ventana} días")
        ax.set_ylabel(nombre)
        ax.legend(loc="upper right")
    axes[0].set_title(f"Evolución temporal - {ciudad}")
    fig.autofmt_xdate()
    _guardar(fig, ruta_salida)


# ---------------------------------------------------------------- orquestador

def ejecutar_validacion_y_resultados(rad_diaria, temp, datos, carpeta_salida="resultados",
                                     cfg=None, ciudad="Ibagué", estricto=False):
    """
    Validación + resultados + gráficas + informe de texto en `carpeta_salida`.
    Con estricto=True lanza ValidacionError si algún control da [FALLA].
    """
    cfg = cfg or Config()
    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    print("VALIDACIÓN")
    controles = validar_integracion(rad_diaria, temp, datos, cfg)
    if estricto and any(c.startswith("[FALLA]") for c in controles):
        raise ValidacionError("Hay controles con [FALLA]; revise el dataset integrado")
    try:
        print("\nRESULTADOS")
        _, _, lineas = calcular_resultados(datos, cfg)
        print("\nGRÁFICAS")
        graficar_dispersion(datos, carpeta / "dispersion.png", cfg, ciudad)
        graficar_serie_temporal(datos, carpeta / "serie_temporal.png", cfg, ciudad)
    except ValidacionError as e:
        lineas = [f"No se calcularon resultados: {e}"]
        print(f"  [FALLA] {lineas[0]}")
    informe = carpeta / "informe_validacion.txt"
    informe.write_text("\n".join(["CONTROLES", *controles, "", "RESULTADOS", *lineas]) + "\n",
                       encoding="utf-8")
    return {"controles": controles, "resultados": lineas, "informe": str(informe)}


if __name__ == "__main__":
    print("Autoprueba con datos SINTÉTICOS (no son datos reales)\n")
    rng = np.random.default_rng(42)
    fechas = pd.date_range("2022-01-01", "2023-12-31", freq="D")
    tmax = np.round(29 + 2.5 * np.sin(2 * np.pi * (fechas.dayofyear - 60) / 365)
                    + rng.normal(0, 1.5, len(fechas)), 1)
    ruido = pd.Series(rng.normal(0, 800, len(fechas))).ewm(alpha=0.5).mean().to_numpy()
    rad_d = pd.DataFrame({"fecha_dia": fechas,
                          "radiacion_diaria": np.round(4800 + 140 * (tmax - 29) + ruido)})
    rad_d = rad_d.drop(index=range(100, 110))
    temp_d = pd.DataFrame({"fecha_dia": fechas, "temp_max_c": tmax}).iloc[5:]
    ejecutar_validacion_y_resultados(rad_d, temp_d, rad_d.merge(temp_d, on="fecha_dia"),
                                     "resultados_demo", ciudad="Ibagué (demo)")
