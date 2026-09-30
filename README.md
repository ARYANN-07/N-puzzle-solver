# 🧩 N-Puzzle Solver

A web application that visually demonstrates **BFS** and **A\*** search algorithms solving the classic **8-puzzle** (3×3 slider puzzle).

---

## 📁 Project Structure

```
SliderPuzzleSolver/
├── backend/
│   ├── main.py              # FastAPI server — API endpoint, validation, CORS
│   ├── solver.py            # Algorithm implementations (BFS, A*, heuristics)
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Page structure
│   ├── style.css            # Design system — dark glassmorphic theme
│   └── app.js               # Puzzle logic, user interaction, animation
└── README.md                # This file
```

---

## 🚀 How to Run

### 1. Backend (Python / FastAPI)

```bash
# Navigate to the backend folder
cd backend

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at **http://127.0.0.1:8000**.  
Docs at **http://127.0.0.1:8000/docs** (Swagger UI).

### 2. Frontend (Static Files)

Open `frontend/index.html` directly in a browser, **or** serve it with any static server:

```bash
# Option A: Python's built-in server
cd frontend
python -m http.server 5500

# Option B: VS Code Live Server extension
# Right-click index.html → "Open with Live Server"
```

Then open **http://localhost:5500** in your browser.

---

## 🎮 Usage

1. **Scramble** the puzzle by clicking tiles adjacent to the blank, or hit **Shuffle**.
2. **Select** an algorithm — A\* (fast, informed) or BFS (brute-force baseline).
3. **Hit Solve** — the backend finds the optimal solution and returns it.
4. **Watch** the tiles animate step-by-step to the goal state.
5. **Compare** the stats (moves, nodes expanded, time) between A\* and BFS.

---

## 📊 Algorithms

| Algorithm | Type | Heuristic | Optimal? | Typical Nodes |
|-----------|------|-----------|----------|---------------|
| **BFS** | Uninformed | None | ✅ | ~100k+ |
| **A\*** | Informed | Manhattan Distance + Linear Conflict | ✅ | ~100–2k |

### Manhattan Distance
Sum of each tile's horizontal and vertical distance from its goal position.

### Linear Conflict
Adds a penalty when two tiles are in their goal row/column but in the wrong relative order — each conflict requires at least 2 extra moves beyond Manhattan Distance.

---

## 🔧 Extending to 4×4 (15-Puzzle)

The code is designed to be modular:
- `solver.py` accepts a `board_size` parameter — all functions work for any size.
- `main.py` forwards the `board_size` from the request body.
- The frontend's `BOARD_SIZE` constant and CSS `--tile-size` are the only things to change.

---

## 📄 License

MIT — free for academic and personal use.
