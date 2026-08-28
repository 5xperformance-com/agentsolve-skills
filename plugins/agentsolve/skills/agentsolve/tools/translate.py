#!/usr/bin/env python3
"""Translate common native optimization formats into canonical AgentSolve input.

Generated from the AgentSolve production format translators; do not edit by
hand — regenerate the adoption surface instead. Formats: TSPLIB
(.tsp/.atsp), CVRPLIB (.vrp), MPS (.mps/.mps.gz), PSPLIB single-mode (.sm),
and Taillard JSSP. Dialects outside the accepted subset are rejected, never
approximated.

Usage:
    python tools/translate.py INSTANCE_FILE [MORE_FILES ...]
        [--out OUT.json | --out-dir DIR]
        [--format {tsplib,cvrplib,mps,psplib-sm,taillard}]
        [--vehicle-count N] [--instance-index K]

Canonical documents are written into the working directory by default
(or --out-dir), never beside the instance files — input directories stay
pristine. Each document carries problem_type, problem_schema_version,
payload, node_numbering, notes, format_id, and source_file; submit it
with tools/submit.py. With one instance the summary printed to stdout is
a single object; with several it is an array in argument order.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


"""Shared parsing primitives for native benchmark-format translators.

Every function here is standard-library pure and standalone-embeddable:
the published skill's translator is generated from these sources, so
nothing in this module may import from the wider package.
"""


import math
import re


class NativeFormatError(ValueError):
    """A native file is outside the supported dialect subset.

    Unsupported semantics are rejected, never approximated; the message
    names the offending header, section, or value.
    """


def split_spec_and_data(text: str) -> tuple[dict[str, str], list[str]]:
    """Split a TSPLIB-family file into `KEY : value` specs and data lines.

    Section markers (`*_SECTION`) are kept in the data stream so callers
    can scope rows to their section. `EOF` and blank lines are dropped.
    """
    specs: dict[str, str] = {}
    data: list[str] = []
    in_data = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "EOF":
            continue
        if re.match(r"^[A-Z_]+_SECTION\s*$", line):
            in_data = True
            data.append(line.split()[0])
            continue
        if not in_data and ":" in line:
            key, _, value = line.partition(":")
            specs[key.strip().upper()] = value.strip()
            continue
        data.append(line)
    return specs, data


def section_lines(data: list[str], section: str) -> list[str]:
    """Return the data lines belonging to one `*_SECTION` block."""
    lines: list[str] = []
    active = False
    for line in data:
        if line.endswith("_SECTION"):
            active = line == section
            continue
        if active:
            lines.append(line)
    return lines


def euclidean_nearest_int(ax: float, ay: float, bx: float, by: float) -> int:
    """TSPLIB/CVRPLIB EUC_2D: Euclidean distance, nearest integer."""
    return int(math.sqrt((ax - bx) ** 2 + (ay - by) ** 2) + 0.5)


def geo_distance(alat: float, alon: float, blat: float, blon: float) -> int:
    """TSPLIB GEO: geographical distance on the idealized sphere.

    Coordinates are DDD.MM (degrees and minutes), the radius is the
    TSPLIB constant 6378.388, and the result truncates after adding 1.0
    — exactly the published TSPLIB definition, which reference optima
    depend on.
    """
    pi = 3.141592

    def radians(value: float) -> float:
        degrees = int(value)
        minutes = value - degrees
        return pi * (degrees + 5.0 * minutes / 3.0) / 180.0

    lat_i, lon_i = radians(alat), radians(alon)
    lat_j, lon_j = radians(blat), radians(blon)
    rrr = 6378.388
    q1 = math.cos(lon_i - lon_j)
    q2 = math.cos(lat_i - lat_j)
    q3 = math.cos(lat_i + lat_j)
    return int(rrr * math.acos(0.5 * ((1.0 + q1) * q2 - (1.0 - q1) * q3)) + 1.0)


def indexed_coord_rows(
    data: list[str],
    section: str,
    *,
    dimension: int,
    file_label: str,
) -> dict[int, tuple[float, float]]:
    """Parse `index x y` rows and require contiguous 1..dimension indices."""
    rows: dict[int, tuple[float, float]] = {}
    for line in section_lines(data, section):
        tokens = line.split()
        if len(tokens) != 3:
            raise NativeFormatError(f"{file_label}: malformed {section} row: {line!r}")
        index = int(tokens[0])
        if index in rows:
            raise NativeFormatError(f"{file_label}: duplicate node index {index}")
        rows[index] = (float(tokens[1]), float(tokens[2]))
    if sorted(rows) != list(range(1, dimension + 1)):
        raise NativeFormatError(
            f"{file_label}: {section} must cover node indices 1..{dimension} contiguously"
        )
    return rows


def section_integers(data: list[str], section: str, *, file_label: str) -> list[int]:
    """All whitespace-separated integers inside one section, in order."""
    values: list[int] = []
    for line in section_lines(data, section):
        for token in line.split():
            try:
                values.append(int(token))
            except ValueError as exc:
                raise NativeFormatError(
                    f"{file_label}: non-integer value {token!r} in {section}"
                ) from exc
    return values


"""TSPLIB `.tsp` / `.atsp` → canonical `1.1.tsp` input payloads.

Supported dialect subset (anything else is rejected, never approximated):
symmetric `TYPE: TSP` with `EUC_2D`, `GEO`, or `EXPLICIT` weights in
`FULL_MATRIX` or `LOWER_DIAG_ROW` format; asymmetric `TYPE: ATSP` with
`EXPLICIT FULL_MATRIX` only. Node ids become `n1..nDIMENSION` in file
order, and the returned numbering maps native index − 1 → canonical id.
"""


from typing import Any


_SUPPORTED_TSP_WEIGHT_TYPES = ("EUC_2D", "GEO", "EXPLICIT")
_SUPPORTED_TSP_EXPLICIT_FORMATS = ("FULL_MATRIX", "LOWER_DIAG_ROW")


def convert_tsp(text: str, *, file_label: str = "input.tsp") -> dict[str, Any]:
    """Translate a symmetric TSPLIB instance; returns payload/numbering/notes."""
    return _convert(text, file_label=file_label, expected_type="TSP")


def convert_atsp(text: str, *, file_label: str = "input.atsp") -> dict[str, Any]:
    """Translate an asymmetric TSPLIB instance; returns payload/numbering/notes."""
    return _convert(text, file_label=file_label, expected_type="ATSP")


def _convert(text: str, *, file_label: str, expected_type: str) -> dict[str, Any]:
    specs, data = split_spec_and_data(text)
    file_type = specs.get("TYPE", "").split()[0] if specs.get("TYPE") else ""
    if file_type != expected_type:
        raise NativeFormatError(
            f"{file_label}: TYPE is {file_type or 'missing'!r}; expected {expected_type}"
        )
    if "DIMENSION" not in specs:
        raise NativeFormatError(f"{file_label}: missing DIMENSION header")
    dimension = int(specs["DIMENSION"])
    if dimension < 2:
        raise NativeFormatError(f"{file_label}: DIMENSION must be at least 2")

    weight_type = specs.get("EDGE_WEIGHT_TYPE", "")
    notes: list[str] = [f"dialect: {expected_type}/{weight_type or 'missing'}"]

    if expected_type == "ATSP":
        if weight_type != "EXPLICIT" or specs.get("EDGE_WEIGHT_FORMAT") != "FULL_MATRIX":
            raise NativeFormatError(
                f"{file_label}: ATSP supports only EXPLICIT FULL_MATRIX weights; "
                f"got {weight_type!r}/{specs.get('EDGE_WEIGHT_FORMAT')!r}"
            )
        matrix = _full_matrix(data, dimension, file_label=file_label)
        notes.append("asymmetric weights preserved directionally")
    elif weight_type == "EUC_2D":
        coords = indexed_coord_rows(
            data, "NODE_COORD_SECTION", dimension=dimension, file_label=file_label
        )
        matrix = [
            [
                euclidean_nearest_int(*coords[a + 1], *coords[b + 1])
                for b in range(dimension)
            ]
            for a in range(dimension)
        ]
        notes.append("EUC_2D nearest-integer rounding applied")
    elif weight_type == "GEO":
        coords = indexed_coord_rows(
            data, "NODE_COORD_SECTION", dimension=dimension, file_label=file_label
        )
        matrix = [
            [
                geo_distance(*coords[a + 1], *coords[b + 1])
                for b in range(dimension)
            ]
            for a in range(dimension)
        ]
        notes.append("GEO spherical distance with TSPLIB truncation applied")
    elif weight_type == "EXPLICIT":
        weight_format = specs.get("EDGE_WEIGHT_FORMAT", "")
        if weight_format == "FULL_MATRIX":
            matrix = _full_matrix(data, dimension, file_label=file_label)
            _require_symmetric(matrix, file_label=file_label)
        elif weight_format == "LOWER_DIAG_ROW":
            matrix = _lower_diag_row(data, dimension, file_label=file_label)
            notes.append("LOWER_DIAG_ROW expanded symmetrically")
        else:
            raise NativeFormatError(
                f"{file_label}: unsupported EDGE_WEIGHT_FORMAT {weight_format or 'missing'!r}; "
                f"supported: {', '.join(_SUPPORTED_TSP_EXPLICIT_FORMATS)}"
            )
    else:
        raise NativeFormatError(
            f"{file_label}: unsupported EDGE_WEIGHT_TYPE {weight_type or 'missing'!r}; "
            f"supported: {', '.join(_SUPPORTED_TSP_WEIGHT_TYPES)}"
        )

    numbering = tuple(f"n{index}" for index in range(1, dimension + 1))
    distances = {
        numbering[a]: {
            numbering[b]: float(matrix[a][b]) for b in range(dimension) if b != a
        }
        for a in range(dimension)
    }
    payload = {
        "nodes": list(numbering),
        "start_node": numbering[0],
        "distances": distances,
    }
    return {"payload": payload, "node_numbering": numbering, "notes": tuple(notes)}


def _require_symmetric(matrix: list[list[int]], *, file_label: str) -> None:
    for row in range(len(matrix)):
        for col in range(row + 1, len(matrix)):
            if matrix[row][col] != matrix[col][row]:
                raise NativeFormatError(
                    f"{file_label}: TYPE TSP declares symmetric weights but "
                    f"FULL_MATRIX entries ({row + 1},{col + 1}) and "
                    f"({col + 1},{row + 1}) differ; use TYPE ATSP for "
                    "asymmetric instances"
                )


def _full_matrix(data: list[str], dimension: int, *, file_label: str) -> list[list[int]]:
    values = section_integers(data, "EDGE_WEIGHT_SECTION", file_label=file_label)
    if len(values) != dimension * dimension:
        raise NativeFormatError(
            f"{file_label}: FULL_MATRIX needs {dimension * dimension} weights, "
            f"got {len(values)}"
        )
    return [values[row * dimension : (row + 1) * dimension] for row in range(dimension)]


def _lower_diag_row(data: list[str], dimension: int, *, file_label: str) -> list[list[int]]:
    values = section_integers(data, "EDGE_WEIGHT_SECTION", file_label=file_label)
    expected = dimension * (dimension + 1) // 2
    if len(values) != expected:
        raise NativeFormatError(
            f"{file_label}: LOWER_DIAG_ROW needs {expected} weights, got {len(values)}"
        )
    matrix = [[0] * dimension for _ in range(dimension)]
    cursor = 0
    for row in range(dimension):
        for col in range(row + 1):
            value = values[cursor]
            cursor += 1
            matrix[row][col] = value
            matrix[col][row] = value
    return matrix


def write_tour(route: list[str], numbering: tuple[str, ...], name: str) -> str:
    """Render a canonical TSP route as a TSPLIB TOUR file (1-based indices)."""
    index_of = {node_id: position + 1 for position, node_id in enumerate(numbering)}
    unknown = [node_id for node_id in route if node_id not in index_of]
    if unknown:
        raise NativeFormatError(f"route names unknown node ids: {unknown[:3]}")
    body = route[:-1] if len(route) > 1 and route[0] == route[-1] else route
    lines = [
        f"NAME : {name}",
        "TYPE : TOUR",
        f"DIMENSION : {len(numbering)}",
        "TOUR_SECTION",
        *[str(index_of[node_id]) for node_id in body],
        "-1",
        "EOF",
        "",
    ]
    return "\n".join(lines)


"""CVRPLIB `.vrp` → canonical `1.2.vrp.cvrp` input payloads.

Supported dialect subset (anything else is rejected, never approximated):
`TYPE: CVRP`, a single depot at node 1 with zero demand, and either
`EDGE_WEIGHT_TYPE: EUC_2D` (nearest-integer rounding) or
`EXPLICIT` weights in `LOWER_ROW` format. The vehicle limit is a semantic
requirement: it comes from a `VEHICLES` header, the Augerat-style
`No of trucks: k` comment, or an explicit argument — never guessed.
Node ids become `n1..nDIMENSION`; the numbering maps native index − 1 →
canonical id, with `n1` the depot.
"""


import re
from typing import Any


_TRUCKS_COMMENT = re.compile(r"No of trucks\s*:\s*(\d+)", re.IGNORECASE)


def convert_vrp(
    text: str,
    *,
    vehicle_count: int | None = None,
    file_label: str = "input.vrp",
) -> dict[str, Any]:
    """Translate a CVRPLIB instance; returns payload/numbering/notes."""
    specs, data = split_spec_and_data(text)
    file_type = specs.get("TYPE", "").split()[0] if specs.get("TYPE") else ""
    if file_type != "CVRP":
        raise NativeFormatError(
            f"{file_label}: TYPE is {file_type or 'missing'!r}; expected CVRP"
        )
    for unsupported in ("DISTANCE", "SERVICE_TIME"):
        if unsupported in specs:
            raise NativeFormatError(
                f"{file_label}: {unsupported} header is outside the supported CVRP subset"
            )
    if "DIMENSION" not in specs or "CAPACITY" not in specs:
        raise NativeFormatError(f"{file_label}: missing DIMENSION or CAPACITY header")
    dimension = int(specs["DIMENSION"])
    capacity = int(specs["CAPACITY"])

    resolved_vehicles: int | None = None
    vehicle_source = ""
    if specs.get("VEHICLES"):
        resolved_vehicles = int(specs["VEHICLES"])
        vehicle_source = "VEHICLES header"
    else:
        comment_match = _TRUCKS_COMMENT.search(specs.get("COMMENT", ""))
        if comment_match:
            resolved_vehicles = int(comment_match.group(1))
            vehicle_source = "COMMENT trucks count"
    if resolved_vehicles is None:
        if vehicle_count is None:
            raise NativeFormatError(
                f"{file_label}: vehicle count not declared (no VEHICLES header or "
                "'No of trucks' comment); pass it explicitly — the exact vehicle "
                "limit is a semantic requirement, never guessed"
            )
        resolved_vehicles = vehicle_count
        vehicle_source = "explicit argument"
    elif vehicle_count is not None and vehicle_count != resolved_vehicles:
        raise NativeFormatError(
            f"{file_label}: explicit vehicle count {vehicle_count} conflicts "
            f"with the file's declared count {resolved_vehicles} "
            f"({vehicle_source}); the file declaration wins and the conflict "
            "is rejected, never resolved silently"
        )

    weight_type = specs.get("EDGE_WEIGHT_TYPE", "")
    notes: list[str] = [
        f"dialect: CVRP/{weight_type or 'missing'}",
        f"vehicle count {resolved_vehicles} from {vehicle_source}",
    ]

    if weight_type == "EUC_2D":
        coords = indexed_coord_rows(
            data, "NODE_COORD_SECTION", dimension=dimension, file_label=file_label
        )
        matrix = [
            [
                euclidean_nearest_int(*coords[a + 1], *coords[b + 1])
                for b in range(dimension)
            ]
            for a in range(dimension)
        ]
        notes.append("EUC_2D nearest-integer rounding applied")
    elif weight_type == "EXPLICIT":
        if specs.get("EDGE_WEIGHT_FORMAT") != "LOWER_ROW":
            raise NativeFormatError(
                f"{file_label}: EXPLICIT CVRP weights support only LOWER_ROW; "
                f"got {specs.get('EDGE_WEIGHT_FORMAT')!r}"
            )
        matrix = _lower_row(data, dimension, file_label=file_label)
        notes.append("EXPLICIT LOWER_ROW weights preserved without rounding")
    else:
        raise NativeFormatError(
            f"{file_label}: unsupported EDGE_WEIGHT_TYPE {weight_type or 'missing'!r}; "
            "supported: EUC_2D, EXPLICIT (LOWER_ROW)"
        )

    demands = _demand_rows(data, dimension, file_label=file_label)
    _require_single_depot_node_one(data, demands, file_label=file_label)

    numbering = tuple(f"n{index}" for index in range(1, dimension + 1))
    payload = {
        "id": file_label.rsplit("/", 1)[-1].rsplit(".", 1)[0] or "cvrp-instance",
        "job_intent": "optimize",
        "depot": {"id": numbering[0]},
        "vehicle_count": resolved_vehicles,
        "vehicle_capacity": capacity,
        "customers": [
            {"id": numbering[index], "demand": demands[index + 1]}
            for index in range(1, dimension)
        ],
        "distances": {
            numbering[a]: {
                numbering[b]: float(matrix[a][b]) for b in range(dimension) if b != a
            }
            for a in range(dimension)
        },
    }
    return {"payload": payload, "node_numbering": numbering, "notes": tuple(notes)}


def _lower_row(data: list[str], dimension: int, *, file_label: str) -> list[list[int]]:
    values = section_integers(data, "EDGE_WEIGHT_SECTION", file_label=file_label)
    expected = dimension * (dimension - 1) // 2
    if len(values) != expected:
        raise NativeFormatError(
            f"{file_label}: LOWER_ROW needs {expected} weights, got {len(values)}"
        )
    matrix = [[0] * dimension for _ in range(dimension)]
    cursor = 0
    for row in range(1, dimension):
        for col in range(row):
            value = values[cursor]
            cursor += 1
            matrix[row][col] = value
            matrix[col][row] = value
    return matrix


def _demand_rows(data: list[str], dimension: int, *, file_label: str) -> dict[int, int]:
    demands: dict[int, int] = {}
    for line in section_lines(data, "DEMAND_SECTION"):
        tokens = line.split()
        if len(tokens) != 2:
            raise NativeFormatError(f"{file_label}: malformed DEMAND_SECTION row: {line!r}")
        demands[int(tokens[0])] = int(tokens[1])
    if sorted(demands) != list(range(1, dimension + 1)):
        raise NativeFormatError(
            f"{file_label}: DEMAND_SECTION must cover node indices 1..{dimension}"
        )
    return demands


def _require_single_depot_node_one(
    data: list[str], demands: dict[int, int], *, file_label: str
) -> None:
    depot_indices: list[int] = []
    for line in section_lines(data, "DEPOT_SECTION"):
        for token in line.split():
            value = int(token)
            if value == -1:
                break
            depot_indices.append(value)
    if depot_indices != [1] or demands[1] != 0:
        raise NativeFormatError(
            f"{file_label}: only single-depot instances with the depot at node 1 "
            "(zero demand) are supported"
        )


def write_sol(
    routes: list[list[str]],
    numbering: tuple[str, ...],
    objective: float | int | None,
) -> str:
    """Render canonical CVRP routes as a CVRPLIB solution file.

    Customers use CVRPLIB solution numbering: node index − 1, depot never
    listed.
    """
    index_of = {node_id: position for position, node_id in enumerate(numbering)}
    lines: list[str] = []
    for route_number, route in enumerate(routes, start=1):
        customers: list[str] = []
        for node_id in route:
            if node_id not in index_of:
                raise NativeFormatError(f"route names unknown node id {node_id!r}")
            position = index_of[node_id]
            if position == 0:
                continue
            customers.append(str(position))
        lines.append(f"Route #{route_number}: " + " ".join(customers))
    if objective is not None:
        rendered = int(objective) if float(objective).is_integer() else objective
        lines.append(f"Cost {rendered}")
    lines.append("")
    return "\n".join(lines)


"""MPS (fixed/free) → canonical `2.2.milp` or `2.1.lp` input payloads.

The parser accepts the deliberately narrow direct-to-canonical subset:
one `N` objective row, linear `L`/`E`/`G` rows, standard integer
markers, value-bearing `LI`/`UP` bounds, single RHS and bound sets.
Anything broader — `RANGES`, `SOS`, quadratic sections, `OBJSENSE` —
is rejected, never approximated. Integrality is structural: any integer
or binary variable routes the model to MILP; a purely continuous model
routes to LP.
"""


import gzip
import math
from dataclasses import dataclass
from typing import Any


DIRECT_ROW_SETS = {"L": "nonpos", "E": "zeros", "G": "nonneg"}
SECTIONS = {"NAME", "ROWS", "COLUMNS", "RHS", "BOUNDS", "ENDATA"}
UNSUPPORTED_SECTIONS = {
    "OBJSENSE",
    "OBJNAME",
    "RANGES",
    "SOS",
    "QMATRIX",
    "QCMATRIX",
    "QUADOBJ",
    "CSECTION",
    "INDICATORS",
}


class MpsPreflightError(NativeFormatError):
    """The model is outside the directly representable MPS subset."""


@dataclass(frozen=True)
class DirectMps:
    """The direct linear MPS subset needed for lossless canonical conversion."""

    name: str
    source_sections: tuple[str, ...]
    objective_row: str
    row_senses: dict[str, str]
    row_order: tuple[str, ...]
    coefficients: dict[str, dict[str, float]]
    variables: frozenset[str]
    marker_integers: frozenset[str]
    bound_integers: frozenset[str]
    lower_bounds: dict[str, float]
    upper_bounds: dict[str, float]
    rhs: dict[str, float]
    values: tuple[float, ...]


def _number(token: str, *, line_number: int, errors: list[str]) -> float | None:
    try:
        value = float(token.replace("D", "E").replace("d", "e"))
    except ValueError:
        errors.append(f"line {line_number}: invalid numeric value {token!r}")
        return None
    if not math.isfinite(value):
        errors.append(f"line {line_number}: non-finite numeric value {token!r}")
        return None
    return value


def parse_mps(text: str) -> DirectMps:
    """Parse the intentionally narrow direct-to-canonical MPS subset."""

    errors: list[str] = []
    section: str | None = None
    seen_sections: list[str] = []
    name: str | None = None
    objective_rows: list[str] = []
    row_senses: dict[str, str] = {}
    row_order: list[str] = []
    coefficients: dict[str, dict[str, float]] = {}
    variables: set[str] = set()
    marker_integers: set[str] = set()
    bound_integers: set[str] = set()
    lower_bounds: dict[str, float] = {}
    upper_bounds: dict[str, float] = {}
    rhs: dict[str, float] = {}
    rhs_set: str | None = None
    bound_set: str | None = None
    integer_mode = False
    values: list[float] = []

    def add_coefficient(row: str, variable: str, value: float, line_number: int) -> None:
        row_coefficients = coefficients.setdefault(row, {})
        if variable in row_coefficients:
            errors.append(
                f"line {line_number}: duplicate coefficient for {variable!r} in {row!r}"
            )
            return
        row_coefficients[variable] = value

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("*"):
            continue
        tokens = stripped.split()
        header = tokens[0].upper()
        is_header = raw_line[:1] not in {" ", "\t"}
        if is_header:
            if header in UNSUPPORTED_SECTIONS:
                errors.append(f"line {line_number}: unsupported {header} section")
                section = header
                continue
            if header not in SECTIONS:
                errors.append(f"line {line_number}: unsupported MPS section {header!r}")
                section = header
                continue
            if header in seen_sections:
                errors.append(f"line {line_number}: duplicate {header} section")
            seen_sections.append(header)
            section = header
            if header == "NAME":
                if len(tokens) != 2:
                    errors.append(f"line {line_number}: NAME must contain one model name")
                else:
                    name = tokens[1]
            continue

        if section == "ROWS":
            if len(tokens) != 2:
                errors.append(f"line {line_number}: malformed ROWS entry")
                continue
            row_sense, row_name = tokens[0].upper(), tokens[1]
            if row_name in row_senses:
                errors.append(f"line {line_number}: duplicate row {row_name!r}")
                continue
            if row_sense == "N":
                objective_rows.append(row_name)
            elif row_sense in DIRECT_ROW_SETS:
                row_order.append(row_name)
            else:
                errors.append(f"line {line_number}: unsupported row sense {row_sense!r}")
                continue
            row_senses[row_name] = row_sense
            continue

        if section == "COLUMNS":
            marker_tokens = {token.strip("'").upper() for token in tokens}
            if "MARKER" in marker_tokens:
                if "INTORG" in marker_tokens and not integer_mode:
                    integer_mode = True
                elif "INTEND" in marker_tokens and integer_mode:
                    integer_mode = False
                else:
                    errors.append(f"line {line_number}: malformed integer marker")
                continue
            if len(tokens) < 3 or len(tokens) % 2 == 0:
                errors.append(f"line {line_number}: malformed COLUMNS entry")
                continue
            variable = tokens[0]
            variables.add(variable)
            if integer_mode:
                marker_integers.add(variable)
            for index in range(1, len(tokens), 2):
                row_name = tokens[index]
                value = _number(tokens[index + 1], line_number=line_number, errors=errors)
                if value is None:
                    continue
                values.append(value)
                if row_name not in row_senses:
                    errors.append(
                        f"line {line_number}: COLUMNS names unknown row {row_name!r}"
                    )
                    continue
                add_coefficient(row_name, variable, value, line_number)
            continue

        if section == "RHS":
            if len(tokens) < 3 or len(tokens) % 2 == 0:
                errors.append(f"line {line_number}: malformed RHS entry")
                continue
            if rhs_set is None:
                rhs_set = tokens[0]
            elif rhs_set != tokens[0]:
                errors.append(f"line {line_number}: multiple RHS sets are unsupported")
            for index in range(1, len(tokens), 2):
                row_name = tokens[index]
                value = _number(tokens[index + 1], line_number=line_number, errors=errors)
                if value is None:
                    continue
                values.append(value)
                if row_name not in row_senses:
                    errors.append(f"line {line_number}: RHS names unknown row {row_name!r}")
                    continue
                if row_name in rhs:
                    errors.append(f"line {line_number}: duplicate RHS for row {row_name!r}")
                    continue
                rhs[row_name] = value
            continue

        if section == "BOUNDS":
            if len(tokens) != 4:
                errors.append(
                    f"line {line_number}: only value-bearing LI and UP bounds are supported"
                )
                continue
            bound_type, current_bound_set, variable, raw_value = tokens
            bound_type = bound_type.upper()
            if bound_type not in {"LI", "UP"}:
                errors.append(f"line {line_number}: unsupported bound type {bound_type!r}")
                continue
            if bound_set is None:
                bound_set = current_bound_set
            elif bound_set != current_bound_set:
                errors.append(f"line {line_number}: multiple bound sets are unsupported")
            value = _number(raw_value, line_number=line_number, errors=errors)
            if value is None:
                continue
            values.append(value)
            variables.add(variable)
            if bound_type == "LI":
                if variable in lower_bounds:
                    errors.append(
                        f"line {line_number}: duplicate lower bound for {variable!r}"
                    )
                lower_bounds[variable] = value
                bound_integers.add(variable)
            else:
                if variable in upper_bounds:
                    errors.append(
                        f"line {line_number}: duplicate upper bound for {variable!r}"
                    )
                upper_bounds[variable] = value
            continue

        if section == "ENDATA":
            errors.append(f"line {line_number}: data appears after ENDATA")
        elif section is not None:
            errors.append(f"line {line_number}: unsupported data in {section} section")

    if integer_mode:
        errors.append("COLUMNS ends inside an INTORG marker region")
    for required in ("NAME", "ROWS", "COLUMNS", "ENDATA"):
        if required not in seen_sections:
            errors.append(f"missing {required} section")
    if name is None:
        errors.append("missing MPS model name")
    if len(objective_rows) != 1:
        errors.append(f"expected exactly one objective row, found {len(objective_rows)}")
    objective_row = objective_rows[0] if len(objective_rows) == 1 else None
    if objective_row is not None and objective_row in rhs:
        errors.append("objective RHS/constant requires a separately reviewed mapping")
    if not variables:
        errors.append("MPS model declares no variables")
    for variable in variables:
        lower = lower_bounds.get(variable, 0.0)
        upper = upper_bounds.get(variable)
        if upper is not None and lower > upper:
            errors.append(
                f"variable {variable!r} has inverted bounds: lower={lower}, upper={upper}"
            )

    if errors:
        raise MpsPreflightError("; ".join(errors))
    assert name is not None
    assert objective_row is not None

    return DirectMps(
        name=name,
        source_sections=tuple(seen_sections),
        objective_row=objective_row,
        row_senses=row_senses,
        row_order=tuple(row_order),
        coefficients=coefficients,
        variables=frozenset(variables),
        marker_integers=frozenset(marker_integers),
        bound_integers=frozenset(bound_integers),
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        rhs=rhs,
        values=tuple(values),
    )


def variable_type(model: DirectMps, variable: str) -> str:
    integer = variable in model.marker_integers or variable in model.bound_integers
    lower = model.lower_bounds.get(variable, 0.0)
    upper = model.upper_bounds.get(variable)
    if integer and lower == 0.0 and upper == 1.0:
        return "binary"
    return "integer" if integer else "continuous"


def _constraint_constant(model: DirectMps, row_name: str) -> float:
    rhs = model.rhs.get(row_name, 0.0)
    return 0.0 if rhs == 0.0 else -rhs


def _payload_from_mps(
    model: DirectMps, model_id: str, *, continuous_only: bool
) -> dict[str, Any]:
    variables: dict[str, dict[str, Any]] = {}
    for variable in sorted(model.variables):
        kind = variable_type(model, variable)
        if continuous_only:
            kind = "continuous"
        if kind == "binary":
            variables[variable] = {"type": kind}
        else:
            variables[variable] = {
                "type": kind,
                "lb": model.lower_bounds.get(variable, 0.0),
                "ub": model.upper_bounds.get(variable),
            }
    return {
        "id": model_id,
        "job_intent": "optimize",
        "variables": variables,
        "constraints": [
            {
                "id": row_name,
                "function": {
                    "type": "linear",
                    "coefficients": dict(
                        sorted(model.coefficients.get(row_name, {}).items())
                    ),
                    "constant": _constraint_constant(model, row_name),
                },
                "set": {
                    "type": DIRECT_ROW_SETS[model.row_senses[row_name]],
                    "dimension": None,
                },
                "scope": "global",
            }
            for row_name in model.row_order
        ],
        "objective": {
            "id": model.objective_row,
            "sense": "minimize",
            "function": {
                "type": "linear",
                "coefficients": dict(
                    sorted(model.coefficients.get(model.objective_row, {}).items())
                ),
                "constant": 0.0,
            },
        },
    }


def milp_payload_from_mps(model: DirectMps, model_id: str) -> dict[str, Any]:
    """Map the accepted MPS subset into the raw MILP canonical shape."""
    return _payload_from_mps(model, model_id, continuous_only=False)


def lp_payload_from_mps(model: DirectMps, model_id: str) -> dict[str, Any]:
    """Map a purely continuous MPS model into the raw LP canonical shape."""
    integers = sorted(
        variable
        for variable in model.variables
        if variable_type(model, variable) != "continuous"
    )
    if integers:
        raise MpsPreflightError(
            "model declares integer or binary variables and belongs to 2.2.milp: "
            + ", ".join(integers[:5])
            + ("..." if len(integers) > 5 else "")
        )
    return _payload_from_mps(model, model_id, continuous_only=True)


def convert_mps(data: bytes, *, file_label: str = "input.mps") -> dict[str, Any]:
    """Translate MPS bytes (gzip tolerated); routes to MILP or LP by integrality."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    model = parse_mps(text)
    model_id = file_label.rsplit("/", 1)[-1].rsplit(".", 1)[0] or model.name
    has_integers = any(
        variable_type(model, variable) != "continuous" for variable in model.variables
    )
    notes = [
        f"dialect: MPS direct subset ({len(model.variables)} variables, "
        f"{len(model.row_order)} constraints)",
        "integrality preserved: routed to 2.2.milp"
        if has_integers
        else "purely continuous: routed to 2.1.lp",
    ]
    if has_integers:
        payload = milp_payload_from_mps(model, model_id)
        problem_type = "2.2.milp"
    else:
        payload = lp_payload_from_mps(model, model_id)
        problem_type = "2.1.lp"
    return {
        "payload": payload,
        "node_numbering": None,
        "notes": tuple(notes),
        "problem_type": problem_type,
    }


"""PSPLIB single-mode `.sm` → canonical `4.1.scheduling.rcpsp` payloads.

Supported subset: single-mode instances with renewable resources only and
zero-valued supersource/sink dummies (the standard PSPLIB shape).
Multi-mode files and nonrenewable or doubly constrained resources are
rejected, never approximated. Activity ids become `j2..j(N-1)` (dummies
dropped), resources `R1..Rk` — matching the corpus convention.
"""


import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SmMetadata:
    horizon: int
    job_count: int
    resource_count: int


def convert_sm(text: str, *, file_label: str = "input.sm") -> dict[str, Any]:
    """Translate a PSPLIB `.sm` instance; returns payload/metadata/notes."""
    job_count = _header_int(text, r"jobs \(incl\. supersource/sink \)", file_label)
    horizon = _header_int(text, r"horizon", file_label)
    for label in ("nonrenewable", "doubly constrained"):
        if _header_int(text, rf"\s*- {re.escape(label)}", file_label) != 0:
            raise NativeFormatError(
                f"{file_label}: declares unsupported {label} resources"
            )

    successors = _precedence_rows(text, job_count, file_label)
    requests = _request_rows(text, job_count, file_label)
    capacities = _capacities(text, file_label)
    resource_ids = [f"R{index + 1}" for index in range(len(capacities))]

    for dummy in (1, job_count):
        duration, demands = requests[dummy]
        if duration != 0 or any(demands):
            raise NativeFormatError(
                f"{file_label}: dummy job {dummy} is not zero-valued"
            )

    def activity_id(jobnr: int) -> str:
        return f"j{jobnr}"

    activities = []
    precedences = []
    for jobnr in range(2, job_count):
        duration, demands = requests[jobnr]
        activities.append(
            {
                "id": activity_id(jobnr),
                "duration_days": duration,
                "resources": dict(zip(resource_ids, demands, strict=True)),
            }
        )
        for successor in successors[jobnr]:
            if successor == job_count:
                continue
            precedences.append(
                {
                    "predecessor": activity_id(jobnr),
                    "successor": activity_id(successor),
                }
            )

    payload = {
        "profile": "RCPSP",
        "job_intent": "optimize",
        "resources": {
            resource_id: {"capacity": capacity}
            for resource_id, capacity in zip(resource_ids, capacities, strict=True)
        },
        "activities": activities,
        "precedences": precedences,
        "objectives": {"primary": "minimize_makespan"},
    }
    metadata = SmMetadata(
        horizon=horizon,
        job_count=job_count,
        resource_count=len(capacities),
    )
    notes = (
        "dialect: PSPLIB single-mode, renewable resources only",
        f"{job_count} jobs (dummies dropped), horizon {horizon}",
        "activity ids keep PSPLIB job numbers (j2..)",
    )
    return {"payload": payload, "metadata": metadata, "notes": notes}


def _header_int(text: str, label: str, file_label: str) -> int:
    match = re.search(rf"(?im)^{label}\s*:\s*(\d+)", text)
    if match is None:
        raise NativeFormatError(f"{file_label}: missing PSPLIB header {label!r}")
    return int(match.group(1))


def _precedence_rows(
    text: str, job_count: int, file_label: str
) -> dict[int, tuple[int, ...]]:
    section = re.search(
        r"(?ims)^PRECEDENCE RELATIONS:\s*(.*?)^REQUESTS/DURATIONS:", text
    )
    if section is None:
        raise NativeFormatError(f"{file_label}: missing PSPLIB precedence section")
    rows: dict[int, tuple[int, ...]] = {}
    for line in section.group(1).splitlines():
        tokens = line.split()
        if not tokens or not tokens[0].isdigit():
            continue
        jobnr, modes, successor_count, *successor_ids = (
            int(token) for token in tokens
        )
        if modes != 1 or successor_count != len(successor_ids):
            raise NativeFormatError(
                f"{file_label}: malformed PSPLIB precedence row: {line!r}"
            )
        rows[jobnr] = tuple(successor_ids)
    if sorted(rows) != list(range(1, job_count + 1)):
        raise NativeFormatError(
            f"{file_label}: PSPLIB precedence rows do not cover every job"
        )
    return rows


def _request_rows(
    text: str, job_count: int, file_label: str
) -> dict[int, tuple[int, tuple[int, ...]]]:
    section = re.search(
        r"(?ims)^REQUESTS/DURATIONS:\s*(.*?)^RESOURCEAVAILABILITIES:", text
    )
    if section is None:
        raise NativeFormatError(f"{file_label}: missing PSPLIB requests section")
    rows: dict[int, tuple[int, tuple[int, ...]]] = {}
    for line in section.group(1).splitlines():
        tokens = line.split()
        if not tokens or not tokens[0].isdigit():
            continue
        jobnr, mode, duration, *demands = (int(token) for token in tokens)
        if mode != 1:
            raise NativeFormatError(
                f"{file_label}: malformed PSPLIB request row: {line!r}"
            )
        rows[jobnr] = (duration, tuple(demands))
    if sorted(rows) != list(range(1, job_count + 1)):
        raise NativeFormatError(
            f"{file_label}: PSPLIB request rows do not cover every job"
        )
    return rows


def _capacities(text: str, file_label: str) -> tuple[int, ...]:
    section = re.search(r"(?ims)^RESOURCEAVAILABILITIES:\s*(.*?)^\*{5,}", text)
    if section is None:
        raise NativeFormatError(f"{file_label}: missing PSPLIB availability section")
    rows = [
        tuple(int(token) for token in line.split())
        for line in section.group(1).splitlines()
        if line.split() and line.split()[0].lstrip("-").isdigit()
    ]
    if len(rows) != 1:
        raise NativeFormatError(
            f"{file_label}: PSPLIB availability section must be a single row"
        )
    return rows[0]


"""Taillard job-shop files → canonical `4.2.scheduling.jssp` payloads.

A Taillard file may hold several instances; translation targets one
(`instance_index`, default 0). Machine numbers convert from Taillard's
1-based ids to canonical `m0..m(k-1)`; jobs become `j0..j(n-1)`.
"""


from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaillardInstance:
    job_count: int
    machine_count: int
    time_seed: int
    machine_seed: int
    upper_bound: int
    lower_bound: int
    durations: tuple[tuple[int, ...], ...]
    machines: tuple[tuple[int, ...], ...]


def parse_taillard(text: str, *, file_label: str = "input.txt") -> tuple[TaillardInstance, ...]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cursor = 0
    records: list[TaillardInstance] = []
    while cursor < len(lines):
        if not lines[cursor].startswith("Nb of jobs, Nb of Machines"):
            raise NativeFormatError(f"{file_label}: invalid Taillard header")
        cursor += 1
        try:
            job_count, machine_count, time_seed, machine_seed, upper, lower = map(
                int, lines[cursor].split()
            )
        except (IndexError, ValueError) as exc:
            raise NativeFormatError(f"{file_label}: invalid instance header") from exc
        cursor += 1
        if cursor >= len(lines) or lines[cursor] != "Times":
            raise NativeFormatError(f"{file_label}: missing duration matrix")
        cursor += 1
        durations, cursor = _matrix(lines, cursor, job_count, machine_count, file_label)
        if cursor >= len(lines) or lines[cursor] != "Machines":
            raise NativeFormatError(f"{file_label}: missing machine matrix")
        cursor += 1
        machines, cursor = _matrix(lines, cursor, job_count, machine_count, file_label)
        expected_machines = set(range(1, machine_count + 1))
        for job_index, machine_row in enumerate(machines):
            if set(machine_row) != expected_machines:
                raise NativeFormatError(
                    f"{file_label}: job {job_index + 1} machine row must be a "
                    f"permutation of 1..{machine_count}"
                )
        records.append(
            TaillardInstance(
                job_count=job_count,
                machine_count=machine_count,
                time_seed=time_seed,
                machine_seed=machine_seed,
                upper_bound=upper,
                lower_bound=lower,
                durations=durations,
                machines=machines,
            )
        )
    if not records:
        raise NativeFormatError(f"{file_label}: no Taillard instances found")
    return tuple(records)


def _matrix(
    lines: list[str], cursor: int, rows: int, columns: int, file_label: str
) -> tuple[tuple[tuple[int, ...], ...], int]:
    matrix: list[tuple[int, ...]] = []
    for _ in range(rows):
        if cursor >= len(lines):
            raise NativeFormatError(f"{file_label}: file ends inside a matrix")
        try:
            values = tuple(map(int, lines[cursor].split()))
        except ValueError as exc:
            raise NativeFormatError(f"{file_label}: non-integer matrix value") from exc
        if len(values) != columns:
            raise NativeFormatError(f"{file_label}: malformed matrix row")
        matrix.append(values)
        cursor += 1
    return tuple(matrix), cursor


def payload_from_instance(record: TaillardInstance) -> dict[str, Any]:
    return {
        "machines": [f"m{machine}" for machine in range(record.machine_count)],
        "jobs": [
            {
                "id": f"j{index}",
                "operations": [
                    {"machine_id": f"m{machine - 1}", "duration_days": duration}
                    for machine, duration in zip(machine_row, duration_row, strict=True)
                ],
            }
            for index, (machine_row, duration_row) in enumerate(
                zip(record.machines, record.durations, strict=True)
            )
        ],
        "objectives": {"primary": "minimize_makespan"},
    }


def convert_taillard(
    text: str, *, instance_index: int = 0, file_label: str = "input.txt"
) -> dict[str, Any]:
    """Translate one instance from a Taillard file; returns payload/notes."""
    records = parse_taillard(text, file_label=file_label)
    if not 0 <= instance_index < len(records):
        raise NativeFormatError(
            f"{file_label}: instance index {instance_index} out of range "
            f"(file holds {len(records)} instances)"
        )
    record = records[instance_index]
    notes = (
        f"dialect: Taillard JSSP ({record.job_count} jobs x {record.machine_count} machines)",
        f"instance {instance_index} of {len(records)} in file",
        "machine ids converted from 1-based to m0..; published bounds "
        f"UB={record.upper_bound} LB={record.lower_bound} recorded here only",
    )
    return {
        "payload": payload_from_instance(record),
        "node_numbering": None,
        "notes": notes,
    }


"""Native-format detection by extension, then header sniffing."""


import gzip
import re
from pathlib import Path


FORMAT_TSPLIB = "tsplib"
FORMAT_CVRPLIB = "cvrplib"
FORMAT_MPS = "mps"
FORMAT_PSPLIB_SM = "psplib-sm"
FORMAT_TAILLARD = "taillard"

_EXTENSIONS = {
    ".tsp": FORMAT_TSPLIB,
    ".atsp": FORMAT_TSPLIB,
    ".vrp": FORMAT_CVRPLIB,
    ".mps": FORMAT_MPS,
    ".sm": FORMAT_PSPLIB_SM,
}


def detect_format(path: str | Path, head: bytes | None = None) -> str:
    """Return the format id for a native file; sniff headers when needed."""
    file_path = Path(path)
    suffixes = [suffix.lower() for suffix in file_path.suffixes]
    if suffixes and suffixes[-1] == ".gz" and len(suffixes) >= 2:
        if suffixes[-2] == ".mps":
            return FORMAT_MPS
    if suffixes and suffixes[-1] in _EXTENSIONS:
        return _EXTENSIONS[suffixes[-1]]

    if head is None:
        with file_path.open("rb") as handle:
            head = handle.read(65536)
    if head[:2] == b"\x1f\x8b":
        head = gzip.decompress(head[: 1 << 20])[:65536]
    try:
        text = head.decode("utf-8", errors="replace")
    except Exception as exc:  # pragma: no cover - decode with replace cannot raise
        raise NativeFormatError(f"{file_path.name}: unreadable file head") from exc

    type_match = re.search(r"(?im)^TYPE\s*:\s*(\w+)", text)
    if type_match:
        declared = type_match.group(1).upper()
        if declared in {"TSP", "ATSP"}:
            return FORMAT_TSPLIB
        if declared == "CVRP":
            return FORMAT_CVRPLIB
    if "Nb of jobs, Nb of Machines" in text:
        return FORMAT_TAILLARD
    if "jobs (incl. supersource/sink" in text:
        return FORMAT_PSPLIB_SM
    if re.search(r"(?m)^NAME\b", text) and re.search(r"(?m)^ROWS\b", text):
        return FORMAT_MPS
    raise NativeFormatError(
        f"{file_path.name}: format not recognized; supported formats are "
        "tsplib (.tsp/.atsp), cvrplib (.vrp), mps (.mps[.gz]), "
        "psplib-sm (.sm), taillard"
    )


INPUT_SCHEMA_VERSIONS = {
    "1.1.tsp": "1.1.tsp.input.v1",
    "1.2.vrp.cvrp": "1.2.vrp.cvrp.input.v4",
    "2.1.lp": "2.1.lp.input.v2",
    "2.2.milp": "2.2.milp.input.v2",
    "4.1.scheduling.rcpsp": "4.1.scheduling.rcpsp.input.v3",
    "4.2.scheduling.jssp": "4.2.scheduling.jssp.input.v3",
}

_FORMAT_PROBLEM_TYPES = {
    FORMAT_TSPLIB: "1.1.tsp",
    FORMAT_CVRPLIB: "1.2.vrp.cvrp",
    FORMAT_PSPLIB_SM: "4.1.scheduling.rcpsp",
    FORMAT_TAILLARD: "4.2.scheduling.jssp",
}


def translate_native(
    path: str | Path,
    *,
    format_id: str | None = None,
    vehicle_count: int | None = None,
    instance_index: int = 0,
) -> dict[str, Any]:
    """Translate one native file into a canonical submission document."""
    file_path = Path(path)
    data = file_path.read_bytes()
    resolved_format = format_id or detect_format(file_path, data[:65536])
    file_label = file_path.name

    if resolved_format == FORMAT_TSPLIB:
        text = data.decode("latin-1")
        is_atsp = file_path.suffix.lower() == ".atsp" or bool(
            re.search(r"(?im)^TYPE\s*:\s*ATSP\b", text)
        )
        converted = (
            convert_atsp(text, file_label=file_label)
            if is_atsp
            else convert_tsp(text, file_label=file_label)
        )
        problem_type = _FORMAT_PROBLEM_TYPES[FORMAT_TSPLIB]
    elif resolved_format == FORMAT_CVRPLIB:
        converted = convert_vrp(
            data.decode("latin-1"),
            vehicle_count=vehicle_count,
            file_label=file_label,
        )
        problem_type = _FORMAT_PROBLEM_TYPES[FORMAT_CVRPLIB]
    elif resolved_format == FORMAT_MPS:
        converted = convert_mps(data, file_label=file_label)
        problem_type = str(converted["problem_type"])
    elif resolved_format == FORMAT_PSPLIB_SM:
        converted = convert_sm(data.decode("latin-1"), file_label=file_label)
        converted["node_numbering"] = None
        problem_type = _FORMAT_PROBLEM_TYPES[FORMAT_PSPLIB_SM]
    elif resolved_format == FORMAT_TAILLARD:
        converted = convert_taillard(
            data.decode("utf-8"),
            instance_index=instance_index,
            file_label=file_label,
        )
        problem_type = _FORMAT_PROBLEM_TYPES[FORMAT_TAILLARD]
    else:
        raise NativeFormatError(f"unknown format id {resolved_format!r}")

    numbering = converted.get("node_numbering")
    return {
        "problem_type": problem_type,
        "problem_schema_version": INPUT_SCHEMA_VERSIONS[problem_type],
        "payload": converted["payload"],
        "node_numbering": list(numbering) if numbering else None,
        "notes": list(converted["notes"]),
        "format_id": resolved_format,
        "source_file": file_label,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Translate native optimization files into canonical AgentSolve "
            "input. Canonical documents land in the working directory by "
            "default (or --out-dir), never beside the instance files."
        )
    )
    parser.add_argument(
        "instances", nargs="+", type=Path, help="native instance file(s)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output JSON path (single instance only)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="directory for canonical documents (default: working directory)",
    )
    parser.add_argument(
        "--format",
        dest="format_id",
        choices=[FORMAT_TSPLIB, FORMAT_CVRPLIB, FORMAT_MPS, FORMAT_PSPLIB_SM, FORMAT_TAILLARD],
        default=None,
        help="override format detection",
    )
    parser.add_argument(
        "--vehicle-count",
        type=int,
        default=None,
        help="CVRPLIB vehicle count when the file does not declare one",
    )
    parser.add_argument(
        "--instance-index",
        type=int,
        default=0,
        help="which instance to take from a multi-instance Taillard file",
    )
    args = parser.parse_args()
    if args.out is not None and len(args.instances) > 1:
        print("translate: --out takes a single instance; use --out-dir", file=sys.stderr)
        return 2
    if args.out is not None and args.out_dir is not None:
        print("translate: pass --out or --out-dir, not both", file=sys.stderr)
        return 2
    out_dir = args.out_dir if args.out_dir is not None else Path.cwd()
    summaries = []
    failed = False
    for instance in args.instances:
        try:
            result = translate_native(
                instance,
                format_id=args.format_id,
                vehicle_count=args.vehicle_count,
                instance_index=args.instance_index,
            )
        except (NativeFormatError, OSError) as exc:
            print(f"translate: {instance}: {exc}", file=sys.stderr)
            failed = True
            continue
        if args.out is not None:
            out_path = args.out
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / (instance.name + ".canonical.json")
        out_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        summaries.append(
            {
                "written": str(out_path),
                "problem_type": result["problem_type"],
                "problem_schema_version": result["problem_schema_version"],
                "notes": result["notes"],
            }
        )
    printable = summaries[0] if len(args.instances) == 1 and summaries else summaries
    if summaries:
        print(json.dumps(printable, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
