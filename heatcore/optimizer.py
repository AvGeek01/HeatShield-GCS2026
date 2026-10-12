"""City-scale heat intervention optimization interfaces."""

from collections.abc import Sequence
from typing import TypedDict


class HeatmapCell(TypedDict):
    """Heat and exposure properties associated with a GeoJSON heatmap cell."""

    risk: float
    temp_c: float
    wbgt_c: float
    population_exposed: int


class InterventionPlan(TypedDict):
    """Selected intervention locations and aggregate optimization outputs."""

    selected_cells: list[int]
    population_reached: int
    budget_used: float


def optimize_interventions(
    cells: Sequence[HeatmapCell],
    *,
    budget: float,
    cost_per_cell: float,
) -> InterventionPlan:
    """Select heatmap cells for interventions under a fixed budget.

    Args:
        cells: Cells carrying the ``risk``, ``temp_c``, ``wbgt_c``, and
            ``population_exposed`` fields exposed by ``/api/heatmap``.
        budget: Available intervention budget in the caller's currency.
        cost_per_cell: Estimated intervention cost for each selected cell.

    Returns:
        Selected cell indices, total population reached, and budget used.
    """
    raise NotImplementedError
