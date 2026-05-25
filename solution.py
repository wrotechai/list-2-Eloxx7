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
                new_r = r + direction
                if 0 <= new_r < rows:
                    # Forward — only onto empty square
                    if state.board[new_r][c] == '_':
                        moves.append((r, c, new_r, c))
                    # Diagonal left — capture only
                    if c - 1 >= 0 and state.board[new_r][c - 1] == opponent:
                        moves.append((r, c, new_r, c - 1))
                    # Diagonal right — capture only
                    if c + 1 < cols and state.board[new_r][c + 1] == opponent:
                        moves.append((r, c, new_r, c + 1))
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
    # B wins if reaches last row
    if 'B' in state.board[state.rows - 1]:
        return 'B'

    # W wins if reaches first row
    if 'W' in state.board[0]:
        return 'W'

    # no pieces left cases
    all_cells = [c for row in state.board for c in row]
    if 'B' not in all_cells:
        return 'W'
    if 'W' not in all_cells:
        return 'B'

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
    """
    winner = is_terminal(state)
    if winner == 'B':
        return float('inf')
    if winner == 'W':
        return float('-inf')

    rows = state.rows
    cols = state.cols

    b_pieces = sum(row.count('B') for row in state.board)
    w_pieces = sum(row.count('W') for row in state.board)
    starting_pieces = cols * 2

    b_best_row = max((r for r in range(rows) for c in range(cols)
                      if state.board[r][c] == 'B'), default=0)
    w_best_row = min((r for r in range(rows) for c in range(cols)
                      if state.board[r][c] == 'W'), default=rows - 1)

    b_distance = rows - 1 - b_best_row
    w_distance = w_best_row

    if b_distance <= 2 or w_distance <= 2:
        return heuristic_most_advanced_piece(state)

    b_ratio = b_pieces / starting_pieces
    w_ratio = w_pieces / starting_pieces
    if b_ratio < 0.7 or w_ratio < 0.7:
        return heuristic_piece_count(state)

    return heuristic_advancement(state)


HEURISTICS = {
    '1': heuristic_piece_count,
    '2': heuristic_advancement,
    '3': heuristic_most_advanced_piece,
    '4': heuristic_adaptive,
}


# ─── Minimax ───────────────────────────────────────────────────────────────────

nodes_visited = 0


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
    if winner is not None or depth == 0:
        return heuristic(state), None

    moves = move_generator(state)
    if not moves:
        return heuristic(state), None

    best_move = None

    if state.current_player == 'B':
        value = float('-inf')

        for move in moves:
            score, _ = alphabeta(apply_move(state, move),
                                 depth - 1, alpha, beta, heuristic)

            if score > value:
                value = score
                best_move = move

            alpha = max(alpha, value)

            if alpha >= beta:
                break

        return value, best_move

    else:
        value = float('inf')

        for move in moves:
            score, _ = alphabeta(apply_move(state, move),
                                 depth - 1, alpha, beta, heuristic)

            if score < value:
                value = score
                best_move = move

            beta = min(beta, value)

            if alpha >= beta:
                break

        return value, best_move


def best_move_for(state, depth, heuristic, use_alphabeta):
    """Return the best move for the current player."""
    if use_alphabeta:
        _, move = alphabeta(state, depth, float('-inf'), float('inf'), heuristic)
    else:
        _, move = minimax(state, depth, heuristic)
    return move


# ─── Mode: full game ───────────────────────────────────────────────────────────

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


# ─── Mode: single move ─────────────────────────────────────────────────────────

def play_single_move(state, depth, heuristic, use_alphabeta):
    global nodes_visited
    nodes_visited = 0
    start_time = time.time()

    winner = is_terminal(state)
    if winner:
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

    winner = is_terminal(state)
    if winner:
        print(f"Rounds: 1 Winner: {winner}")

    print(nodes_visited, file=sys.stderr)
    print(f"{elapsed:.3f}", file=sys.stderr)


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python3 solution.py <algorithm> <heuristic> <depth> [single <player>]",
              file=sys.stderr)
        sys.exit(1)

    algorithm    = sys.argv[1]
    heuristic_id = sys.argv[2]
    depth        = int(sys.argv[3])
    mode         = sys.argv[4] if len(sys.argv) > 4 else 'full'
    player       = sys.argv[5] if len(sys.argv) > 5 else 'B'

    if heuristic_id not in HEURISTICS:
        print(f"Unknown heuristic '{heuristic_id}'. Use 1, 2, 3, or 4.", file=sys.stderr)
        sys.exit(1)

    heuristic     = HEURISTICS[heuristic_id]
    use_alphabeta = algorithm == 'alphabeta'

    board = parse_board_from_stdin()
    if not board:
        board = make_default_board()

    state = GameState(board, player)

    if mode == 'single':
        play_single_move(state, depth, heuristic, use_alphabeta)
    else:
        play_full_game(state, depth, heuristic, use_alphabeta)
