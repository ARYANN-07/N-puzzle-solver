/**
 * app.js — N-Puzzle Solver Frontend Logic
 * =========================================
 *
 * Responsibilities:
 *   1. Render the 3×3 puzzle grid with absolutely-positioned tiles.
 *   2. Handle user clicks to slide tiles (manual scrambling).
 *   3. Provide a "Shuffle" button for quick random scrambling.
 *   4. Send the current state to the backend API and display the solution.
 *   5. Animate the solution path step-by-step with smooth CSS transitions.
 *
 * The code is structured around a single `PuzzleSolver` class that
 * encapsulates all state and DOM interactions.
 */

// ─── Configuration ─────────────────────────────────────────────────────────

const API_BASE = "http://127.0.0.1:8000";   // Backend URL
const BOARD_SIZE = 3;                        // 3×3 for the 8-puzzle
const TOTAL_TILES = BOARD_SIZE * BOARD_SIZE;  // 9

/**
 * The solved (goal) state.
 * Tiles 1–8 in reading order, 0 (blank) at the end.
 */
const GOAL_STATE = [...Array(TOTAL_TILES - 1).keys()].map(i => i + 1).concat(0);
// → [1, 2, 3, 4, 5, 6, 7, 8, 0]


// ─── PuzzleSolver Class ────────────────────────────────────────────────────

class PuzzleSolver {
  constructor() {
    /**
     * `this.state` is a 1D array of length 9, mirroring the flattened grid.
     * Index 0 → row 0, col 0   |  Index 1 → row 0, col 1  ...
     * The value 0 represents the blank tile.
     */
    this.state = [...GOAL_STATE];

    /** True while the solve animation is playing — disables user interaction. */
    this.isAnimating = false;

    /** Handle returned by setTimeout — lets us cancel mid-animation. */
    this.animationTimer = null;

    // Grab DOM references
    this.grid       = document.getElementById("puzzle-grid");
    this.btnSolve   = document.getElementById("btn-solve");
    this.btnReset   = document.getElementById("btn-reset");
    this.btnShuffle = document.getElementById("btn-shuffle");
    this.algoSelect = document.getElementById("algo-select");
    this.speedSlider = document.getElementById("speed-slider");
    this.statusBar  = document.getElementById("status-bar");
    this.hintText   = document.getElementById("hint-text");
    this.statsCard  = document.getElementById("stats-card");
    this.moveCounter = document.getElementById("move-counter");
    this.currentStep = document.getElementById("current-step");
    this.totalSteps  = document.getElementById("total-steps");

    // Stat value elements
    this.statMoves = document.getElementById("stat-moves");
    this.statNodes = document.getElementById("stat-nodes");
    this.statTime  = document.getElementById("stat-time");
    this.statAlgo  = document.getElementById("stat-algo");

    // Build tile DOM elements and bind events
    this._createTiles();
    this._bindEvents();
    this._renderTiles();
  }


  // ────────────────────────────────────────────────────────────────────────
  //  TILE CREATION & RENDERING
  // ────────────────────────────────────────────────────────────────────────

  /**
   * Create 9 tile <div> elements (one per number 0-8) and append to the grid.
   * Each tile is absolutely positioned; its (row, col) position is set via
   * a CSS `transform: translate(...)` during rendering.
   */
  _createTiles() {
    /** @type {Object.<number, HTMLDivElement>} Maps tile value → DOM element */
    this.tileElements = {};

    for (let value = 0; value < TOTAL_TILES; value++) {
      const tile = document.createElement("div");
      tile.classList.add("tile");
      tile.dataset.value = value;

      if (value === 0) {
        // The blank tile — invisible, no number shown
        tile.classList.add("tile--blank");
      } else {
        tile.textContent = value;
        // Click handler: try to slide this tile into the blank
        tile.addEventListener("click", () => this._handleTileClick(value));
      }

      this.grid.appendChild(tile);
      this.tileElements[value] = tile;
    }
  }

  /**
   * Update every tile's CSS transform so it visually sits in the correct
   * grid cell based on the current `this.state`.
   *
   * Each tile's position is calculated as:
   *   x = col × (tileSize + gap)
   *   y = row × (tileSize + gap)
   *
   * CSS transitions on `transform` handle the smooth sliding animation.
   */
  _renderTiles() {
    // Read CSS variables for sizing
    const style = getComputedStyle(document.documentElement);
    const tileSize = parseInt(style.getPropertyValue("--tile-size"), 10);
    const gap = parseInt(style.getPropertyValue("--grid-gap"), 10);
    const step = tileSize + gap;

    for (let index = 0; index < TOTAL_TILES; index++) {
      const value = this.state[index];
      const row = Math.floor(index / BOARD_SIZE);
      const col = index % BOARD_SIZE;
      const x = col * step;
      const y = row * step;

      const tile = this.tileElements[value];
      tile.style.setProperty("--tile-translate", `translate(${x}px, ${y}px)`);
      tile.style.transform = `translate(${x}px, ${y}px)`;
    }
  }


  // ────────────────────────────────────────────────────────────────────────
  //  USER INTERACTION
  // ────────────────────────────────────────────────────────────────────────

  /**
   * Bind click handlers and keyboard shortcuts to buttons.
   */
  _bindEvents() {
    this.btnSolve.addEventListener("click", () => this._solve());
    this.btnReset.addEventListener("click", () => this._reset());
    this.btnShuffle.addEventListener("click", () => this._shuffle());
  }

  /**
   * Handle a click on a numbered tile.
   *
   * A tile can slide into the blank only if it is directly adjacent
   * (horizontally or vertically) to the blank space.
   */
  _handleTileClick(tileValue) {
    if (this.isAnimating) return;

    const tileIndex = this.state.indexOf(tileValue);
    const blankIndex = this.state.indexOf(0);

    // Check adjacency
    if (!this._isAdjacent(tileIndex, blankIndex)) return;

    // Swap the tile and the blank
    this.state[blankIndex] = tileValue;
    this.state[tileIndex] = 0;

    this._renderTiles();
    this._clearSolvedGlow();
    this._checkIfSolved();
  }

  /**
   * Determine if two indices are adjacent on the grid
   * (same row, ±1 col  OR  same col, ±1 row).
   */
  _isAdjacent(indexA, indexB) {
    const rowA = Math.floor(indexA / BOARD_SIZE);
    const colA = indexA % BOARD_SIZE;
    const rowB = Math.floor(indexB / BOARD_SIZE);
    const colB = indexB % BOARD_SIZE;

    const dr = Math.abs(rowA - rowB);
    const dc = Math.abs(colA - colB);

    // Exactly one step in one direction, zero in the other
    return (dr + dc) === 1;
  }


  // ────────────────────────────────────────────────────────────────────────
  //  SCRAMBLE / SHUFFLE
  // ────────────────────────────────────────────────────────────────────────

  /**
   * Shuffle the board by making a series of random valid moves.
   *
   * Rather than generating a random permutation (which might be unsolvable),
   * we simulate 100+ random slides from the solved state.  This guarantees
   * the resulting state is always reachable.
   */
  _shuffle() {
    if (this.isAnimating) return;

    // Start from solved
    this.state = [...GOAL_STATE];
    this._clearSolvedGlow();
    this._clearStatus();
    this.statsCard.classList.remove("stats-card--visible");

    const numMoves = 100 + Math.floor(Math.random() * 50);
    let lastBlank = this.state.indexOf(0);

    for (let i = 0; i < numMoves; i++) {
      const row = Math.floor(lastBlank / BOARD_SIZE);
      const col = lastBlank % BOARD_SIZE;

      // Collect valid neighbors of the blank
      const neighbors = [];
      if (row > 0) neighbors.push(lastBlank - BOARD_SIZE);  // up
      if (row < BOARD_SIZE - 1) neighbors.push(lastBlank + BOARD_SIZE);  // down
      if (col > 0) neighbors.push(lastBlank - 1);  // left
      if (col < BOARD_SIZE - 1) neighbors.push(lastBlank + 1);  // right

      // Pick a random neighbor to swap with the blank
      const pick = neighbors[Math.floor(Math.random() * neighbors.length)];
      this.state[lastBlank] = this.state[pick];
      this.state[pick] = 0;
      lastBlank = pick;
    }

    this._renderTiles();
  }


  // ────────────────────────────────────────────────────────────────────────
  //  RESET
  // ────────────────────────────────────────────────────────────────────────

  _reset() {
    // Cancel any running animation
    if (this.animationTimer) {
      clearTimeout(this.animationTimer);
      this.animationTimer = null;
    }
    this.isAnimating = false;

    this.state = [...GOAL_STATE];
    this._renderTiles();
    this._setLocked(false);
    this._clearStatus();
    this._clearSolvedGlow();
    this.statsCard.classList.remove("stats-card--visible");
    this.moveCounter.classList.remove("move-counter--visible");
    this.hintText.textContent = "Click a tile next to the blank to slide it";
    this.hintText.style.opacity = "1";
  }


  // ────────────────────────────────────────────────────────────────────────
  //  SOLVE — API CALL
  // ────────────────────────────────────────────────────────────────────────

  /**
   * Send the current board state to the backend and, on success,
   * animate the returned solution path.
   */
  async _solve() {
    if (this.isAnimating) return;

    // Already solved?
    if (this._isSolved()) {
      this._setStatus("Already solved! 🎉", "success");
      return;
    }

    const algorithm = this.algoSelect.value;

    // UI feedback: show loading state
    this.btnSolve.disabled = true;
    this.btnSolve.innerHTML = `<span class="spinner"></span> Solving…`;
    this._setStatus(`Running ${algorithm === "astar" ? "A*" : "BFS"}…`, "solving");

    try {
      const response = await fetch(`${API_BASE}/api/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state: this.state,
          algorithm: algorithm,
          board_size: BOARD_SIZE,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || `Server error (${response.status})`);
      }

      const data = await response.json();

      // Display stats
      this._showStats(data, algorithm);

      // Animate the solution
      this._animateSolution(data.path);

    } catch (err) {
      this._setStatus(`Error: ${err.message}`, "error");
      this._restoreSolveButton();
    }
  }


  // ────────────────────────────────────────────────────────────────────────
  //  ANIMATION
  // ────────────────────────────────────────────────────────────────────────

  /**
   * Play back the solution path one step at a time.
   *
   * @param {number[][]} path - Array of board states from start to goal.
   */
  _animateSolution(path) {
    if (path.length <= 1) {
      this._setStatus("Already solved! 🎉", "success");
      this._restoreSolveButton();
      return;
    }

    this.isAnimating = true;
    this._setLocked(true);
    this.hintText.style.opacity = "0";

    // Show the move counter
    this.totalSteps.textContent = path.length - 1;
    this.currentStep.textContent = "0";
    this.moveCounter.classList.add("move-counter--visible");

    // The speed slider value is the delay in ms between steps.
    // Lower value → faster animation (slider is inverted in the UI labels).
    const baseDelay = 1100 - parseInt(this.speedSlider.value, 10);

    let stepIndex = 1;  // start from step 1 (step 0 is the initial state)

    const playStep = () => {
      if (stepIndex >= path.length) {
        // Animation complete!
        this._onAnimationComplete();
        return;
      }

      // Update state and render
      this.state = [...path[stepIndex]];
      this._renderTiles();
      this.currentStep.textContent = stepIndex;

      stepIndex++;
      this.animationTimer = setTimeout(playStep, baseDelay);
    };

    // Kick off the first step
    this.animationTimer = setTimeout(playStep, 300);
  }

  /**
   * Called when the solution animation finishes.
   */
  _onAnimationComplete() {
    this.isAnimating = false;
    this._setLocked(false);
    this._restoreSolveButton();
    this._setStatus("Puzzle solved! 🎉", "success");
    this.hintText.textContent = "Solved! Hit Reset or Shuffle to try again";
    this.hintText.style.opacity = "1";

    // Hide move counter after a short delay
    setTimeout(() => {
      this.moveCounter.classList.remove("move-counter--visible");
    }, 2000);

    // Apply celebration glow to all tiles
    this._applySolvedGlow();
  }


  // ────────────────────────────────────────────────────────────────────────
  //  STATS DISPLAY
  // ────────────────────────────────────────────────────────────────────────

  _showStats(data, algorithm) {
    this.statMoves.textContent = data.moves;
    this.statNodes.textContent = data.nodes_expanded.toLocaleString();
    this.statTime.textContent  = data.time_taken + "s";
    this.statAlgo.textContent  = algorithm === "astar" ? "A*" : "BFS";
    this.statsCard.classList.add("stats-card--visible");
  }


  // ────────────────────────────────────────────────────────────────────────
  //  HELPERS
  // ────────────────────────────────────────────────────────────────────────

  /** Check if the current state matches the goal. */
  _isSolved() {
    return this.state.every((val, idx) => val === GOAL_STATE[idx]);
  }

  /** Quick check + glow after manual moves. */
  _checkIfSolved() {
    if (this._isSolved()) {
      this._setStatus("Solved! 🎉", "success");
      this._applySolvedGlow();
    }
  }

  /** Lock or unlock all tiles (during animation). */
  _setLocked(locked) {
    for (let v = 1; v < TOTAL_TILES; v++) {
      this.tileElements[v].classList.toggle("tile--locked", locked);
    }
    this.btnSolve.disabled = locked;
    this.btnShuffle.disabled = locked;
  }

  /** Apply the green "solved" glow to every numbered tile. */
  _applySolvedGlow() {
    for (let v = 1; v < TOTAL_TILES; v++) {
      this.tileElements[v].classList.add("tile--solved");
    }
  }

  /** Remove the green "solved" glow from all tiles. */
  _clearSolvedGlow() {
    for (let v = 1; v < TOTAL_TILES; v++) {
      this.tileElements[v].classList.remove("tile--solved");
    }
  }

  /** Set a message in the status bar with a given type. */
  _setStatus(message, type = "info") {
    this.statusBar.textContent = message;
    this.statusBar.className = `status-bar status-bar--${type}`;
  }

  /** Clear the status bar. */
  _clearStatus() {
    this.statusBar.textContent = "";
    this.statusBar.className = "status-bar";
  }

  /** Restore the Solve button to its default state. */
  _restoreSolveButton() {
    this.btnSolve.disabled = false;
    this.btnSolve.innerHTML = `<span class="btn__icon">▶</span> Solve`;
  }
}


// ─── Initialize on DOM ready ───────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  window.puzzleSolver = new PuzzleSolver();
});
