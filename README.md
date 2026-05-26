[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=24002748&assignment_repo_type=AssignmentRepo)
# Assignment #2 — Breakthrough (Minimax & Alpha-Beta)

**Course:** Artificial Intelligence and Knowledge Engineering (AI&KE), 2025/2026, SI4024L

---

## Overview

In this assignment you implement game-playing algorithms for **Breakthrough**, a two-player board game:

- **Minimax** — a game tree search algorithm for optimal decision-making in zero-sum games.
- **Alpha-Beta pruning** — an optimization of Minimax that prunes branches that cannot affect the final decision.
- **Heuristics** — at least 3 different board evaluation functions per player.

See the full assignment PDF for details, scoring, and theoretical background.

---

## Repository structure

```
.
├── run_game.sh             # Runner script (edit this)
├── tests/
│   └── autograder.py        # Automated tests (DO NOT MODIFY)
├── .github/                 # CI/autograding config (DO NOT MODIFY)
└── README.md
```

---

## How to submit your solution

### 1. Clone this repository

```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2. Add your solution

Place your solution files (e.g. `solution.py`, `main.py`, or compiled binaries) in the root of this repository. You can use any programming language.

### 3. Configure the runner script

Edit **`run_game.sh`** — change the last line to invoke your solution.

The autograder calls `run_game.sh` with these positional arguments:

| Argument | Description | Example |
|----------|-------------|---------|
| `$1` | Algorithm | `"minimax"` or `"alphabeta"` |
| `$2` | Heuristic ID | `"1"`, `"2"`, or `"3"` |
| `$3` | Search depth | `"3"` |

The **starting board** is piped via **stdin** — your program reads it from standard input.

Examples — pick one and adapt:

```bash
# Python (default, already set):
python3 solution.py "$1" "$2" "$3"

# Python with named args:
python3 main.py --algorithm "$1" --heuristic "$2" --depth "$3"

# Java:
java -jar solution.jar "$1" "$2" "$3"

# C++:
./solution "$1" "$2" "$3"
```

### 4. Board format

**Input (stdin):** The board is given as `m` lines of `n` space-separated tokens:

| Token | Meaning |
|-------|---------|
| `B` | Player 1's piece |
| `W` | Player 2's piece |
| `_` | Empty square |
| `o` | Empty square (origin of the last move) |

**Convention:**
- Line 1 = top of the board.
- **B** (Player 1) starts at the top two rows, moves **downward**.
- **W** (Player 2) starts at the bottom two rows, moves **upward**.
- B wins by reaching the last row; W wins by reaching the first row.
- **Player 1 (B) moves first.**

Default 8x8 starting board:
```
B B B B B B B B
B B B B B B B B
_ _ _ _ _ _ _ _
_ _ _ _ _ _ _ _
_ _ _ _ _ _ _ _
_ _ _ _ _ _ _ _
W W W W W W W W
W W W W W W W W
```

### 5. Output format

**stdout:** The final board state (`m` lines of space-separated tokens), followed by a summary line:

```
_ _ _ _ B _ _ _
_ _ _ o _ _ _ _
...
W _ _ _ _ _ W _
Rounds: 23 Winner: B
```

**stderr:** Two values — visited node count and computation time:

```
154832
1.456
```

### 6. Push your solution

```bash
git add .
git commit -m "Add my solution"
git push
```

Every push triggers the **autograder** via GitHub Actions. Check results in the **Actions** tab of your repository.

---

## Autograder tests

The autograder runs 9 correctness tests (44 points). These tests verify that your solution produces correct outputs — they do **not** determine your final grade.

> **The final grade is determined by the teacher** based on the autograder results, the quality of your report, and your understanding of the theoretical background (algorithm design, heuristic justification, experimental comparisons). Passing all autograder tests is necessary but not sufficient for a full score. See the grading rubric for the complete breakdown.

| Test | What it checks | Points |
|------|---------------|--------|
| T1_OUTPUT_FORMAT | Valid board output + summary + stderr | 5 |
| T2_MINIMAX_GAME | Minimax plays a full game with valid winner | 5 |
| T3_ALPHABETA_GAME | Alpha-beta plays a full game with valid winner | 5 |
| T4_PRUNING | Alpha-beta visits fewer nodes than Minimax (6x6, d=3) | 5 |
| T5_ENDGAME | Forced win detected (B one step from last row) | 5 |
| T6_CAPTURE | Diagonal capture mechanic works (forced capture) | 4 |
| T7_HEURISTIC_2 | Heuristic 2 produces a valid game | 5 |
| T8_HEURISTIC_3 | Heuristic 3 produces a valid game | 5 |
| T9_DEPTH_EFFECT | Deeper search explores more nodes | 5 |

### Running tests locally

```bash
# Run a single test:
python3 tests/autograder.py T1_OUTPUT_FORMAT

# Run all tests:
for t in T1_OUTPUT_FORMAT T2_MINIMAX_GAME T3_ALPHABETA_GAME T4_PRUNING T5_ENDGAME T6_CAPTURE T7_HEURISTIC_2 T8_HEURISTIC_3 T9_DEPTH_EFFECT; do
    echo "--- $t ---"
    python3 tests/autograder.py $t
done
```

---

## Game rules (Breakthrough)

1. **Setup:** Two players on an 8x8 board. Each player fills their two closest rows with pieces.
2. **Turns:** Players alternate. Player 1 (B) goes first.
3. **Moves:** A piece can move one square forward (straight or diagonal), if the target square is empty.
4. **Captures:** A piece can capture an opponent's piece **only diagonally** (never straight ahead). The captured piece is removed.
5. **Winning:** The first player to move a piece onto the opponent's back row wins.

---

## Important notes

- **Do not modify** files in `tests/` or `.github/`. Changes to these protected files will be flagged.
- Your program must read the board from **stdin** and accept algorithm, heuristic, and depth as command-line arguments.
- Implement **at least 3 different heuristics** (each with a fundamentally different evaluation strategy).
- Both **Minimax** and **Alpha-Beta** must be implemented. The autograder tests both algorithms.

---

## Quick Git reference

| What you want to do | Command |
|---------------------|---------|
| Clone your repo | `git clone <url>` |
| Check what changed | `git status` |
| Stage files | `git add solution.py run_game.sh` |
| Commit | `git commit -m "description"` |
| Push to GitHub | `git push` |
| Pull latest changes | `git pull` |

New to Git? See the [Git Handbook](https://docs.github.com/en/get-started/using-git/about-git) or [this short video](https://www.youtube.com/watch?v=w3jLJU7DT5E).
