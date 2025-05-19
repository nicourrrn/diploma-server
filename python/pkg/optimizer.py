import numpy as np
from scipy.optimize import linear_sum_assignment
from pkg.models import Requirement, RequirementWithVolonteer, Volunteer


def optimize_requirement_assignment(
    requirements: list[RequirementWithVolonteer],
    volunteers: list[Volunteer],
    max_capacity: int = 3,
) -> dict[str, list[str]] | None:
    num_req = len(requirements)
    num_vol = len(volunteers)
    cost_matrix = np.zeros((num_vol, num_req))
    for i, volunteer in enumerate(volunteers):
        for j, requirement in enumerate(requirements):
            cost = 0
            current_load = len([r for r in requirements if r.volunteer == volunteer.id])
            cost += current_load * 2
            if volunteer.rating:
                cost -= volunteer.rating * 0.3
            if requirement.priority == "High":
                cost -= 3
            cost_matrix[i][j] = cost
    cost_matrix = (cost_matrix - cost_matrix.min()) / (
        cost_matrix.max() - cost_matrix.min()
    )
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    assignment = {volunteer.id: [] for volunteer in volunteers}
    load_counter = {volunteer.id: 0 for volunteer in volunteers}
    for vol_idx, req_idx in zip(row_ind, col_ind):
        volunteer = volunteers[vol_idx]
        requirement = requirements[req_idx]

        if load_counter[volunteer.id] < max_capacity:
            assignment[volunteer.id].append(requirement.id)
            load_counter[volunteer.id] += 1
    unassigned = [
        r.id for r in requirements if not any(r.id in v for v in assignment.values())
    ]
    for req_id in unassigned:
        min_volunteer = min(volunteers, key=lambda v: load_counter[v.id])
        if load_counter[min_volunteer.id] < max_capacity:
            assignment[min_volunteer.id].append(req_id)
            load_counter[min_volunteer.id] += 1
    return assignment
