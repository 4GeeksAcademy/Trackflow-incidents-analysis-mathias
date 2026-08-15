import csv
import re

from collections import Counter
from datetime import datetime
from io import StringIO


EXPECTED_COLUMNS = [
    "incident_id",
    "date",
    "country",
    "customer_type",
    "tracking_number",
    "carrier",
    "category",
    "description",
    "status",
    "customer_email",
    "satisfaction_score",
]


VALID_COUNTRIES = [
    "ES",
    "US",
]


VALID_CUSTOMER_TYPES = [
    "B2B",
    "B2C",
]


VALID_CARRIERS = [
    "LOCAL_ES",
    "MRW",
    "UPS",
    "FEDEX",
    "SEUR",
    "DHL_ES",
    "DHL_US",
]


VALID_CATEGORIES = [
    "RETURN_REQUEST",
    "DAMAGE",
    "DELAYED_DELIVERY",
    "WRONG_ADDRESS",
    "LOST_PARCEL",
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

    "invalid_country":
        "Invalid or missing country",

    "invalid_customer_type":
        "Invalid or missing customer_type",

    "invalid_tracking_number":
        "Invalid tracking_number format",

    "invalid_carrier":
        "Invalid or missing carrier",

    "invalid_category":
        "Invalid or missing category",

    "invalid_description":
        "Empty or too-short description",

    "invalid_status":
        "Invalid or missing status",

    "invalid_customer_email":
        "Invalid customer_email format",

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
        r"TRF-\d{6}",
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


    # country

    country = clean(
        row.get("country")
    )

    if (
        country
        not in VALID_COUNTRIES
    ):

        errors.append(
            "invalid_country"
        )


    # customer_type

    customer_type = clean(
        row.get("customer_type")
    )

    if (
        customer_type
        not in VALID_CUSTOMER_TYPES
    ):

        errors.append(
            "invalid_customer_type"
        )


    # tracking_number

    tracking_number = clean(
        row.get("tracking_number")
    )

    if not re.fullmatch(
        r"[A-Z0-9]{12}",
        tracking_number,
    ):

        errors.append(
            "invalid_tracking_number"
        )


    # carrier

    carrier = clean(
        row.get("carrier")
    )

    if (
        carrier
        not in VALID_CARRIERS
    ):

        errors.append(
            "invalid_carrier"
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


    # customer_email

    customer_email = clean(
        row.get("customer_email")
    )

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        customer_email,
    ):

        errors.append(
            "invalid_customer_email"
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
        "incidents-trackflow.csv"
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


    # Países

    country_counts = Counter(

        clean(
            row.get("country")
        )

        for row in valid_rows
    )


    # Tipo de cliente

    customer_type_counts = Counter(

        clean(
            row.get("customer_type")
        )

        for row in valid_rows
    )


    # Carrier

    carrier_counts = Counter(

        clean(
            row.get("carrier")
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
            "TRACKFLOW",

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

        "by_country":
            build_breakdown(
                country_counts,
                VALID_COUNTRIES,
                valid_records,
            ),

        "by_customer_type":
            build_breakdown(
                customer_type_counts,
                VALID_CUSTOMER_TYPES,
                valid_records,
            ),

        "by_carrier":
            build_breakdown(
                carrier_counts,
                VALID_CARRIERS,
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
            "  TRACKFLOW — "
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


    lines.extend([
        "",
        (
            "BREAKDOWN BY COUNTRY "
            "(valid records)"
        ),
    ])


    for country, data in (
        summary[
            "by_country"
        ].items()
    ):

        lines.append(

            f"  {country:<28} "

            f"{data['count']:>3}  "

            f"("
            f"{data['percentage']:.1f}"
            f"%)"

        )


    lines.extend([
        "",
        (
            "BREAKDOWN BY CUSTOMER TYPE "
            "(valid records)"
        ),
    ])


    for customer_type, data in (
        summary[
            "by_customer_type"
        ].items()
    ):

        lines.append(

            f"  {customer_type:<28} "

            f"{data['count']:>3}  "

            f"("
            f"{data['percentage']:.1f}"
            f"%)"

        )


    lines.extend([
        "",
        (
            "BREAKDOWN BY CARRIER "
            "(valid records)"
        ),
    ])


    for carrier, data in (
        summary[
            "by_carrier"
        ].items()
    ):

        lines.append(

            f"  {carrier:<28} "

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


    for country, data in (
        summary[
            "by_country"
        ].items()
    ):

        writer.writerow([

            f"country.{country}",

            data[
                "count"
            ],

            data[
                "percentage"
            ],

        ])


    for customer_type, data in (
        summary[
            "by_customer_type"
        ].items()
    ):

        writer.writerow([

            f"customer_type.{customer_type}",

            data[
                "count"
            ],

            data[
                "percentage"
            ],

        ])


    for carrier, data in (
        summary[
            "by_carrier"
        ].items()
    ):

        writer.writerow([

            f"carrier.{carrier}",

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
