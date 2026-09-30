"""
solver.py — N-Puzzle Solver Algorithms
=======================================
Contains implementations of:
  1. Breadth-First Search (BFS)       — uninformed, brute-force baseline
  2. A* Search                        — informed search with Manhattan Distance
                                        + Linear Conflict heuristic

The module is parameterized by `board_size` (default 3 for the 8-puzzle)
so that adding 4×4 (15-puzzle) support later requires no structural changes.
"""

from __future__ import annotations

import heapq
import time
from collections import deque
from typing import Optional


# ---------------------------------------------------------------------------
# 1.  SOLVABILITY CHECK
# ---------------------------------------------------------------------------

def count_inversions(state: list[int]) -> int:
    """
    Count the number of inversions in the puzzle state.

    An *inversion* is any pair (a, b) where a appears before b in the
    flattened array, a ≠ 0, b ≠ 0, and a > b.

    For a 3×3 puzzle the state is solvable ⟺ inversions are EVEN.
    (For 4×4 the rule also involves the blank's row — to be added later.)

    Time complexity: O(n²) where n = board_size² — acceptable for small boards.
    """
    inversions = 0
    for i in range(len(state)):
        if state[i] == 0:
            continue  # skip the blank tile
        for j in range(i + 1, len(state)):
            if state[j] == 0:
                continue
            if state[i] > state[j]:
                inversions += 1
    return inversions


def is_solvable(state: list[int], board_size: int = 3) -> bool:
    """
    Determine whether a given board state can reach the goal.

    For an odd-width board (e.g. 3×3):
        solvable ⟺ number of inversions is even.

    For an even-width board (e.g. 4×4):
        solvable ⟺ (inversions + row of blank from bottom) is even.
        (Stub — not yet implemented for 4×4.)
    """
    inversions = count_inversions(state)

    if board_size % 2 == 1:
        # Odd-width board: solvable when inversions are even
        return inversions % 2 == 0
    else:
        # Even-width board (placeholder for future 4×4 support)
        blank_index = state.index(0)
        blank_row_from_bottom = board_size - (blank_index // board_size)
        return (inversions + blank_row_from_bottom) % 2 == 0


# ---------------------------------------------------------------------------
# 2.  GOAL STATE BUILDER
# ---------------------------------------------------------------------------

def build_goal(board_size: int = 3) -> tuple[int, ...]:
    """
    Build the canonical goal state for a board of the given size.
    Example for 3×3:  (1, 2, 3, 4, 5, 6, 7, 8, 0)
    """
    n = board_size * board_size
    return tuple(list(range(1, n)) + [0])


# ---------------------------------------------------------------------------
# 3.  NEIGHBOUR GENERATION
# ---------------------------------------------------------------------------

def get_neighbors(state: tuple[int, ...], board_size: int = 3) -> list[tuple[int, ...]]:
    """
    Generate all valid successor states by sliding one tile into the blank.

    The blank (0) can swap with tiles directly above, below, left, or right
    of it — as long as the swap stays within the grid boundaries.

    Returns a list of new state tuples.
    """
    n = board_size * board_size
    blank = state.index(0)
    row, col = divmod(blank, board_size)

    neighbors = []

    # (delta_row, delta_col) for Up, Down, Left, Right
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < board_size and 0 <= nc < board_size:
            new_blank = nr * board_size + nc
            # Swap the blank with the adjacent tile
            lst = list(state)
            lst[blank], lst[new_blank] = lst[new_blank], lst[blank]
            neighbors.append(tuple(lst))

    return neighbors


# ---------------------------------------------------------------------------
# 4.  HEURISTIC FUNCTIONS
# ---------------------------------------------------------------------------

def manhattan_distance(state: tuple[int, ...], board_size: int = 3) -> int:
    """
    Compute the Manhattan Distance heuristic.

    For each tile (except the blank), calculate the sum of:
        |current_row − goal_row| + |current_col − goal_col|

    This is *admissible* (never overestimates) and *consistent*.
    """
    distance = 0
    for index, tile in enumerate(state):
        if tile == 0:
            continue  # don't count the blank
        # Where the tile currently is
        current_row, current_col = divmod(index, board_size)
        # Where the tile should be in the goal  (tile 1 → index 0, etc.)
        goal_index = tile - 1
        goal_row, goal_col = divmod(goal_index, board_size)
        distance += abs(current_row - goal_row) + abs(current_col - goal_col)
    return distance


def linear_conflict(state: tuple[int, ...], board_size: int = 3) -> int:
    """
    Compute the Linear Conflict heuristic *add-on*.

    Two tiles are in *linear conflict* if:
      1. Both tiles are in their goal row (or column).
      2. One tile must pass over the other to reach its goal position.

    Each such conflict adds at least 2 extra moves beyond what Manhattan
    Distance accounts for, because one tile must leave the row/column and
    come back.

    This function returns ONLY the linear-conflict penalty (to be added
    to Manhattan Distance), making the combined heuristic:
        h(n) = manhattan_distance(n) + linear_conflict(n)

    The combined heuristic is still admissible and consistent.
    """
    conflict = 0

    # --- Row conflicts ---
    for row in range(board_size):
        for col_a in range(board_size):
            tile_a = state[row * board_size + col_a]
            if tile_a == 0:
                continue
            # Check if tile_a's goal row is this row
            goal_row_a = (tile_a - 1) // board_size
            if goal_row_a != row:
                continue
            for col_b in range(col_a + 1, board_size):
                tile_b = state[row * board_size + col_b]
                if tile_b == 0:
                    continue
                goal_row_b = (tile_b - 1) // board_size
                if goal_row_b != row:
                    continue
                # Both tiles belong in this row.
                # Conflict if tile_a's goal column > tile_b's goal column
                # (i.e. tile_a is to the LEFT of tile_b now, but should be
                #  to the RIGHT in the goal — they must cross each other).
                goal_col_a = (tile_a - 1) % board_size
                goal_col_b = (tile_b - 1) % board_size
                if goal_col_a > goal_col_b:
                    conflict += 2  # each conflict adds 2 moves

    # --- Column conflicts ---
    for col in range(board_size):
        for row_a in range(board_size):
            tile_a = state[row_a * board_size + col]
            if tile_a == 0:
                continue
            goal_col_a = (tile_a - 1) % board_size
            if goal_col_a != col:
                continue
            for row_b in range(row_a + 1, board_size):
                tile_b = state[row_b * board_size + col]
                if tile_b == 0:
                    continue
                goal_col_b = (tile_b - 1) % board_size
                if goal_col_b != col:
                    continue
                goal_row_a = (tile_a - 1) // board_size
                goal_row_b = (tile_b - 1) // board_size
                if goal_row_a > goal_row_b:
                    conflict += 2

    return conflict


def heuristic(state: tuple[int, ...], board_size: int = 3) -> int:
    """Combined admissible heuristic: Manhattan Distance + Linear Conflict."""
    return manhattan_distance(state, board_size) + linear_conflict(state, board_size)


# ---------------------------------------------------------------------------
# 5.  PATH RECONSTRUCTION HELPER
# ---------------------------------------------------------------------------

def reconstruct_path(
    came_from: dict[tuple[int, ...], Optional[tuple[int, ...]]],
    current: tuple[int, ...],
) -> list[list[int]]:
    """
    Walk backwards through the `came_from` map from `current` to the start
    and return the full path as a list of states (each state is a plain list
    so it serializes nicely to JSON).
    """
    path: list[list[int]] = []
    while current is not None:
        path.append(list(current))
        current = came_from[current]
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# 6.  BFS SOLVER
# ---------------------------------------------------------------------------

def solve_bfs(
    initial_state: list[int],
    board_size: int = 3,
) -> dict:
    """
    Solve the puzzle using Breadth-First Search (BFS).

    BFS explores nodes level-by-level, guaranteeing the shortest path in
    terms of number of moves.  However, it is uninformed (uses no heuristic)
    so it expands many more nodes than A*.

    Returns a dict with:
        - path:          list of board states from start to goal
        - moves:         number of moves in the solution
        - nodes_expanded: total nodes popped from the queue
        - time_taken:    wall-clock seconds
    """
    start_tuple = tuple(initial_state)
    goal = build_goal(board_size)

    # Edge case: already solved
    if start_tuple == goal:
        return {
            "path": [list(start_tuple)],
            "moves": 0,
            "nodes_expanded": 0,
            "time_taken": 0.0,
        }

    t0 = time.perf_counter()

    # `came_from` stores the parent of each visited state (None for start)
    came_from: dict[tuple[int, ...], Optional[tuple[int, ...]]] = {start_tuple: None}

    # Standard BFS queue
    queue: deque[tuple[int, ...]] = deque([start_tuple])
    nodes_expanded = 0

    while queue:
        current = queue.popleft()
        nodes_expanded += 1

        for neighbor in get_neighbors(current, board_size):
            if neighbor in came_from:
                continue  # already visited
            came_from[neighbor] = current

            if neighbor == goal:
                # Found the goal — reconstruct and return
                path = reconstruct_path(came_from, neighbor)
                elapsed = time.perf_counter() - t0
                return {
                    "path": path,
                    "moves": len(path) - 1,
                    "nodes_expanded": nodes_expanded,
                    "time_taken": round(elapsed, 4),
                }

            queue.append(neighbor)

    # Should never reach here if solvability was checked first
    return {"error": "No solution found (should not happen for a solvable state)."}


# ---------------------------------------------------------------------------
# 7.  A* SOLVER
# ---------------------------------------------------------------------------

def solve_astar(
    initial_state: list[int],
    board_size: int = 3,
) -> dict:
    """
    Solve the puzzle using A* Search with Manhattan Distance + Linear Conflict.

    A* maintains a priority queue ordered by f(n) = g(n) + h(n):
        - g(n) = number of moves so far (cost from start)
        - h(n) = heuristic estimate of remaining cost

    Because our heuristic is admissible and consistent, A* is guaranteed to
    find an optimal (shortest) solution while expanding far fewer nodes than BFS.

    Returns a dict with:
        - path:           list of board states from start to goal
        - moves:          number of moves in the solution
        - nodes_expanded: total nodes popped from the priority queue
        - time_taken:     wall-clock seconds
    """
    start_tuple = tuple(initial_state)
    goal = build_goal(board_size)

    # Edge case: already solved
    if start_tuple == goal:
        return {
            "path": [list(start_tuple)],
            "moves": 0,
            "nodes_expanded": 0,
            "time_taken": 0.0,
        }

    t0 = time.perf_counter()

    # Priority queue entries: (f_score, tie_breaker, state)
    # The tie_breaker (a counter) ensures FIFO ordering when f scores are equal,
    # preventing tuple-comparison errors on the state.
    counter = 0
    open_set: list[tuple[int, int, tuple[int, ...]]] = []
    h_start = heuristic(start_tuple, board_size)
    heapq.heappush(open_set, (h_start, counter, start_tuple))

    # g_score[state] = cost of cheapest path from start to state found so far
    g_score: dict[tuple[int, ...], int] = {start_tuple: 0}

    # came_from[state] = predecessor on the cheapest path
    came_from: dict[tuple[int, ...], Optional[tuple[int, ...]]] = {start_tuple: None}

    # Track which states have already been expanded (closed set)
    closed: set[tuple[int, ...]] = set()

    nodes_expanded = 0

    while open_set:
        f, _, current = heapq.heappop(open_set)

        # Skip if we already expanded this state via a cheaper path
        if current in closed:
            continue

        closed.add(current)
        nodes_expanded += 1

        # Goal test (done at expansion time for correctness with consistent h)
        if current == goal:
            path = reconstruct_path(came_from, current)
            elapsed = time.perf_counter() - t0
            return {
                "path": path,
                "moves": len(path) - 1,
                "nodes_expanded": nodes_expanded,
                "time_taken": round(elapsed, 4),
            }

        current_g = g_score[current]

        for neighbor in get_neighbors(current, board_size):
            if neighbor in closed:
                continue

            tentative_g = current_g + 1  # each move costs 1

            # Only process if this is a new or cheaper path to `neighbor`
            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                f_score = tentative_g + heuristic(neighbor, board_size)
                counter += 1
                heapq.heappush(open_set, (f_score, counter, neighbor))

    return {"error": "No solution found (should not happen for a solvable state)."}
