# Analizador de Incidencias Brasaland

Vamos a construir esto:

```text
CSV Brasaland
     │
     ▼
Lógica Python compartida
     │
     ├── scripts/analyze.py
     │
     └── FastAPI
            │
            ▼
          Next.js
            │
            ▼
      Panel Backoffice
```

La lógica del CSV se escribe **una sola vez**.

El script y FastAPI reutilizan exactamente las mismas funciones.

---

# PASO 1 — Crear el repositorio desde el template

Entrá al repositorio:

```text
https://github.com/4GeeksAcademy/ai-engineering-company-project-monorepo
```

GitHub indica que para crear un proyecto desde un template hay que usar `Use this template` → `Create a new repository` y después elegir el propietario.

Arriba tocá:

```text
Use this template
```

Después:

```text
Create a new repository
```

En:

```text
Owner
```

elegí:

```text
4GeeksAcademy
```

Como nombre podés poner:

```text
brasaland-incidents-analysis
```

Si ya existe, agregale algo que lo haga único:

```text
brasaland-incidents-analysis-tuusuario
```

Elegí:

```text
Public
```

y tocá:

```text
Create repository
```

---

# PASO 2 — Abrir GitHub Codespaces

Una vez creado TU repositorio, entrá en él.

Tocá:

```text
Code
```

Después la pestaña:

```text
Codespaces
```

Y:

```text
Create codespace on main
```

Ese es el flujo oficial de GitHub para abrir un Codespace desde un repositorio.

Esperá que abra VS Code en el navegador.

---

# PASO 3 — Abrir una terminal

En VS Code:

```text
Terminal
→ New Terminal
```

Comprobá dónde estás:

```bash
pwd
```

Después:

```bash
git status
```

Deberías estar dentro del repositorio recién creado.

---

# PASO 4 — Crear nuestra rama

En la terminal:

```bash
git checkout -b incidents-analysis
```

Comprobá:

```bash
git branch
```

Deberías ver:

```text
* incidents-analysis
  main
```

---

# PASO 5 — Reemplazar CONTEXT.md por Brasaland, si no lo hiciste antes! ( ojo )

El template dice explícitamente que `CONTEXT.md` es un placeholder y debe reemplazarse por el contexto de la empresa elegida.

Vamos a bajar directamente el CONTEXT oficial de Brasaland.

Terminal:

```bash
curl -L "https://raw.githubusercontent.com/4GeeksAcademy/ai-engineering-syllabus/main/content/contexts/incidents-file-analysis/CONTEXT-brasaland.es.md" -o CONTEXT.md
```

Comprobá:

```bash
head -n 5 CONTEXT.md
```

Tiene que aparecer:

```text
# CONTEXT — Utilidad de Análisis de Datos...

## Empresa: Brasaland
```

Perfecto.

---

# PASO 6 — Descargar el CSV oficial

El contexto oficial define estas columnas:

```text
incident_id
date
location_id
category
description
status
customer_id
satisfaction_score
reporter_id
```

También define las categorías, estados y reglas de validación que vamos a implementar.

Descargá el CSV directamente dentro de `scripts/`:

```bash
curl -L "https://raw.githubusercontent.com/4GeeksAcademy/ai-engineering-syllabus/main/content/contexts/incidents-file-analysis/incidents-brasaland.csv" -o scripts/incidents-brasaland.csv
```

Comprobá:

```bash
head -n 3 scripts/incidents-brasaland.csv
```

Después:

```bash
wc -l scripts/incidents-brasaland.csv
```

Tiene que dar:

```text
101
```

¿Por qué 101?

```text
1 encabezado
+
100 registros
=
101 líneas
```

El archivo real tiene justamente esas 100 filas de datos.

---

# PASO 7 — Entender qué resultado tenemos que obtener

NO vamos a escribir estos números en el código.

El programa tiene que **calcularlos**.

Después simplemente comprobamos que coincidan.

El CONTEXT oficial de Brasaland dice que el resultado correcto es:

```text
TOTAL:      100

VÁLIDOS:     96
INVÁLIDOS:    4
```

Categorías válidas:

```text
CUSTOMER_COMPLAINT    29
EQUIPMENT             17
SUPPLY                22
FOOD_QUALITY          19
STAFF                   9
```

Estados:

```text
OPEN         32
CLOSED       50
DISCARDED    14
```

Inválidos:

```text
location_id faltante             1
category faltante/inválida       1
description vacía/corta          1
CLOSED sin satisfaction_score    1
```

Satisfacción:

```text
1 → 4
2 → 6
3 → 12
4 → 19
5 → 9
```

Promedio:

```text
3.46
```

Si nuestro script no obtiene esto:

```text
NO seguimos con FastAPI.
```

Primero arreglamos Python.

---

# PASO 8 — Preparar .gitignore

El `.gitignore` del template actualmente está vacío.

Abrilo:

```text
.gitignore
```

Poné:

```gitignore
.venv/
__pycache__/
*.py[cod]
results.csv
```

Guardá.

---

# PASO 9 — Crear la estructura Python

Terminal:

```bash
mkdir -p packages/incidents_analysis
mkdir -p services/api
```

Después:

```bash
touch packages/__init__.py
touch packages/incidents_analysis/__init__.py
touch packages/incidents_analysis/analyzer.py
touch services/__init__.py
touch services/api/__init__.py
touch services/api/main.py
touch scripts/analyze.py
```

Nuestra parte nueva queda:

```text
packages/
└── incidents_analysis/
    ├── __init__.py
    └── analyzer.py

scripts/
├── analyze.py
└── incidents-brasaland.csv

services/
└── api/
    ├── __init__.py
    └── main.py
```

La lógica compartida vive en:

```text
packages/incidents_analysis/
```

Esto encaja con la estructura del monorepo, que reserva `packages/` para código reutilizado entre distintas partes del sistema.

---

# PASO 10 — Crear la lógica del analizador

Abrí:

```text
packages/incidents_analysis/analyzer.py
```

Pegá todo esto:

```python
import csv
import re

from collections import Counter
from datetime import datetime
from io import StringIO


EXPECTED_COLUMNS = [
    "incident_id",
    "date",
    "location_id",
    "category",
    "description",
    "status",
    "customer_id",
    "satisfaction_score",
    "reporter_id",
]


VALID_LOCATIONS = [
    *[
        f"COL-{number:02d}"
        for number in range(1, 11)
    ],
    *[
        f"FLA-{number:02d}"
        for number in range(1, 5)
    ],
]


VALID_CATEGORIES = [
    "CUSTOMER_COMPLAINT",
    "EQUIPMENT",
    "SUPPLY",
    "FOOD_QUALITY",
    "STAFF",
]


VALID_STATUSES = [
    "OPEN",
    "CLOSED",
    "DISCARDED",
]


ERROR_LABELS = {
    "missing_incident_id":
        "Missing incident_id",

    "invalid_incident_id":
        "Invalid incident_id format",

    "missing_date":
        "Missing date",

    "invalid_date":
        "Invalid date format",

    "invalid_location_id":
        "Missing or invalid location_id",

    "invalid_category":
        "Invalid or missing category",

    "invalid_description":
        "Empty or too-short description",

    "invalid_status":
        "Invalid or missing status",

    "missing_reporter_id":
        "Missing reporter_id",

    "invalid_reporter_id":
        "Invalid reporter_id format",

    "invalid_customer_id":
        "Invalid customer_id format",

    "closed_missing_score":
        "Closed case, no score",

    "invalid_score":
        "Invalid satisfaction_score",

    "score_out_of_range":
        "satisfaction_score out of range",
}


def clean(value):
    if value is None:
        return ""

    return str(value).strip()


def valid_date(value):
    try:
        datetime.strptime(
            value,
            "%Y-%m-%d",
        )

        return True

    except ValueError:
        return False


def validate_row(row):
    errors = []


    # incident_id

    incident_id = clean(
        row.get("incident_id")
    )

    if not incident_id:

        errors.append(
            "missing_incident_id"
        )

    elif not re.fullmatch(
        r"BRS-\d{6}",
        incident_id,
    ):

        errors.append(
            "invalid_incident_id"
        )


    # date

    date = clean(
        row.get("date")
    )

    if not date:

        errors.append(
            "missing_date"
        )

    elif not valid_date(date):

        errors.append(
            "invalid_date"
        )


    # location_id

    location_id = clean(
        row.get("location_id")
    )

    if (
        location_id
        not in VALID_LOCATIONS
    ):

        errors.append(
            "invalid_location_id"
        )


    # category

    category = clean(
        row.get("category")
    )

    if (
        category
        not in VALID_CATEGORIES
    ):

        errors.append(
            "invalid_category"
        )


    # description

    description = clean(
        row.get("description")
    )

    if len(description) < 5:

        errors.append(
            "invalid_description"
        )


    # status

    status = clean(
        row.get("status")
    )

    if (
        status
        not in VALID_STATUSES
    ):

        errors.append(
            "invalid_status"
        )


    # reporter_id

    reporter_id = clean(
        row.get("reporter_id")
    )

    if not reporter_id:

        errors.append(
            "missing_reporter_id"
        )

    elif not re.fullmatch(
        r"MGR-\d{2}",
        reporter_id,
    ):

        errors.append(
            "invalid_reporter_id"
        )


    # customer_id
    # Es opcional.
    # Pero si viene informado,
    # verificamos su formato.

    customer_id = clean(
        row.get("customer_id")
    )

    if (
        customer_id
        and not re.fullmatch(
            r"CLI-\d{6}",
            customer_id,
        )
    ):

        errors.append(
            "invalid_customer_id"
        )


    # satisfaction_score

    score_text = clean(
        row.get(
            "satisfaction_score"
        )
    )


    # CLOSED necesita puntaje.

    if (
        status == "CLOSED"
        and not score_text
    ):

        errors.append(
            "closed_missing_score"
        )


    # Si hay puntaje,
    # debe ser entero entre 1 y 5.

    if score_text:

        try:
            score = int(
                score_text
            )

        except ValueError:

            errors.append(
                "invalid_score"
            )

        else:

            if not 1 <= score <= 5:

                errors.append(
                    "score_out_of_range"
                )


    return errors


def build_breakdown(
    counter,
    possible_values,
    total,
):

    breakdown = {}


    for value in possible_values:

        count = counter.get(
            value,
            0,
        )


        if total:

            percentage = round(
                (
                    count
                    / total
                )
                * 100,
                1,
            )

        else:

            percentage = 0.0


        breakdown[value] = {
            "count": count,
            "percentage": percentage,
        }


    return breakdown


def analyze_csv_text(
    text,
    source_file=(
        "incidents-brasaland.csv"
    ),
):

    if (
        not text
        or not text.strip()
    ):

        raise ValueError(
            "El fichero CSV está vacío"
        )


    try:

        reader = csv.DictReader(
            StringIO(text),
            strict=True,
        )


        if not reader.fieldnames:

            raise ValueError(
                "El CSV no contiene "
                "encabezados"
            )


        missing_columns = [
            column
            for column
            in EXPECTED_COLUMNS

            if column
            not in reader.fieldnames
        ]


        if missing_columns:

            raise ValueError(
                "Faltan columnas "
                "obligatorias: "
                + ", ".join(
                    missing_columns
                )
            )


        rows = list(
            reader
        )


    except csv.Error as error:

        raise ValueError(
            "El fichero no contiene "
            "un CSV válido"
        ) from error


    if not rows:

        raise ValueError(
            "El CSV no contiene registros"
        )


    valid_rows = []

    invalid_reason_counts = (
        Counter()
    )

    invalid_records = 0


    for row in rows:

        problems = validate_row(
            row
        )


        if problems:

            invalid_records += 1

            invalid_reason_counts.update(
                problems
            )


        else:

            valid_rows.append(
                row
            )


    valid_records = len(
        valid_rows
    )


    # Categorías

    category_counts = Counter(

        clean(
            row.get("category")
        )

        for row in valid_rows
    )


    # Estados

    status_counts = Counter(

        clean(
            row.get("status")
        )

        for row in valid_rows
    )


    # Casos CLOSED válidos

    closed_rows = [

        row

        for row in valid_rows

        if clean(
            row.get("status")
        ) == "CLOSED"

    ]


    # Los CLOSED válidos
    # siempre tienen score válido.

    scores = [

        int(
            clean(
                row.get(
                    "satisfaction_score"
                )
            )
        )

        for row in closed_rows

    ]


    score_counts = Counter(
        scores
    )


    if scores:

        average_score = round(
            sum(scores)
            / len(scores),
            2,
        )

    else:

        average_score = None


    invalid_breakdown = {

        ERROR_LABELS.get(
            code,
            code,
        ): count

        for code, count
        in invalid_reason_counts.items()

    }


    return {

        "company":
            "BRASALAND",

        "source_file":
            source_file,

        "total_records":
            len(rows),

        "valid_records":
            valid_records,

        "invalid_records":
            invalid_records,

        "invalid_breakdown":
            invalid_breakdown,

        "by_category":
            build_breakdown(
                category_counts,
                VALID_CATEGORIES,
                valid_records,
            ),

        "by_status":
            build_breakdown(
                status_counts,
                VALID_STATUSES,
                valid_records,
            ),

        "satisfaction": {

            "closed_cases":
                len(closed_rows),

            "scored_cases":
                len(scores),

            "average":
                average_score,

            "scores": {

                str(score):
                    score_counts.get(
                        score,
                        0,
                    )

                for score
                in range(1, 6)

            },
        },
    }


def format_summary(
    summary
):

    lines = [

        "=" * 60,

        (
            "  BRASALAND — "
            "INCIDENT REPORT ANALYSIS"
        ),

        (
            "  Source file: "
            f"{summary['source_file']}"
        ),

        "=" * 60,

        "",

        (
            "TOTAL RECORDS IN FILE "
            ".......... "
            f"{summary['total_records']}"
        ),

        (
            "  Valid records "
            "................ "
            f"{summary['valid_records']}"
        ),

        (
            "  Invalid / incomplete "
            "......... "
            f"{summary['invalid_records']}"
        ),

        "",

        "INVALID RECORDS BREAKDOWN",

    ]


    if summary[
        "invalid_breakdown"
    ]:

        for reason, count in (
            summary[
                "invalid_breakdown"
            ].items()
        ):

            lines.append(
                f"  {reason:<42} "
                f"{count}"
            )

    else:

        lines.append(
            "  No invalid records"
        )


    lines.extend([
        "",
        (
            "BREAKDOWN BY CATEGORY "
            "(valid records)"
        ),
    ])


    for category, data in (
        summary[
            "by_category"
        ].items()
    ):

        lines.append(

            f"  {category:<28} "

            f"{data['count']:>3}  "

            f"("
            f"{data['percentage']:.1f}"
            f"%)"

        )


    lines.extend([
        "",
        (
            "BREAKDOWN BY STATUS "
            "(valid records)"
        ),
    ])


    for status, data in (
        summary[
            "by_status"
        ].items()
    ):

        lines.append(

            f"  {status:<28} "

            f"{data['count']:>3}  "

            f"("
            f"{data['percentage']:.1f}"
            f"%)"

        )


    satisfaction = (
        summary[
            "satisfaction"
        ]
    )


    lines.extend([

        "",

        (
            "SATISFACTION INDEX "
            "(closed cases)"
        ),

        (
            "  Scored cases: "
            f"{satisfaction['scored_cases']} "
            "of "
            f"{satisfaction['closed_cases']}"
        ),

    ])


    if (
        satisfaction[
            "average"
        ] is None
    ):

        lines.append(
            "  Average score: N/A"
        )

    else:

        lines.append(

            "  Average score: "

            f"{satisfaction['average']:.2f}"

            " / 5.00"

        )


    score_labels = {

        "1":
            "Very dissatisfied",

        "2":
            "Dissatisfied",

        "3":
            "Neutral",

        "4":
            "Satisfied",

        "5":
            "Very satisfied",

    }


    for score, count in (
        satisfaction[
            "scores"
        ].items()
    ):

        label = (
            score_labels[
                score
            ]
        )

        lines.append(

            f"  Score {score} "

            f"({label}) "

            f"........ {count}"

        )


    lines.extend([
        "",
        "=" * 60,
    ])


    return "\n".join(
        lines
    )


def summary_to_csv(
    summary
):

    output = StringIO()

    writer = csv.writer(
        output
    )


    writer.writerow([
        "metric",
        "value",
        "percentage",
    ])


    writer.writerow([
        "total_records",
        summary[
            "total_records"
        ],
        "",
    ])


    writer.writerow([
        "valid_records",
        summary[
            "valid_records"
        ],
        "",
    ])


    writer.writerow([
        "invalid_records",
        summary[
            "invalid_records"
        ],
        "",
    ])


    for reason, count in (
        summary[
            "invalid_breakdown"
        ].items()
    ):

        writer.writerow([
            f"invalid.{reason}",
            count,
            "",
        ])


    for category, data in (
        summary[
            "by_category"
        ].items()
    ):

        writer.writerow([

            f"category.{category}",

            data[
                "count"
            ],

            data[
                "percentage"
            ],

        ])


    for status, data in (
        summary[
            "by_status"
        ].items()
    ):

        writer.writerow([

            f"status.{status}",

            data[
                "count"
            ],

            data[
                "percentage"
            ],

        ])


    satisfaction = (
        summary[
            "satisfaction"
        ]
    )


    writer.writerow([

        "satisfaction.closed_cases",

        satisfaction[
            "closed_cases"
        ],

        "",

    ])


    writer.writerow([

        "satisfaction.scored_cases",

        satisfaction[
            "scored_cases"
        ],

        "",

    ])


    writer.writerow([

        "satisfaction.average",

        satisfaction[
            "average"
        ],

        "",

    ])


    for score, count in (
        satisfaction[
            "scores"
        ].items()
    ):

        writer.writerow([

            (
                "satisfaction."
                f"score_{score}"
            ),

            count,

            "",

        ])


    return output.getvalue()
```

Guardá.

---

# PASO 11 — Exportar las funciones del paquete

Abrí:

```text
packages/incidents_analysis/__init__.py
```

Pegá:

```python
from .analyzer import (
    analyze_csv_text,
    format_summary,
    summary_to_csv,
)
```

Guardá.

---

# PASO 12 — Crear el script analyze.py

Abrí:

```text
scripts/analyze.py
```

Pegá:

```python
import argparse
import sys

from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


sys.path.insert(
    0,
    str(ROOT),
)


from packages.incidents_analysis import (
    analyze_csv_text,
    format_summary,
    summary_to_csv,
)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Analiza el CSV de "
            "incidencias de Brasaland."
        )
    )


    parser.add_argument(
        "csv_file",
        help=(
            "Ruta al fichero CSV "
            "que se quiere analizar."
        ),
    )


    args = parser.parse_args()

    csv_path = Path(
        args.csv_file
    )


    if not csv_path.exists():

        print(
            "Error: no existe "
            f"el fichero {csv_path}"
        )

        sys.exit(1)


    try:

        text = (
            csv_path.read_text(
                encoding="utf-8-sig"
            )
        )


        summary = (
            analyze_csv_text(
                text=text,
                source_file=(
                    csv_path.name
                ),
            )
        )


    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
    ) as error:

        print(
            f"Error: {error}"
        )

        sys.exit(1)


    print()

    print(
        format_summary(
            summary
        )
    )

    print()


    answer = input(
        "¿Deseas exportar "
        "los resultados a CSV? "
        "[s / n]: "
    ).strip().lower()


    if answer in {
        "s",
        "si",
        "sí",
        "y",
        "yes",
    }:

        result_path = Path(
            "results.csv"
        )


        result_path.write_text(

            summary_to_csv(
                summary
            ),

            encoding="utf-8",

        )


        print(
            "Resultados guardados en "
            f"{result_path.resolve()}"
        )


    else:

        print(
            "Resultados no exportados."
        )


if __name__ == "__main__":
    main()
```

Guardá.

---

# PASO 13 — Ejecutar por primera vez

Desde la raíz del repositorio:

```bash
python scripts/analyze.py scripts/incidents-brasaland.csv
```

El programa debería terminar mostrando:

```text
TOTAL RECORDS IN FILE .......... 100

Valid records ................ 96
Invalid / incomplete ......... 4
```

Las categorías tienen que ser:

```text
CUSTOMER_COMPLAINT    29
EQUIPMENT             17
SUPPLY                22
FOOD_QUALITY          19
STAFF                   9
```

Estados:

```text
OPEN         32
CLOSED       50
DISCARDED    14
```

Promedio:

```text
3.46
```

Estos son exactamente los valores definidos por Brasaland.

Cuando pregunte:

```text
¿Deseas exportar los resultados a CSV? [s / n]:
```

por ahora escribí:

```text
n
```

---

# PASO 14 — Si los números coinciden

Si obtenemos:

```text
100
96
4
3.46
```

seguimos.

Si no:

```text
NO avanzar.
```

Algo quedó mal copiado.

FastAPI todavía no tiene nada que ver.

---

# PASO 15 — Probar la exportación del script

Ejecutá nuevamente:

```bash
python scripts/analyze.py scripts/incidents-brasaland.csv
```

Esta vez respondé:

```text
s
```

Comprobá:

```bash
cat results.csv
```

Arriba tiene que aparecer:

```text
metric,value,percentage
total_records,100,
valid_records,96,
invalid_records,4,
```

Después aparecen las métricas por:

```text
invalid
category
status
satisfaction
```

Con esto queda terminada la Fase 1.

---

# PASO 16 — Crear virtualenv para FastAPI

Desde la raíz:

```bash
python -m venv .venv
```

Activarlo:

```bash
source .venv/bin/activate
```

Cuando esté activo deberías ver algo parecido a:

```text
(.venv)
```

al principio de la terminal.

---

# PASO 17 — Crear requirements.txt

Abrí:

```text
services/api/requirements.txt
```

Si no existe, crealo.

Poné:

```text
fastapi
uvicorn[standard]
python-multipart
```

Guardá.

Instalá:

```bash
python -m pip install -r services/api/requirements.txt
```

FastAPI necesita `python-multipart` para recibir archivos enviados mediante formularios, ya que las cargas de archivos llegan como `multipart/form-data`.

---

# PASO 18 — Crear FastAPI

Abrí:

```text
services/api/main.py
```

Pegá:

```python
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from fastapi.responses import (
    Response,
)


from packages.incidents_analysis import (
    analyze_csv_text,
    summary_to_csv,
)


app = FastAPI(
    title=(
        "Brasaland Incidents API"
    ),
    version="1.0.0",
)


LAST_ANALYSIS = None


@app.get("/")
def root():

    return {
        "message":
            (
                "Brasaland Incidents "
                "API is running"
            )
    }


@app.post(
    "/api/incidents/analyze"
)
async def analyze_incidents(
    file: UploadFile = File(...)
):

    global LAST_ANALYSIS


    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail=(
                "El fichero "
                "no tiene nombre."
            ),
        )


    if not (
        file.filename
        .lower()
        .endswith(".csv")
    ):

        raise HTTPException(
            status_code=415,
            detail=(
                "El fichero debe "
                "tener extensión .csv."
            ),
        )


    content = await file.read()


    if not content:

        raise HTTPException(
            status_code=400,
            detail=(
                "El fichero está vacío."
            ),
        )


    try:

        text = content.decode(
            "utf-8-sig"
        )


    except UnicodeDecodeError as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "El fichero debe "
                "utilizar codificación "
                "UTF-8."
            ),
        ) from error


    try:

        result = analyze_csv_text(
            text=text,
            source_file=file.filename,
        )


    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


    LAST_ANALYSIS = result


    return result


@app.get(
    "/api/incidents/results/export"
)
def export_results():

    if LAST_ANALYSIS is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Todavía no existe "
                "ningún análisis "
                "para exportar."
            ),
        )


    csv_content = (
        summary_to_csv(
            LAST_ANALYSIS
        )
    )


    return Response(
        content=csv_content,

        media_type="text/csv",

        headers={
            "Content-Disposition":
                (
                    "attachment; "
                    'filename="results.csv"'
                )
        },
    )
```

Guardá.

---

# PASO 19 — Levantar FastAPI

Desde la raíz y con `.venv` activo:

```bash
python -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Tiene que aparecer algo similar a:

```text
Uvicorn running on http://0.0.0.0:8000
```

DEJÁ ESA TERMINAL ABIERTA.

FastAPI está corriendo ahí.

---

# PASO 20 — Probar FastAPI desde otra terminal

Abrí:

```text
Terminal
→ New Terminal
```

No hace falta activar el virtualenv para usar `curl`.

Ejecutá:

```bash
curl -s -F "file=@scripts/incidents-brasaland.csv" http://127.0.0.1:8000/api/incidents/analyze | python -m json.tool
```

Tiene que devolver un JSON.

Arriba deberías encontrar:

```json
{
    "company": "BRASALAND",
    "source_file": "incidents-brasaland.csv",
    "total_records": 100,
    "valid_records": 96,
    "invalid_records": 4
}
```

Además aparecerán:

```text
invalid_breakdown
by_category
by_status
satisfaction
```

---

# PASO 21 — Probar exportación desde FastAPI

Después del POST anterior:

```bash
curl http://127.0.0.1:8000/api/incidents/results/export -o /tmp/results-api.csv
```


Backend listo.

---

# PASO 22 — Abrir Swagger

El devcontainer del template ya tiene previstos los puertos `3000` y `8000` para forwarding en Codespaces.

Abajo en VS Code buscá la pestaña:

```text
PORTS
```

Debería aparecer:

```text
8000
```

Hacé clic derecho:

```text
Open in Browser
```

En la URL que abra agregá:

```text
/docs
```

Ahí vas a ver Swagger.

Podés probar SI QUERES ( descargando previamente el csv para tenerlo a mano )
https://[raw.githubusercontent.com/4GeeksAcademy/ai-engineering-syllabus/main/content/contexts/incidents-file-analysis/incidents-brasaland.csv&#34;](https://raw.githubusercontent.com/4GeeksAcademy/ai-engineering-syllabus/main/content/contexts/incidents-file-analysis/incidents-brasaland.csv) :

```text
POST /api/incidents/analyze
```

y:

```text
GET /api/incidents/results/export
```

---

# PASO 23 — Crear Next.js

DEJÁ FastAPI funcionando.

Abrí otra terminal.

Desde la raíz:

```bash
npx create-next-app@latest uis/backoffice --ts --eslint --app --src-dir --use-npm --yes
```

`create-next-app` soporta TypeScript, App Router y estructura `src/` directamente desde su CLI.

Esperá que termine.

La estructura será aproximadamente:

```text
uis/
└── backoffice/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.ts
    └── src/
        └── app/
            ├── layout.tsx
            ├── page.tsx
            └── globals.css
```

---

# PASO 24 — Hacer que Next se comunique con FastAPI en Codespaces

Podríamos andar jugando con URLs externas de Codespaces, CORS, puertos públicos y otros entretenimientos diseñados para quitarnos años de vida.

No.

Next tiene `rewrites`, que funcionan como proxy de URLs.

El navegador le hablará a Next.

Next internamente le hablará a:

```text
127.0.0.1:8000
```

Como ambos procesos están dentro del mismo Codespace, funciona perfecto.

Abrí:

```text
uis/backoffice/next.config.ts
```

Reemplazá todo por:

```tsx
import type {
  NextConfig
} from "next";


const nextConfig: NextConfig = {

  async rewrites() {

    return [

      {
        source:
          "/backend/:path*",

        destination:
          (
            "http://127.0.0.1:"
            + "8000/:path*"
          ),
      },

    ];

  },

};


export default nextConfig;
```

Guardá.

Nuestro navegador llamará:

```text
/backend/api/incidents/analyze
```

Next lo transformará internamente en:

```text
http://127.0.0.1:8000/api/incidents/analyze
```

Así no necesitamos CORS ni URLs rarísimas de Codespaces.

---

# PASO 25 — Crear el layout

Abrí:

```text
uis/backoffice/src/app/layout.tsx
```

Borrá todo.

Pegá:

```tsx
import type {
  Metadata
} from "next";


import Link from "next/link";

import "./globals.css";


export const metadata: Metadata = {

  title:
    "Brasaland Backoffice",

  description:
    (
      "Panel interno "
      + "de Brasaland"
    ),

};


export default function RootLayout({

  children,

}: Readonly<{

  children:
    React.ReactNode;

}>) {

  return (

    <html lang="es">

      <body>

        <nav className="navbar">

          <div className="navContent">

            <Link
              href="/"
              className="logo"
            >
              BRASALAND
            </Link>


            <div className="navLinks">

              <Link href="/">
                Inicio
              </Link>

              <Link href="/incidents">
                Incidencias
              </Link>

            </div>

          </div>

        </nav>


        {children}

      </body>

    </html>

  );

}
```

---

# PASO 26 — Crear la home

Abrí:

```text
uis/backoffice/src/app/page.tsx
```

Borrá todo.

Pegá:

```tsx
import Link from "next/link";


export default function Home() {

  return (

    <main className="container">

      <section className="hero">

        <span className="eyebrow">
          BRASALAND DIGITAL
        </span>


        <h1>
          Backoffice operativo
        </h1>


        <p>
          Herramientas internas
          para gestión y análisis
          de operaciones.
        </p>


        <Link
          href="/incidents"
          className="button"
        >
          Analizar incidencias
        </Link>

      </section>

    </main>

  );

}
```

---

# PASO 27 — Crear la página de incidencias

Terminal:

```bash
mkdir -p uis/backoffice/src/app/incidents
```

Después creá:

```text
uis/backoffice/src/app/incidents/page.tsx
```

Pegá:

```tsx
"use client";


import {
  useState
} from "react";


import type {
  FormEvent
} from "react";


type BreakdownValue = {

  count: number;

  percentage: number;

};


type Satisfaction = {

  closed_cases: number;

  scored_cases: number;

  average:
    number | null;

  scores:
    Record<
      string,
      number
    >;

};


type AnalysisResult = {

  company: string;

  source_file: string;

  total_records: number;

  valid_records: number;

  invalid_records: number;

  invalid_breakdown:
    Record<
      string,
      number
    >;

  by_category:
    Record<
      string,
      BreakdownValue
    >;

  by_status:
    Record<
      string,
      BreakdownValue
    >;

  satisfaction:
    Satisfaction;

};


export default function IncidentsPage() {


  const [
    file,
    setFile,
  ] = useState<
    File | null
  >(null);


  const [
    result,
    setResult,
  ] = useState<
    AnalysisResult | null
  >(null);


  const [
    error,
    setError,
  ] = useState("");


  const [
    loading,
    setLoading,
  ] = useState(false);


  async function handleSubmit(

    event:
      FormEvent<HTMLFormElement>

  ) {

    event.preventDefault();


    if (!file) {

      setError(
        "Seleccioná un archivo CSV."
      );

      return;

    }


    setLoading(true);

    setError("");

    setResult(null);


    const formData =
      new FormData();


    formData.append(
      "file",
      file
    );


    try {

      const response =
        await fetch(

          (
            "/backend"
            + "/api/incidents/analyze"
          ),

          {
            method:
              "POST",

            body:
              formData,
          }

        );


      const data =
        await response
          .json()
          .catch(
            () => null
          );


      if (!response.ok) {

        throw new Error(

          data?.detail
          ??
          (
            "No fue posible "
            + "analizar el CSV."
          )

        );

      }


      setResult(
        data as AnalysisResult
      );


    } catch (error) {


      if (
        error
        instanceof Error
      ) {

        setError(
          error.message
        );

      } else {

        setError(
          "Ocurrió un error inesperado."
        );

      }


    } finally {

      setLoading(false);

    }

  }


  async function downloadResults() {


    setError("");


    try {

      const response =
        await fetch(
          (
            "/backend"
            + "/api/incidents/"
            + "results/export"
          )
        );


      if (!response.ok) {

        throw new Error(
          (
            "No fue posible "
            + "descargar "
            + "los resultados."
          )
        );

      }


      const blob =
        await response.blob();


      const url =
        URL.createObjectURL(
          blob
        );


      const link =
        document.createElement(
          "a"
        );


      link.href =
        url;


      link.download =
        "results.csv";


      document.body
        .appendChild(
          link
        );


      link.click();

      link.remove();


      URL.revokeObjectURL(
        url
      );


    } catch (error) {


      if (
        error
        instanceof Error
      ) {

        setError(
          error.message
        );

      }

    }

  }


  return (

    <main className="container">


      <header className="pageHeader">

        <span className="eyebrow">
          OPERACIONES
        </span>


        <h1>
          Análisis de incidencias
        </h1>


        <p>
          Cargá el archivo CSV
          para validar registros
          y consultar sus métricas.
        </p>

      </header>


      <section className="card">


        <form
          onSubmit={handleSubmit}
          className="uploadForm"
        >


          <div className="fileArea">

            <label htmlFor="csvFile">

              Archivo CSV

            </label>


            <input

              id="csvFile"

              type="file"

              accept=".csv,text/csv"

              onChange={(
                event
              ) => {

                const selected =
                  event
                    .target
                    .files?.[0]
                  ?? null;


                setFile(
                  selected
                );

              }}

            />


            {
              file
              && (

                <small>

                  Seleccionado:
                  {" "}
                  {file.name}

                </small>

              )
            }

          </div>


          <button
            type="submit"
            disabled={loading}
          >

            {
              loading
              ? "Analizando..."
              : "Analizar CSV"
            }

          </button>


        </form>


        {
          error
          && (

            <div className="error">

              {error}

            </div>

          )
        }


      </section>


      {
        result
        && (

          <>


            <section className="metrics">


              <article className="metric">

                <span>
                  Total
                </span>

                <strong>
                  {
                    result
                      .total_records
                  }
                </strong>

              </article>


              <article className="metric">

                <span>
                  Válidos
                </span>

                <strong>
                  {
                    result
                      .valid_records
                  }
                </strong>

              </article>


              <article className="metric">

                <span>
                  Inválidos
                </span>

                <strong>
                  {
                    result
                      .invalid_records
                  }
                </strong>

              </article>


              <article className="metric">

                <span>
                  Satisfacción
                </span>

                <strong>

                  {
                    result
                      .satisfaction
                      .average
                      ?.toFixed(2)
                    ?? "N/A"
                  }

                </strong>

              </article>


            </section>


            <section className="card">


              <h2>
                Registros inválidos
              </h2>


              {
                Object.keys(
                  result
                    .invalid_breakdown
                ).length === 0

                ? (

                  <p>
                    No hay registros
                    inválidos.
                  </p>

                )

                : (

                  <ul className="dataList">


                    {
                      Object.entries(

                        result
                          .invalid_breakdown

                      ).map(
                        ([
                          reason,
                          count,
                        ]) => (

                          <li key={reason}>

                            <span>
                              {reason}
                            </span>

                            <strong>
                              {count}
                            </strong>

                          </li>

                        )
                      )
                    }


                  </ul>

                )
              }


            </section>


            <section className="twoColumns">


              <article className="card">


                <h2>
                  Categorías
                </h2>


                <ul className="dataList">


                  {
                    Object.entries(

                      result
                        .by_category

                    ).map(
                      ([
                        category,
                        data,
                      ]) => (

                        <li key={category}>

                          <span>
                            {category}
                          </span>

                          <strong>

                            {data.count}

                            {" "}

                            (
                            {
                              data
                                .percentage
                                .toFixed(1)
                            }
                            %)

                          </strong>

                        </li>

                      )
                    )
                  }


                </ul>


              </article>


              <article className="card">


                <h2>
                  Estados
                </h2>


                <ul className="dataList">


                  {
                    Object.entries(

                      result
                        .by_status

                    ).map(
                      ([
                        status,
                        data,
                      ]) => (

                        <li key={status}>

                          <span>
                            {status}
                          </span>

                          <strong>

                            {data.count}

                            {" "}

                            (
                            {
                              data
                                .percentage
                                .toFixed(1)
                            }
                            %)

                          </strong>

                        </li>

                      )
                    )
                  }


                </ul>


              </article>


            </section>


            <section className="card">


              <h2>
                Índice de satisfacción
              </h2>


              <div className="satisfactionGrid">


                <div>

                  <span>
                    Casos cerrados
                  </span>

                  <strong>
                    {
                      result
                        .satisfaction
                        .closed_cases
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Casos puntuados
                  </span>

                  <strong>
                    {
                      result
                        .satisfaction
                        .scored_cases
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Promedio
                  </span>

                  <strong>

                    {
                      result
                        .satisfaction
                        .average
                        ?.toFixed(2)
                      ?? "N/A"
                    }

                  </strong>

                </div>


              </div>


              <h3>
                Distribución de puntajes
              </h3>


              <ul className="dataList">


                {
                  Object.entries(

                    result
                      .satisfaction
                      .scores

                  ).map(
                    ([
                      score,
                      count,
                    ]) => (

                      <li key={score}>

                        <span>
                          Puntaje {score}
                        </span>

                        <strong>
                          {count}
                        </strong>

                      </li>

                    )
                  )
                }


              </ul>


              <button
                type="button"
                onClick={
                  downloadResults
                }
                className="downloadButton"
              >

                Descargar resultados CSV

              </button>


            </section>


          </>

        )
      }


    </main>

  );

}
```

Ese es prácticamente todo el TypeScript.

Lo principal es:

```tsx
File | null
```

y:

```tsx
type AnalysisResult = {
   ...
}
```

No necesitamos transformar la clase en una competencia internacional de tipos genéricos.

---

# PASO 28 — Crear los estilos

Abrí:

```text
uis/backoffice/src/app/globals.css
```

Borrá todo.

Pegá:

```css
* {
  box-sizing: border-box;
}


html,
body {
  margin: 0;
  padding: 0;
}


body {
  font-family:
    Arial,
    Helvetica,
    sans-serif;

  background:
    #f4f5f7;

  color:
    #1c2128;
}


a {
  color: inherit;

  text-decoration: none;
}


button,
input {
  font: inherit;
}


.navbar {
  background:
    #181b20;

  color:
    white;
}


.navContent {
  width:
    min(
      1100px,
      92%
    );

  height:
    68px;

  margin:
    auto;

  display:
    flex;

  align-items:
    center;

  justify-content:
    space-between;
}


.logo {
  font-weight:
    800;

  letter-spacing:
    1.5px;
}


.navLinks {
  display:
    flex;

  gap:
    24px;
}


.navLinks a {
  opacity:
    0.75;
}


.navLinks a:hover {
  opacity:
    1;
}


.container {
  width:
    min(
      1100px,
      92%
    );

  margin:
    48px auto;
}


.hero {
  padding:
    70px 0;
}


.hero h1,
.pageHeader h1 {
  margin:
    8px 0 12px;

  font-size:
    42px;
}


.hero p,
.pageHeader p {
  color:
    #656d76;

  line-height:
    1.6;
}


.eyebrow {
  font-size:
    12px;

  letter-spacing:
    2px;

  font-weight:
    800;

  color:
    #777f89;
}


.button,
button {
  display:
    inline-block;

  border:
    0;

  border-radius:
    8px;

  background:
    #1f2328;

  color:
    white;

  padding:
    12px 18px;

  font-weight:
    700;

  cursor:
    pointer;
}


.button {
  margin-top:
    16px;
}


button:disabled {
  opacity:
    0.55;

  cursor:
    default;
}


.card {
  background:
    white;

  border:
    1px solid #e5e7eb;

  border-radius:
    14px;

  padding:
    24px;

  margin-bottom:
    20px;

  box-shadow:
    0 5px 20px
    rgba(
      0,
      0,
      0,
      0.04
    );
}


.card h2 {
  margin-top:
    0;
}


.uploadForm {
  display:
    flex;

  align-items:
    flex-end;

  justify-content:
    space-between;

  gap:
    20px;

  flex-wrap:
    wrap;
}


.fileArea {
  display:
    flex;

  flex-direction:
    column;

  gap:
    10px;
}


.fileArea label {
  font-weight:
    700;
}


.fileArea small {
  color:
    #656d76;
}


.error {
  margin-top:
    20px;

  padding:
    14px;

  border-radius:
    8px;

  background:
    #feecec;

  color:
    #a12020;
}


.metrics {
  display:
    grid;

  grid-template-columns:
    repeat(
      4,
      1fr
    );

  gap:
    16px;

  margin-bottom:
    20px;
}


.metric {
  padding:
    22px;

  border-radius:
    14px;

  background:
    white;

  border:
    1px solid #e5e7eb;

  box-shadow:
    0 5px 20px
    rgba(
      0,
      0,
      0,
      0.04
    );
}


.metric span {
  display:
    block;

  margin-bottom:
    10px;

  color:
    #656d76;
}


.metric strong {
  font-size:
    30px;
}


.twoColumns {
  display:
    grid;

  grid-template-columns:
    1fr 1fr;

  gap:
    20px;
}


.dataList {
  list-style:
    none;

  padding:
    0;

  margin:
    0;
}


.dataList li {
  display:
    flex;

  justify-content:
    space-between;

  gap:
    20px;

  padding:
    11px 0;

  border-bottom:
    1px solid #edf0f2;
}


.satisfactionGrid {
  display:
    grid;

  grid-template-columns:
    repeat(
      3,
      1fr
    );

  gap:
    16px;

  margin:
    20px 0 28px;
}


.satisfactionGrid div {
  padding:
    16px;

  background:
    #f6f7f8;

  border-radius:
    10px;
}


.satisfactionGrid span {
  display:
    block;

  color:
    #656d76;

  margin-bottom:
    7px;
}


.satisfactionGrid strong {
  font-size:
    22px;
}


.downloadButton {
  margin-top:
    24px;
}


@media (
  max-width: 750px
) {

  .metrics {
    grid-template-columns:
      1fr 1fr;
  }


  .twoColumns {
    grid-template-columns:
      1fr;
  }


  .satisfactionGrid {
    grid-template-columns:
      1fr;
  }


  .navContent {
    height:
      auto;

    padding:
      18px 0;

    flex-direction:
      column;

    gap:
      14px;
  }


  .hero h1,
  .pageHeader h1 {
    font-size:
      34px;
  }

}
```

Guardá.

---

# PASO 29 — Levantar Next

Tenemos que tener FastAPI todavía encendido en la otra terminal.

En una terminal nueva:

```bash
cd uis/backoffice
```

Después:

```bash
npm run dev -- --hostname 0.0.0.0
```

Debería aparecer:

```text
Local: http://localhost:3000
```

---

# PASO 30 — Abrir Next en Codespaces

Abajo abrí:

```text
PORTS
```

Buscá:

```text
3000
```

Hacé:

```text
Open in Browser
```

Te abre nuestra aplicación.

No escribas manualmente una URL externa.

Usá la que Codespaces te abre.

---

# PASO 31 — Entrar al analizador

En la home tocá:

```text
Analizar incidencias
```

O el menú:

```text
Incidencias
```

Vas a entrar a:

```text
/incidents
```

---

# PASO 32 — Probar todo desde el navegador

Tocá:

```text
Seleccionar archivo
```

Elegí:

```text
scripts/incidents-brasaland.csv
```

Obviamente el navegador te va a mostrar el selector de archivos de tu computadora, así que si Codespaces está remoto y el archivo no está local, descargá primero el CSV a tu PC desde GitHub.

Una alternativa más fácil para la captura final es descargar desde GitHub el archivo:

```text
incidents-brasaland.csv
```

y luego seleccionarlo.

Tocá:

```text
Analizar CSV
```

Tiene que aparecer:

```text
Total
100
```

```text
Válidos
96
```

```text
Inválidos
4
```

```text
Satisfacción
3.46
```

---

# PASO 33 — Revisar categorías

Tiene que mostrar:

```text
CUSTOMER_COMPLAINT    29
EQUIPMENT             17
SUPPLY                22
FOOD_QUALITY          19
STAFF                   9
```

---

# PASO 34 — Revisar estados

Tiene que mostrar:

```text
OPEN         32
CLOSED       50
DISCARDED    14
```

---

# PASO 35 — Revisar inválidos

Tiene que informar cuatro registros inválidos.

Uno de cada tipo:

```text
Missing or invalid location_id    1

Invalid or missing category       1

Empty or too-short description    1

Closed case, no score             1
```

---

# PASO 36 — Revisar satisfacción

Tiene que mostrar:

```text
Casos cerrados: 50

Casos puntuados: 50

Promedio: 3.46
```

Distribución:

```text
Puntaje 1 → 4
Puntaje 2 → 6
Puntaje 3 → 12
Puntaje 4 → 19
Puntaje 5 → 9
```

---

# PASO 37 — Probar descarga

Tocá:

```text
Descargar resultados CSV
```

Debe descargarse:

```text
results.csv
```

Con esto tenemos funcionando:

```text
Next
 ↓
FastAPI
 ↓
analyzer.py
 ↓
CSV
```

---

# PASO 38 — Entender qué está pasando

Cuando seleccionamos un archivo en React tenemos:

```tsx
File | null
```

Después creamos:

```tsx
const formData =
  new FormData();
```

Agregamos el archivo:

```tsx
formData.append(
  "file",
  file
);
```

Next manda:

```text
multipart/form-data
```

a:

```text
/backend/api/incidents/analyze
```

El `rewrite` de Next lo manda internamente a:

```text
127.0.0.1:8000
/api/incidents/analyze
```

FastAPI recibe:

```python
file: UploadFile
```

Lee sus bytes:

```python
content =
    await file.read()
```

Los transforma a texto:

```python
text =
    content.decode(
        "utf-8-sig"
    )
```

Y llama:

```python
analyze_csv_text(
    text
)
```

---

# PASO 39 — Lo más importante de toda la arquitectura

Tenemos:

```text
                 CSV
                  │
                  ▼
 packages/incidents_analysis/
           analyzer.py
                  │
                  │
        analyze_csv_text()
          /             \
         /               \
        ▼                 ▼
scripts/analyze.py      FastAPI
                          │
                          ▼
                       Next.js
```

No tenemos:

```text
validación del script
+
otra validación para FastAPI
```

Tenemos UNA SOLA:

```python
analyze_csv_text()
```

Esto cumple el requisito transversal de la consigna.

---

# PASO 40 — Probar errores HTTP

Con FastAPI encendido, abrí otra terminal.

## Archivo vacío

```bash
touch /tmp/empty.csv
```

Después:

```bash
curl -i -F "file=@/tmp/empty.csv" http://127.0.0.1:8000/api/incidents/analyze
```

Debe devolver:

```text
400
```

---

## Archivo que no sea CSV

```bash
echo "hola" > /tmp/test.txt
```

Después:

```bash
curl -i -F "file=@/tmp/test.txt" http://127.0.0.1:8000/api/incidents/analyze
```

Debe devolver:

```text
415
```

---

## CSV con columnas incorrectas

```bash
printf "foo,bar\n1,2\n" > /tmp/bad.csv
```

Ejecutá:

```bash
curl -i -F "file=@/tmp/bad.csv" http://127.0.0.1:8000/api/incidents/analyze
```

Debe devolver:

```text
400
```

con un mensaje indicando columnas faltantes.

---

# PASO 41 — Verificar que Python no tenga errores

Desde la raíz:

```bash
python -m compileall packages scripts services
```

No tiene que aparecer ningún:

```text
SyntaxError
```

---

# PASO 42 — Verificar el frontend

Entrá:

```bash
cd uis/backoffice
```

Ejecutá:

```bash
npm run build
```

Tiene que terminar correctamente.

Después volver a la raíz:

```bash
cd ../..
```

---

# PASO 43 — Crear README del backend

Abrí:

```text
services/api/README.md
```

Poné:

```markdown
# Brasaland Incidents API

Backend FastAPI para analizar archivos CSV de incidencias de Brasaland.

## Ejecutar

Desde la raíz del monorepo:

```bash
source .venv/bin/activate
python -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

### Analizar CSV

`POST /api/incidents/analyze`

Recibe un archivo CSV mediante `multipart/form-data`.

### Exportar último análisis

`GET /api/incidents/results/export`

Devuelve el último análisis en formato CSV.

```

---

# PASO 44 — Crear README del frontend

Abrí:

```text
uis/backoffice/README.md
```

Reemplazá el README generado por:

```markdown
# Brasaland Backoffice

Panel interno realizado con Next.js, React y TypeScript.

Permite cargar el CSV de incidencias de Brasaland, visualizar métricas y descargar los resultados.

## Ejecutar

Primero debe estar funcionando FastAPI en el puerto 8000.

Después:

```bash
npm install
npm run dev -- --hostname 0.0.0.0
```

La aplicación utiliza un rewrite de Next.js para comunicarse con FastAPI.

```

---

# PASO 45 — Crear README del módulo compartido

Creá:

```text
packages/incidents_analysis/README.md
```

Poné:

```markdown
# Incidents Analysis

Lógica Python compartida para la validación y análisis del CSV de incidencias de Brasaland.

Es utilizada tanto por:

- `scripts/analyze.py`
- `services/api/main.py`

Esto evita duplicar la lógica de negocio.
```

---

# PASO 46 — Revisar la estructura final

Desde la raíz:

```bash
tree -L 3 packages scripts services uis
```

Deberías tener aproximadamente:

```text
packages/
└── incidents_analysis/
    ├── __init__.py
    ├── analyzer.py
    └── README.md


scripts/
├── README.md
├── analyze.py
└── incidents-brasaland.csv


services/
├── README.md
└── api/
    ├── __init__.py
    ├── main.py
    ├── README.md
    └── requirements.txt


uis/
├── README.md
└── backoffice/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.ts
    ├── README.md
    └── src/
```

---

# PASO 47 — Checklist contra la consigna

## Script

- [ ] `analyze.py` acepta una ruta por argumento.
- [ ] Puede ejecutarse sin modificar el código.
- [ ] Lee el CSV.
- [ ] Detecta registros inválidos.
- [ ] Informa la causa.
- [ ] Cuenta válidos.
- [ ] Cuenta inválidos.
- [ ] Cuenta categorías.
- [ ] Cuenta estados.
- [ ] Calcula satisfacción.
- [ ] Imprime salida legible.
- [ ] Pregunta si exportar.
- [ ] Genera `results.csv`.
- [ ] Obtiene exactamente los valores del CONTEXT.

---

## Backend

- [ ] Existe `POST /api/incidents/analyze`.
- [ ] Recibe `multipart/form-data`.
- [ ] Reutiliza `analyze_csv_text()`.
- [ ] Devuelve JSON.
- [ ] Existe `GET /api/incidents/results/export`.
- [ ] Devuelve CSV.
- [ ] Archivo vacío devuelve error.
- [ ] Archivo incorrecto devuelve error.
- [ ] CSV incorrecto devuelve error.

---

## Frontend

- [ ] Está en `uis/backoffice`.
- [ ] Utiliza Next.js.
- [ ] Utiliza React.
- [ ] Utiliza TypeScript.
- [ ] Tiene menú.
- [ ] Tiene página `/incidents`.
- [ ] Permite seleccionar CSV.
- [ ] Envía el archivo a FastAPI.
- [ ] Muestra total.
- [ ] Muestra válidos.
- [ ] Muestra inválidos.
- [ ] Muestra causas de inválidos.
- [ ] Muestra categorías.
- [ ] Muestra estados.
- [ ] Muestra satisfacción.
- [ ] Permite descargar CSV.

---

## Transversal

- [ ] Script y API utilizan la misma lógica.
- [ ] La validación no está duplicada.
- [ ] El código respeta Brasaland.
- [ ] La estructura respeta el monorepo.

---

# PASO 48 — Sacar captura de consola

Desde la raíz:

```bash
python scripts/analyze.py scripts/incidents-brasaland.csv
```

Cuando pregunte:

```text
¿Deseas exportar los resultados a CSV?
```

poné:

```text
n
```

Sacá una captura donde se vea:

```text
100 total

96 válidos

4 inválidos

categorías

estados

3.46 satisfacción
```

Esta es la primera captura requerida.

---

# PASO 49 — Sacar captura del frontend

Encendé FastAPI:

```bash
source .venv/bin/activate
```

```bash
python -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Otra terminal:

```bash
cd uis/backoffice
```

```bash
npm run dev -- --hostname 0.0.0.0
```

Abrí el puerto `3000`.

Entrá en:

```text
Incidencias
```

Subí:

```text
incidents-brasaland.csv
```

Esperá que aparezca el análisis.

Sacá una captura.

Esta es la segunda captura requerida.

---

# PASO 50 — Revisar Git

Desde la raíz:

```bash
git status
```

Después:

```bash
git diff --check
```

No debería mostrar errores.

---

# PASO 51 — Agregar los archivos

```bash
git add .
```

Comprobá:

```bash
git status
```

IMPORTANTE:

No debería aparecer:

```text
.venv/
```

ni:

```text
node_modules/
```

entre los archivos a commitear.

Si aparecen, NO hagas commit todavía.

---

# PASO 52 — Commit

Ejecutá:

```bash
git commit -m "Add Brasaland incidents analysis"
```

---

# PASO 53 — Push

```bash
git push -u origin incidents-analysis
```

---

# PASO 54 — Crear Pull Request

Volvé al repositorio en GitHub.

Debería aparecer:

```text
Compare & pull request
```

Entrá.

La configuración debería ser:

```text
base:
main

compare:
incidents-analysis
```

Título:

```text
Brasaland incidents analysis
```

Descripción sugerida:

```markdown
## Brasaland Incidents Analysis

Implements the incidents CSV analysis project.

### Included

- Python analysis script
- CSV validation
- Invalid record classification
- Category and status metrics
- Satisfaction metrics
- CSV result export
- FastAPI integration
- Next.js backoffice
- TypeScript frontend
- Downloadable result export

### Validation

The provided Brasaland CSV produces:

- 100 total records
- 96 valid records
- 4 invalid records
- 3.46 average satisfaction
```

Abajo de la descripción arrastrá:

1. La captura de consola.
2. La captura del frontend.

Creá el Pull Request.

---

# RESULTADO FINAL

Al terminar tenemos:

```text
regenerik-monorepo
│
├── CONTEXT.md
│
├── packages/
│   └── incidents_analysis/
│       └── analyzer.py
│
├── scripts/
│   ├── analyze.py
│   └── incidents-brasaland.csv
│
├── services/
│   └── api/
│       └── main.py
│
└── uis/
    └── backoffice/
        └── Next.js
```

Y funcionalmente:

```text
                 ┌───────────────┐
                 │ Brasaland CSV │
                 └───────┬───────┘
                         │
                         ▼
              ┌────────────────────┐
              │ analyzer.py        │
              │                    │
              │ Validar            │
              │ Contar             │
              │ Calcular métricas  │
              └─────────┬──────────┘
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
       analyze.py              FastAPI
                                  │
                                  ▼
                               Next.js
                                  │
                                  ▼
                              USUARIO
```

El corazón de TODO el proyecto es solamente:

```python
for row in rows:

    problems =
        validate_row(row)

    if problems:

        invalid_records += 1

    else:

        valid_rows.append(row)
```

Después:

```python
category_counts =
    Counter(
        row["category"]
        for row in valid_rows
    )
```

Es decir:

```text
LOS REGISTROS INVÁLIDOS
SE INFORMAN

PERO

NO PARTICIPAN
DE LAS MÉTRICAS PRINCIPALES.
```

Todo lo demás es simplemente ponerle interfaces alrededor:

```text
Python script
     +
FastAPI
     +
Next.js
```

Y listo. No estamos construyendo Skynet para contar cien filas de un CSV.
