"""
main.py — FastAPI Backend for the N-Puzzle Solver
===================================================
Provides a single REST endpoint:

    POST /api/solve
        Body:  { "state": [1,2,3,4,0,5,6,7,8], "algorithm": "astar" }
        Returns: { "path": [...], "moves": 5, "nodes_expanded": 12, "time_taken": 0.002 }

CORS is configured to allow the frontend (served separately) to make requests.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from solver import is_solvable, solve_bfs, solve_astar

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="N-Puzzle Solver API",
    description="Solve the 8-puzzle (and later 15-puzzle) with BFS or A*.",
    version="1.0.0",
)

# Allow any origin for local development.
# In production you'd lock this down to your frontend's domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class SolveRequest(BaseModel):
    """
    JSON body sent by the frontend.

    Fields:
        state      – 1D list representing the board (0 = blank).
                     For 3×3 this is 9 elements; for 4×4 it would be 16.
        algorithm  – "bfs" or "astar"
        board_size – width of the board (default 3)
    """
    state: list[int]
    algorithm: str = "astar"
    board_size: int = 3

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("bfs", "astar"):
            raise ValueError("algorithm must be 'bfs' or 'astar'")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: list[int]) -> list[int]:
        # Basic sanity — full validation below uses board_size
        if not v:
            raise ValueError("state must not be empty")
        return v


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/solve")
async def solve(req: SolveRequest):
    """
    Main solve endpoint.

    Steps:
        1. Validate the board state (correct length, correct tile values).
        2. Check solvability via inversion counting.
        3. Dispatch to the chosen algorithm.
        4. Return the solution path, statistics, or an error.
    """
    n = req.board_size
    expected_length = n * n

    # --- Validate tile count ---
    if len(req.state) != expected_length:
        raise HTTPException(
            status_code=400,
            detail=f"State must have exactly {expected_length} elements for a {n}×{n} board.",
        )

    # --- Validate tile values ---
    expected_tiles = set(range(expected_length))
    if set(req.state) != expected_tiles:
        raise HTTPException(
            status_code=400,
            detail=f"State must contain each number from 0 to {expected_length - 1} exactly once.",
        )

    # --- Solvability check ---
    if not is_solvable(req.state, req.board_size):
        raise HTTPException(
            status_code=400,
            detail=(
                "This board configuration is unsolvable. "
                f"Inversion count is odd (must be even for a {n}×{n} board)."
            ),
        )

    # --- Dispatch to solver ---
    if req.algorithm == "bfs":
        result = solve_bfs(req.state, req.board_size)
    else:
        result = solve_astar(req.state, req.board_size)

    # --- Handle unexpected solver errors ---
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@app.get("/api/health")
async def health():
    """Simple health-check endpoint."""
    return {"status": "ok"}
