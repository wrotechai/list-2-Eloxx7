"""
Breakthrough – Minimax / Alpha-Beta solver
==========================================
Usage
-----
Basic (full game, single process):
    echo "<board>" | python3 solution.py <algorithm> <heuristic> <depth>

Single-move mode (extended two-agent):
    echo "<board>" | python3 solution.py <algorithm> <heuristic> <depth> single <player>

Arguments
---------
algorithm  : minimax | alphabeta
heuristic  : 1 (piece count)  2 (advancement)  3 (most-advanced)  4 (adaptive)
depth      : positive integer
mode       : full (default) | single
player     : B | W  (required for single mode)
"""

import sys
import time


# ══════════════════════════════════════════════════════════════════════════════
# Game state
# ══════════════════════════════════════════════════════════════════════════════

class GameState:
    def __init__(self, board, current_player):
        self.board = board                    # list[list[str]]
        self.current_player = current_player  # 'B' or 'W'
        self.rows = len(board)
        self.cols = len(board[0])

    def copy(self):
        return GameState([row[:] for row in self.board], self.current_player)


# ══════════════════════════════════════════════════════════════════════════════
# Board helpers
# ══════════════════════════════════════════════════════════════════════════════

def make_default_board(rows=8, cols=8):
    board = [['_'] * cols for _ in range(rows)]
    for r in range(2):
        for c in range(cols):
            board[r][c] = 'B'
    for r in range(rows - 2, rows):
        for c in range(cols):
            board[r][c] = 'W'
    return board


def parse_board_from_stdin():
    """Read a board from stdin; skip blank lines and comment lines."""
    lines = []
    for line in sys.stdin:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            lines.append(stripped.split())
    return lines


def board_to_str(state):
    """Return the board as a multiline string (autograder format)."""
    return '\n'.join(' '.join(row) for row in state.board)


def print_board(state):
    print(board_to_str(state))


# ══════════════════════════════════════════════════════════════════════════════
# Move generation
# ══════════════════════════════════════════════════════════════════════════════

def move_generator(state):
    """
    Return list of (from_r, from_c, to_r, to_c) for the current player.

    Rules:
      - Forward (straight): allowed only onto an empty square ('_').
      - Diagonal (left/right forward): capture-only; target must hold opponent piece.
    """
    rows, cols = state.rows, state.cols
    player   = state.current_player
    opponent = 'W' if player == 'B' else 'B'
    direction = 1 if player == 'B' else -1
    moves = []

    for r in range(rows):
        for c in range(cols):
            if state.board[r][c] != player:
                continue
            new_r = r + direction
            if not (0 <= new_r < rows):
                continue
            # Forward — empty square only
            if state.board[new_r][c] == '_':
                moves.append((r, c, new_r, c))
            # Diagonal left — capture only
            if c - 1 >= 0 and state.board[new_r][c - 1] == opponent:
                moves.append((r, c, new_r, c - 1))
            # Diagonal right — capture only
            if c + 1 < cols and state.board[new_r][c + 1] == opponent:
                moves.append((r, c, new_r, c + 1))

    return moves


# ══════════════════════════════════════════════════════════════════════════════
# Apply move
# ══════════════════════════════════════════════════════════════════════════════

def apply_move(state, move):
    from_r, from_c, to_r, to_c = move
    new_state = state.copy()
    new_state.board[to_r][to_c] = new_state.board[from_r][from_c]
    new_state.board[from_r][from_c] = '_'
    new_state.current_player = 'W' if state.current_player == 'B' else 'B'
    return new_state


# ══════════════════════════════════════════════════════════════════════════════
# Terminal check
# ══════════════════════════════════════════════════════════════════════════════

def is_terminal(state):
    """Return 'B', 'W', or None."""
    # B wins by reaching the last row
    if any(state.board[state.rows - 1][c] == 'B' for c in range(state.cols)):
        return 'B'
    # W wins by reaching the first row
    if any(state.board[0][c] == 'W' for c in range(state.cols)):
        return 'W'
    # A player with no pieces loses
    flat = [cell for row in state.board for cell in row]
    if 'B' not in flat:
        return 'W'
    if 'W' not in flat:
        return 'B'
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Heuristics
# ══════════════════════════════════════════════════════════════════════════════

def _terminal_score(state):
    """Return (score, is_terminal). Score is ±inf only at terminal nodes."""
    w = is_terminal(state)
    if w == 'B':
        return float('inf'), True
    if w == 'W':
        return float('-inf'), True
    return 0.0, False


# ── Heuristic 1: piece count ──────────────────────────────────────────────────

def heuristic_piece_count(state):
    """Net piece advantage for B."""
    score, done = _terminal_score(state)
    if done:
        return score
    b = sum(row.count('B') for row in state.board)
    w = sum(row.count('W') for row in state.board)
    return float(b - w)


# ── Heuristic 2: total advancement ───────────────────────────────────────────

def heuristic_advancement(state):
    """Sum of row indices for B pieces minus sum of reversed row indices for W."""
    score, done = _terminal_score(state)
    if done:
        return score
    rows = state.rows
    b_adv = sum(r for r in range(rows) for c in range(state.cols)
                if state.board[r][c] == 'B')
    w_adv = sum(rows - 1 - r for r in range(rows) for c in range(state.cols)
                if state.board[r][c] == 'W')
    return float(b_adv - w_adv)


# ── Heuristic 3: most-advanced single piece ───────────────────────────────────

def heuristic_most_advanced_piece(state):
    """Row of B's furthest piece minus rows-remaining for W's furthest piece."""
    score, done = _terminal_score(state)
    if done:
        return score
    rows = state.rows
    b_best = max((r for r in range(rows) for c in range(state.cols)
                  if state.board[r][c] == 'B'), default=0)
    w_best = max((rows - 1 - r for r in range(rows) for c in range(state.cols)
                  if state.board[r][c] == 'W'), default=0)
    return float(b_best - w_best)


# ── Heuristic 4: adaptive ────────────────────────────────────────────────────

def heuristic_adaptive(state):
    """
    Dynamically selects among the three base heuristics:

      Sprint phase  (either player ≤ 2 rows from winning)
          → most_advanced_piece  — prioritise getting the runner home fast.

      Defend phase  (either player has lost > 30 % of starting pieces)
          → piece_count          — stop the bleeding, protect material.

      Default phase
          → advancement          — push the whole front forward.

    Because B is always the maximiser and W the minimiser, this single
    evaluation function works correctly for both sides inside the search.
    """
    score, done = _terminal_score(state)
    if done:
        return score

    rows, cols = state.rows, state.cols
    starting = cols * 2  # two full rows at game start

    b_pieces = sum(row.count('B') for row in state.board)
    w_pieces = sum(row.count('W') for row in state.board)

    b_best_row = max((r for r in range(rows) for c in range(cols)
                      if state.board[r][c] == 'B'), default=0)
    w_best_row = min((r for r in range(rows) for c in range(cols)
                      if state.board[r][c] == 'W'), default=rows - 1)

    b_distance = rows - 1 - b_best_row   # rows B still needs to travel
    w_distance = w_best_row               # rows W still needs to travel

    # Sprint: race to win / stop opponent from winning
    if b_distance <= 2 or w_distance <= 2:
        return heuristic_most_advanced_piece(state)

    # Defend: material disadvantage
    if b_pieces / starting < 0.70 or w_pieces / starting < 0.70:
        return heuristic_piece_count(state)

    # Default: advance the whole army
    return heuristic_advancement(state)


HEURISTICS = {
    '1': heuristic_piece_count,
    '2': heuristic_advancement,
    '3': heuristic_most_advanced_piece,
    '4': heuristic_adaptive,
}


# ══════════════════════════════════════════════════════════════════════════════
# Search algorithms
# ══════════════════════════════════════════════════════════════════════════════

nodes_visited = 0   # global counter reset before each top-level call


def minimax(state, depth, heuristic):
    global nodes_visited
    nodes_visited += 1

    winner = is_terminal(state)
    if winner is not None or depth == 0:
        return heuristic(state), None

    moves = move_generator(state)
    if not moves:
        return heuristic(state), None

    best_move = None

    if state.current_player == 'B':          # maximiser
        best_score = float('-inf')
        for move in moves:
            score, _ = minimax(apply_move(state, move), depth - 1, heuristic)
            if score > best_score:
                best_score, best_move = score, move
        return best_score, best_move
    else:                                     # minimiser
        best_score = float('inf')
        for move in moves:
            score, _ = minimax(apply_move(state, move), depth - 1, heuristic)
            if score < best_score:
                best_score, best_move = score, move
        return best_score, best_move


def alphabeta(state, depth, alpha, beta, heuristic):
    global nodes_visited
    nodes_visited += 1

    winner = is_terminal(state)
    if winner is not None or depth == 0:
        return heuristic(state), None

    moves = move_generator(state)
    if not moves:
        return heuristic(state), None

    best_move = None

    if state.current_player == 'B':          # maximiser
        value = float('-inf')
        for move in moves:
            score, _ = alphabeta(apply_move(state, move), depth - 1, alpha, beta, heuristic)
            if score > value:
                value, best_move = score, move
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:                                     # minimiser
        value = float('inf')
        for move in moves:
            score, _ = alphabeta(apply_move(state, move), depth - 1, alpha, beta, heuristic)
            if score < value:
                value, best_move = score, move
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move


def best_move_for(state, depth, heuristic, use_alphabeta):
    """Return the best move for the current player (or None if no moves)."""
    if use_alphabeta:
        _, move = alphabeta(state, depth, float('-inf'), float('inf'), heuristic)
    else:
        _, move = minimax(state, depth, heuristic)
    return move


# ══════════════════════════════════════════════════════════════════════════════
# Mode: full game  (basic version — single process plays both sides)
# ══════════════════════════════════════════════════════════════════════════════

def play_full_game(state, depth, heuristic, use_alphabeta):
    global nodes_visited
    nodes_visited = 0
    rounds = 0
    start_time = time.time()

    while True:
        winner = is_terminal(state)
        if winner:
            elapsed = time.time() - start_time
            print_board(state)
            print(f"Rounds: {rounds} Winner: {winner}")
            print(nodes_visited, file=sys.stderr)
            print(f"{elapsed:.3f}", file=sys.stderr)
            return

        move = best_move_for(state, depth, heuristic, use_alphabeta)
        if move is None:
            # No legal moves — opponent wins
            winner = 'W' if state.current_player == 'B' else 'B'
            elapsed = time.time() - start_time
            print_board(state)
            print(f"Rounds: {rounds} Winner: {winner}")
            print(nodes_visited, file=sys.stderr)
            print(f"{elapsed:.3f}", file=sys.stderr)
            return

        state = apply_move(state, move)
        rounds += 1


# ══════════════════════════════════════════════════════════════════════════════
# Mode: single move  (extended version — one agent per invocation)
# ══════════════════════════════════════════════════════════════════════════════

def play_single_move(state, depth, heuristic, use_alphabeta):
    """
    Compute ONE move for `state.current_player`, apply it, then print:
      stdout  – updated board  (and summary line if the game is now over)
      stderr  – nodes visited, elapsed time
    """
    global nodes_visited
    nodes_visited = 0
    start_time = time.time()

    # Already over before we even move?
    winner = is_terminal(state)
    if winner:
        print_board(state)
        print(f"Rounds: 0 Winner: {winner}")
        print(nodes_visited, file=sys.stderr)
        print("0.000", file=sys.stderr)
        return

    move = best_move_for(state, depth, heuristic, use_alphabeta)
    if move:
        state = apply_move(state, move)

    elapsed = time.time() - start_time

    print_board(state)

    # Print summary only when the game ends so the referee can detect it
    winner = is_terminal(state)
    if winner:
        print(f"Rounds: 1 Winner: {winner}")

    print(nodes_visited, file=sys.stderr)
    print(f"{elapsed:.3f}", file=sys.stderr)


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(
            "Usage: python3 solution.py <algorithm> <heuristic> <depth> [single <player>]\n"
            "  algorithm : minimax | alphabeta\n"
            "  heuristic : 1 | 2 | 3 | 4\n"
            "  depth     : positive integer\n"
            "  mode      : full (default) | single\n"
            "  player    : B | W  (required for single mode)",
            file=sys.stderr,
        )
        sys.exit(1)

    algorithm    = sys.argv[1]
    heuristic_id = sys.argv[2]
    depth        = int(sys.argv[3])
    mode         = sys.argv[4] if len(sys.argv) > 4 else 'full'
    player       = sys.argv[5] if len(sys.argv) > 5 else 'B'

    if heuristic_id not in HEURISTICS:
        print(f"Unknown heuristic '{heuristic_id}'. Choose from: {', '.join(HEURISTICS)}.",
              file=sys.stderr)
        sys.exit(1)

    heuristic     = HEURISTICS[heuristic_id]
    use_alphabeta = (algorithm == 'alphabeta')

    board = parse_board_from_stdin()
    if not board:
        board = make_default_board()

    state = GameState(board, player)

    if mode == 'single':
        play_single_move(state, depth, heuristic, use_alphabeta)
    else:
        play_full_game(state, depth, heuristic, use_alphabeta)
