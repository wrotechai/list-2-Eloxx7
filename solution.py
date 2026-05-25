import sys
import time


# ─── Game State ────────────────────────────────────────────────────────────────

class GameState:
    def __init__(self, board, current_player):
        self.board = board
        self.current_player = current_player  # 'B' or 'W'
        self.rows = len(board)
        self.cols = len(board[0])

    def copy(self):
        return GameState(
            [row[:] for row in self.board],
            self.current_player
        )


# ─── Board helpers ─────────────────────────────────────────────────────────────

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
    lines = []
    for line in sys.stdin:
        line = line.strip()
        if line:
            lines.append(line.split())
    return lines


def print_board_final(state):
    """Print board in autograder format (no labels, just tokens)."""
    for row in state.board:
        print(' '.join(row))


# ─── Move generation ───────────────────────────────────────────────────────────

def move_generator(state):
    rows = state.rows
    cols = state.cols
    moves = []
    direction = 1 if state.current_player == 'B' else -1
    opponent = 'W' if state.current_player == 'B' else 'B'

    for r in range(rows):
        for c in range(cols):
            if state.board[r][c] == state.current_player:
                current_moves = []
                new_r = r + direction
                if 0 <= new_r < rows:
                    # Forward — empty or 'o' only
                    if state.board[new_r][c] == '_':
                        current_moves.append((r, c, new_r, c))
                    # Diagonal left
                    if c - 1 >= 0 and state.board[new_r][c - 1] != state.current_player:
                        current_moves.append((r, c, new_r, c - 1))
                    # Diagonal right
                    if c + 1 >= 0 and state.board[new_r][c - 1] != state.current_player:
                        current_moves.append((r, c, new_r, c + 1))
                moves.extend(current_moves)
    return moves


# ─── Apply move ────────────────────────────────────────────────────────────────

def apply_move(state, move):
    from_row, from_col, to_row, to_col = move

    new_state = state.copy()

    piece = new_state.board[from_row][from_col]

    new_state.board[to_row][to_col] = piece
    new_state.board[from_row][from_col] = '_'

    new_state.current_player = 'W' if state.current_player == 'B' else 'B'

    return new_state


# ─── Terminal check ────────────────────────────────────────────────────────────

def is_terminal(state):
    for c in range(state.cols):
        if state.board[state.rows - 1][c] == 'B':
            return 'B'
        if state.board[0][c] == 'W':
            return 'W'
    return None


# ─── Heuristics ────────────────────────────────────────────────────────────────

def heuristic_piece_count(state):
    winner = is_terminal(state)
    if winner == 'B':
        return float('inf')
    if winner == 'W':
        return float('-inf')
    black_count = sum(row.count('B') for row in state.board)
    white_count = sum(row.count('W') for row in state.board)
    return black_count - white_count


def heuristic_advancement(state):
    winner = is_terminal(state)
    if winner == 'B':
        return float('inf')
    if winner == 'W':
        return float('-inf')
    black_adv = sum(r for r in range(state.rows)
                    for c in range(state.cols) if state.board[r][c] == 'B')
    white_adv = sum(state.rows - 1 - r for r in range(state.rows)
                    for c in range(state.cols) if state.board[r][c] == 'W')
    return black_adv - white_adv


def heuristic_most_advanced_piece(state):
    winner = is_terminal(state)
    if winner == 'B':
        return float('inf')
    if winner == 'W':
        return float('-inf')
    black_best = max((r for r in range(state.rows)
                      for c in range(state.cols) if state.board[r][c] == 'B'), default=0)
    white_best = max((state.rows - 1 - r for r in range(state.rows)
                      for c in range(state.cols) if state.board[r][c] == 'W'), default=0)
    return black_best - white_best


def heuristic_adaptive(state):
    """
    Switches strategy based on board state:
      - If our best piece is within 2 rows of winning  → sprint (most_advanced)
      - If we've lost more than 30% of our pieces      → defend (piece_count)
      - Otherwise                                       → advance (advancement)

    'Our' perspective is always B (maximising), so we evaluate from B's point of view.
    W's minimax will still minimise this score, so the adaptive logic naturally
    works for both players within the same search.
    """
    winner = is_terminal(state)
    if winner == 'B':
        return float('inf')
    if winner == 'W':
        return float('-inf')

    rows = state.rows
    cols = state.cols

    # Count pieces
    b_pieces = sum(row.count('B') for row in state.board)
    w_pieces = sum(row.count('W') for row in state.board)
    starting_pieces = cols * 2  # default two rows each

    # Most advanced piece for each player
    b_best_row = max((r for r in range(rows) for c in range(cols)
                      if state.board[r][c] == 'B'), default=0)
    w_best_row = min((r for r in range(rows) for c in range(cols)
                      if state.board[r][c] == 'W'), default=rows - 1)

    b_distance = rows - 1 - b_best_row   # rows remaining for B to win
    w_distance = w_best_row               # rows remaining for W to win

    # Sprint condition: either player is within 2 rows of winning
    if b_distance <= 2 or w_distance <= 2:
        return heuristic_most_advanced_piece(state)

    # Defend condition: current player has lost more than 30% of pieces
    b_ratio = b_pieces / starting_pieces
    w_ratio = w_pieces / starting_pieces
    if b_ratio < 0.7 or w_ratio < 0.7:
        return heuristic_piece_count(state)

    # Default: advancement
    return heuristic_advancement(state)


HEURISTICS = {
    '1': heuristic_piece_count,
    '2': heuristic_advancement,
    '3': heuristic_most_advanced_piece,
    '4': heuristic_adaptive,   # extended adaptive heuristic
}


# ─── Minimax ───────────────────────────────────────────────────────────────────

nodes_visited = 0


def minimax(state, depth, heuristic):
    global nodes_visited
    nodes_visited += 1

    winner = is_terminal(state)
    if winner is not None:
        return heuristic(state), None
    if depth == 0:
        return heuristic(state), None

    moves = move_generator(state)
    if not moves:
        return heuristic(state), None

    best_move = None

    if state.current_player == 'B':
        best_score = float('-inf')
        for move in moves:
            score, _ = minimax(apply_move(state, move), depth - 1, heuristic)
            if score > best_score:
                best_score = score
                best_move = move
        return best_score, best_move
    else:
        best_score = float('inf')
        for move in moves:
            score, _ = minimax(apply_move(state, move), depth - 1, heuristic)
            if score < best_score:
                best_score = score
                best_move = move
        return best_score, best_move


# ─── Alpha-Beta ────────────────────────────────────────────────────────────────

def alphabeta(state, depth, alpha, beta, heuristic):
    global nodes_visited
    nodes_visited += 1

    winner = is_terminal(state)
    if winner is not None:
        return heuristic(state), None
    if depth == 0:
        return heuristic(state), None

    moves = move_generator(state)
    if not moves:
        return heuristic(state), None

    best_move = None

    if state.current_player == 'B':
        best_score = float('-inf')
        for move in moves:
            score, _ = alphabeta(apply_move(state, move), depth - 1, alpha, beta, heuristic)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        best_score = float('inf')
        for move in moves:
            score, _ = alphabeta(apply_move(state, move), depth - 1, alpha, beta, heuristic)
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score, best_move


def best_move_for(state, depth, heuristic, use_alphabeta):
    """Return the best move for the current player."""
    if use_alphabeta:
        _, move = alphabeta(state, depth, float('-inf'), float('inf'), heuristic)
    else:
        _, move = minimax(state, depth, heuristic)
    return move


# ─── Mode: full game (basic) ───────────────────────────────────────────────────

def play_full_game(state, depth, heuristic, use_alphabeta):
    global nodes_visited
    nodes_visited = 0
    rounds = 0
    start_time = time.time()

    while True:
        winner = is_terminal(state)
        if winner:
            elapsed = time.time() - start_time
            print_board_final(state)
            print(f"Rounds: {rounds} Winner: {winner}")
            print(nodes_visited, file=sys.stderr)
            print(f"{elapsed:.3f}", file=sys.stderr)
            return

        move = best_move_for(state, depth, heuristic, use_alphabeta)
        if move is None:
            winner = 'W' if state.current_player == 'B' else 'B'
            elapsed = time.time() - start_time

            print_board_final(state)
            print(f"Rounds: {rounds} Winner: {winner}")

            print(nodes_visited, file=sys.stderr)
            print(f"{elapsed:.3f}", file=sys.stderr)
            return

        state = apply_move(state, move)
        rounds += 1


# ─── Mode: single move (extended two-agent) ────────────────────────────────────

def play_single_move(state, depth, heuristic, use_alphabeta):
    """
    Compute and apply one move for the current player.
    Output: updated board only (no summary line).
    Stderr: nodes visited, time.
    Used when two agents alternate invocations.
    """
    global nodes_visited
    nodes_visited = 0
    start_time = time.time()

    winner = is_terminal(state)
    if winner:
        # Game is already over — just print the board
        print_board_final(state)
        print(f"Rounds: 0 Winner: {winner}")
        print(nodes_visited, file=sys.stderr)
        print("0.000", file=sys.stderr)
        return

    move = best_move_for(state, depth, heuristic, use_alphabeta)
    if move:
        state = apply_move(state, move)

    elapsed = time.time() - start_time
    print_board_final(state)

    # Check if the move just won the game
    winner = is_terminal(state)
    if winner:
        print(f"Rounds: 1 Winner: {winner}")

    print(nodes_visited, file=sys.stderr)
    print(f"{elapsed:.3f}", file=sys.stderr)


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Expected args:
    #   Basic:    solution.py <algorithm> <heuristic> <depth>
    #   Extended: solution.py <algorithm> <heuristic> <depth> <mode> <player>
    #
    #   <mode>   = "full" (default) | "single"
    #   <player> = "B" | "W"  (only required for single mode)

    if len(sys.argv) < 4:
        print("Usage: python3 solution.py <algorithm> <heuristic> <depth> [single <player>]",
              file=sys.stderr)
        sys.exit(1)

    algorithm    = sys.argv[1]          # "minimax" or "alphabeta"
    heuristic_id = sys.argv[2]          # "1", "2", "3", or "4"
    depth        = int(sys.argv[3])
    mode         = sys.argv[4] if len(sys.argv) > 4 else 'full'   # "full" or "single"
    player       = sys.argv[5] if len(sys.argv) > 5 else 'B'      # "B" or "W"

    if heuristic_id not in HEURISTICS:
        print(f"Unknown heuristic '{heuristic_id}'. Use 1, 2, 3, or 4.", file=sys.stderr)
        sys.exit(1)

    heuristic    = HEURISTICS[heuristic_id]
    use_alphabeta = algorithm == 'alphabeta'

    board = parse_board_from_stdin()
    if not board:
        board = make_default_board()

    state = GameState(board, player)

    if mode == 'single':
        play_single_move(state, depth, heuristic, use_alphabeta)
    else:
        play_full_game(state, depth, heuristic, use_alphabeta)
