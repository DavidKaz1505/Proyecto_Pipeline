# Proyecto ETL: temperatura máxima y radiación solar en Ibagué

**Integrantes:**
-  David Casallas
-  Samuel Sarmiento
-  Tomas Cardenas

**Entrega:** Segundo avance del proyecto, 9 de noviembre de 2026

## Inicio rápido

Este proyecto lee dos archivos CSV del IDEAM (radiación solar y temperatura máxima de Ibagué), los limpia, los une en una sola tabla diaria y calcula qué relación hay entre ambas variables. **Los datos ya vienen incluidos en el repositorio**, no hay que descargar nada.

Si ya tiene Python 3 instalado, abra una terminal **dentro de la carpeta del proyecto** (la que contiene `main.py`) y ejecute:

```
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

(En Mac o Linux, la segunda línea es `source venv/bin/activate` y se escribe `python3` en lugar de `python`.)

Si todo sale bien, el programa termina con el mensaje **`Pipeline terminado.`** Los pasos detallados, lo que debe ver en pantalla y las soluciones a los problemas más comunes están en la sección 4.

## 1. Problema y objetivo

**Pregunta:** ¿qué relación existe entre la temperatura máxima diaria y la radiación solar diaria en Ibagué entre diciembre de 2006 y septiembre de 2016?

**Objetivo:** construir un pipeline ETL (extracción, limpieza, transformación, integración y validación) que integre dos fuentes del IDEAM en un único dataset diario y permita medir la relación entre ambas variables.

> Una correlación mide relación, no causalidad. Físicamente la radiación solar es uno de los factores que calientan la superficie, por lo que este análisis describe cómo se mueven juntas ambas variables, no cuál causa a cuál.

## 2. Fuentes de datos

Ambas fuentes se descargaron del portal de atención al ciudadano del IDEAM (atencionalciudadano.ideam.gov.co) en formato CSV y están en `data/raw/`.

| Archivo | Estación | Variable | Frecuencia | Unidad | Registros |
|---|---|---|---|---|---|
| `Radiacion.csv` | Batallón Rooke (21215180) | Radiación solar global horaria validada | Horaria | Wh/m² | 57.020 |
| `Temperatura.csv` | Aeropuerto Perales (21245040) | Temperatura máxima diaria | Diaria | °C | 3.531 |

**Limitación:** las dos variables provienen de estaciones distintas, por lo que no están medidas exactamente en el mismo punto.

## 3. Estructura del proyecto

```
Proyecto_Pipeline/
├── data/
│   ├── raw/                 # archivos originales (no se modifican)
│   └── processed/           # dataset integrado (datos_integrados.csv)
├── src/
│   ├── __init__.py          # marca src como paquete
│   ├── extraction.py        # lectura de los CSV y validación de ruta y esquema
│   ├── cleaning.py          # diagnóstico de calidad y limpieza
│   ├── transformation.py    # separar fecha/hora, agregar a diario, filtrar cobertura
│   ├── integration.py       # merge por fecha
│   └── validation.py        # validaciones, correlación y gráfica
├── outputs/                 # diagnóstico, resultados y gráfica
├── docs/                    # informe técnico del segundo avance (Word y PDF)
├── requirements.txt         # dependencias (pandas, matplotlib, scipy)
├── .gitignore               # excluye venv, caches y archivos .env
├── main.py                  # punto de entrada: ejecuta todo el pipeline
└── README.md
```

**Documentación:** el informe técnico (arquitectura, decisiones técnicas, validaciones y hallazgos iniciales) está en `docs/Informe_Tecnico_Segundo_Avance.docx`, con copia en PDF en `docs/Informe_Tecnico_Segundo_Avance.pdf`.

## 4. Cómo ejecutar (paso a paso)

Esta guía está escrita para una persona que **no conoce el proyecto**. Funciona en Windows, Mac y Linux.

### Paso 1: tener Python 3

Abra una terminal (ver el paso 3 para saber cómo) y escriba:

```
python --version
```

- Debe aparecer algo como `Python 3.12.3`. El equipo desarrolló y probó el proyecto con Python 3.14.6.
- En Windows, si dice que `python` no se reconoce, pruebe con `py --version`. Si tampoco funciona, instale Python desde https://www.python.org/downloads/ y **marque la casilla "Add Python to PATH"** durante la instalación. Luego cierre y vuelva a abrir la terminal.
- En Mac y Linux use `python3` en lugar de `python` en todos los comandos de esta guía.

### Paso 2: obtener el código

- **Opción A (sin Git):** en la página del repositorio de GitHub, botón verde **Code → Download ZIP**. Descomprima el archivo en cualquier carpeta.
- **Opción B (con Git):** `git clone https://github.com/DavidKaz1505/Proyecto_Pipeline.git`

Los archivos de datos (`Radiacion.csv` y `Temperatura.csv`) ya están incluidos en `data/raw/`. No hay que descargar ni mover nada.

### Paso 3: abrir una terminal dentro de la carpeta del proyecto

La carpeta correcta es la que contiene el archivo `main.py`.

- **Con Visual Studio Code:** *Archivo → Abrir carpeta* y elija la carpeta del proyecto; luego *Terminal → Nueva terminal*.
- **Windows sin VS Code:** abra la carpeta en el Explorador de archivos, haga clic derecho en un espacio vacío y elija **Abrir en Terminal** (en Windows 10: mantenga presionada la tecla Shift, clic derecho y **Abrir ventana de PowerShell aquí**).
- **Mac o Linux:** abra la aplicación Terminal, escriba `cd ` (con un espacio al final), arrastre la carpeta del proyecto hasta la ventana de la terminal y presione Enter.

Para comprobar que está en el lugar correcto, escriba `dir` (Windows) o `ls` (Mac/Linux). Debe ver `main.py`, `README.md`, `requirements.txt` y las carpetas `src` y `data`.

### Paso 4: crear y activar un entorno virtual

El entorno virtual mantiene las librerías del proyecto separadas del resto del computador.

| Sistema | Crear | Activar |
|---|---|---|
| Windows (PowerShell o VS Code) | `python -m venv venv` | `venv\Scripts\activate` |
| Mac / Linux | `python3 -m venv venv` | `source venv/bin/activate` |

Cuando quede activado, aparece **`(venv)`** al inicio de la línea de la terminal.

> **Si en Windows aparece un error rojo que menciona "la ejecución de scripts está deshabilitada":** ejecute una sola vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, responda `S` (o `Y`) y vuelva a activar el entorno.

### Paso 5: instalar las librerías

```
python -m pip install -r requirements.txt
```

Instala `pandas`, `matplotlib` y `scipy` (esta última es necesaria para calcular la correlación de Spearman). Puede tardar uno o dos minutos y termina con `Successfully installed ...`. El equipo lo probó con pandas 3.0.6, matplotlib 3.11.2 y scipy 1.18.1; `requirements.txt` exige como mínimo pandas 2.2, matplotlib 3.8 y scipy 1.12.

### Paso 6: ejecutar el proyecto

```
python main.py
```

El programa funciona aunque se ejecute desde otra carpeta, porque calcula las rutas a partir de la ubicación de `main.py`. Tarda unos segundos.

### Paso 7: comprobar que salió bien

La salida se muestra por etapas (`=== 1. EXTRACCIÓN ===` hasta `=== 7. RESULTADOS ===`) y termina con **`Pipeline terminado.`** Estos son los valores que debe ver:

| Qué buscar en pantalla | Valor esperado |
|---|---|
| Archivos cargados | Radiacion.csv: 57020 filas · Temperatura.csv: 3531 filas |
| Días de radiación con al menos 20 horas | 2270 (se descartan 272) |
| Dataset integrado | 2237 filas |
| Las 4 validaciones | todas con `[OK]` |
| Correlación de Pearson | 0.600 |
| Correlación de Spearman | 0.583 |
| Regresión lineal | 317 Wh/m² por cada +1 °C |
| R² | 0.360 |

### Paso 8: ver los resultados generados

| Archivo | Qué contiene |
|---|---|
| `data/processed/datos_integrados.csv` | Tabla final: un registro por día (`fecha_dia`, `radiacion_diaria`, `n_horas`, `temp_max_c`) |
| `outputs/diagnostico_calidad.csv` | Los problemas de calidad de los datos originales, cuantificados |
| `outputs/resultados.txt` | Validaciones y resultados estadísticos |
| `outputs/dispersion_temp_vs_radiacion.png` | Gráfica de dispersión temperatura vs radiación |

Estos archivos ya vienen en el repositorio; al ejecutar el programa se **vuelven a generar** (se sobrescriben con el mismo contenido).

### Problemas comunes

| Mensaje o síntoma | Causa | Solución |
|---|---|---|
| `python` no se reconoce | Python no está instalado o no está en el PATH | Ver el paso 1 |
| `ModuleNotFoundError: No module named 'pandas'` (o `scipy`, `matplotlib`) | El entorno virtual no está activo o faltó el paso 5 | Active el entorno (`(venv)` visible) y repita el paso 5 |
| `ModuleNotFoundError: No module named 'src'` | La terminal no está en la carpeta del proyecto, o falta el archivo `src/__init__.py` | Repita el paso 3 y compruebe que existe la carpeta `src` con sus archivos |
| `ERROR: No se encontró el archivo ... data/raw/...` | Falta un CSV o cambió de nombre | Deje `Radiacion.csv` y `Temperatura.csv` en `data/raw/` con esos nombres exactos |
| `PermissionError` al guardar un resultado | Un archivo de `outputs/` o `data/processed/` está abierto en Excel u otro programa | Ciérrelo y vuelva a ejecutar |
| Los números no coinciden con la tabla del paso 7 | Se modificó un dato o el valor de `MIN_HORAS` en `main.py` | Vuelva a descargar el proyecto sin cambios |

### Manejo de errores y validaciones de entrada

El pipeline se detiene con un mensaje claro y código de salida 1 (nunca falla en silencio) en estos casos:

| Situación | Dónde se controla | Mensaje |
|---|---|---|
| Falta un archivo de `data/raw/` o no es un `.csv` | `extraction.py` | `No se encontró el archivo: ...` |
| El CSV está vacío o no se puede leer | `extraction.py` | `No se pudo leer ... como CSV` |
| Faltan columnas esperadas (`Fecha`, `Valor`, ...) | `extraction.py` | `faltan columnas [...]` |
| `Valor` contiene texto en vez de números | `extraction.py` | `la columna 'Valor' debe ser numérica` |
| El dataset integrado queda vacío o un control de validación da `[FALLA]` | `main.py` | `La validación del dataset integrado falló` (no se guarda el dataset) |

## 5. Diagnóstico de calidad (datos originales)

| Revisión | Radiación | Temperatura |
|---|---|---|
| Filas | 57.020 | 3.531 |
| Valores nulos | 0 | 0 |
| Filas duplicadas | 0 | 0 |
| Fechas duplicadas | 0 | 0 |
| Valores negativos | 0 | 0 |
| Tipo de la columna `Fecha` | texto | texto |
| Registros esperados en la serie continua | 86.003 (horas) | 3.584 (días) |
| Registros faltantes | 28.983 horas | 53 días |

Hallazgos principales:
- No hay nulos ni duplicados, pero **sí hay fechas faltantes**: la radiación tiene datos en 2.542 días y solo 1.469 de ellos con las 24 horas.
- La columna `Fecha` viene como texto en ambos archivos.
- **Las frecuencias no coinciden** (horaria vs diaria), lo que impide unir directamente.
- Ambos archivos tienen columnas con un único valor (estación, unidad, nivel de aprobación).

## 6. Transformaciones (con justificación)

| # | Transformación | Dónde | Justificación |
|---|---|---|---|
| 1 | Convertir `Fecha` de texto a fecha-hora | `cleaning.py` | Permite separar fecha y hora y operar con fechas |
| 2 | Renombrar columnas (`radiacion_wh_m2`, `temp_max_c`, etc.) | `cleaning.py` | Ambos archivos llaman `Valor` a la medición; evita confusión tras el merge |
| 3 | Eliminar duplicados y nulos | `cleaning.py` | Evita contar datos dos veces o con valores vacíos (en estos datos dio 0 casos) |
| 4 | Eliminar columnas constantes y guardarlas como metadatos | `cleaning.py` | No aportan información al análisis; su valor queda documentado |
| 5 | Separar fecha y hora (`fecha_dia`, `hora`) | `transformation.py` | La fecha sin hora es la clave de unión; con fecha y hora solo coincidirían las 00:00 |
| 6 | Agregar la radiación de horaria a diaria (suma y `n_horas`) | `transformation.py` | La temperatura es diaria; ambas deben estar al mismo nivel |
| 7 | Filtrar días con menos de 20 horas de radiación | `transformation.py` | Un día incompleto suma menos por datos faltantes, no por menos sol, y distorsionaría la correlación |

### Justificación del umbral de 20 horas (transformación 7)

El mínimo de horas por día (`MIN_HORAS` en `main.py`) es una decisión del equipo. Para respaldarla se ejecutó el pipeline completo con distintos valores y se comparó cuántos días quedan y cuánto da la correlación:

| Mínimo de horas | Días analizados | Pearson | Spearman |
|---|---|---|---|
| 1 (sin filtrar) | 2.504 | 0,522 | 0,541 |
| 12 | 2.430 | 0,575 | 0,563 |
| 18 | 2.304 | 0,592 | 0,576 |
| **20 (elegido)** | **2.237** | **0,600** | **0,583** |
| 22 | 2.098 | 0,608 | 0,588 |
| 24 | 1.443 | 0,607 | 0,591 |

- Sin filtrar, la correlación baja a 0,52 porque los días con pocas horas registradas suman menos radiación por datos faltantes y no por menos sol, lo que mete ruido.
- A partir de 18 horas el resultado se estabiliza alrededor de 0,6.
- Exigir 24 horas completas casi no cambia la correlación, pero descarta unos 800 días más.
- Se eligió 20 horas porque conserva una gran cantidad de días (2.237) sin cambiar la conclusión.

Cualquier persona puede reproducir esta tabla cambiando el valor de `MIN_HORAS` en `main.py` y ejecutando `python main.py`.

**Seguridad:** el repositorio no contiene claves de API, tokens ni credenciales; `.gitignore` excluye `.env` por si se agregan en el futuro. Tampoco hay rutas absolutas locales en el código.

**Conservación de los datos originales:** los archivos de `data/raw/` nunca se modifican y cada función trabaja sobre una copia del DataFrame.

## 7. Integración

- **Método:** `pandas.merge` con `how="inner"`.
- **Clave de relación:** `fecha_dia` (fecha sin hora).
- **Por qué inner:** solo sirven los días que tienen temperatura y radiación a la vez.
- **Prevención de pérdidas y duplicaciones:** se comprueba que `fecha_dia` tenga el mismo tipo en ambos lados antes del merge y, después, que el número de filas obtenido sea igual al número de días en común.

## 8. Validación y resultados

Resultados de la ejecución (ver `outputs/resultados.txt`):

| Control | Resultado |
|---|---|
| Registros del dataset integrado | 2.237 días (esperados: 2.237) |
| Fechas duplicadas | 0 |
| Nulos en radiación o temperatura | 0 |
| Rango de temperatura máxima | 22,0 a 36,0 °C |

Evolución de los registros: 57.020 horas de radiación → 2.542 días → 2.270 días con al menos 20 horas → 2.237 días en común con temperatura.

### Interpretación preliminar

- Correlación de Pearson: **0,600**. El programa la clasifica como "moderada" porque está apenas por debajo del corte de 0,6 de la regla práctica usada; en la práctica está en el límite entre una relación moderada y una fuerte.
- Correlación de Spearman: **0,583** (relación moderada, positiva).
- Regresión lineal: por cada grado más de temperatura máxima, la radiación diaria es en promedio unos **317 Wh/m²** mayor (la radiación media del periodo es de unos 4.560 Wh/m² al día).
- R² = **0,36**: la temperatura máxima está asociada con cerca del 36 % de la variación de la radiación diaria. El resto depende de otros factores.

**Respuesta a la pregunta del proyecto:** entre 2006 y 2016 existe en Ibagué una relación positiva, de moderada a fuerte, entre la temperatura máxima diaria y la radiación solar diaria: los días más calurosos tienden a ser también los de mayor radiación acumulada. Los dos coeficientes son parecidos, lo que refuerza la conclusión. Sin embargo, la relación no es perfecta (la dispersión de la gráfica es amplia): otros factores, como la nubosidad, influyen en ambas variables. Esta correlación no prueba causalidad.

## 9. Limitaciones

- Las variables vienen de dos estaciones distintas (Batallón Rooke y Aeropuerto Perales), por lo que no están medidas exactamente en el mismo punto.
- Solo hay datos en parte de los días del periodo (la radiación tiene años casi vacíos, como 2009).
- El umbral de 20 horas es una decisión del equipo; puede cambiarse en `MIN_HORAS` dentro de `main.py`. Un día con 20 horas sigue sumando algo menos radiación que uno con 24.
- Los días consecutivos no son independientes entre sí (una racha de días soleados, temporadas secas y lluviosas). Parte de la relación observada puede deberse a esa estacionalidad y no solo a la relación día a día entre las dos variables.
- La correlación y la regresión miden asociación, no causa y efecto.
