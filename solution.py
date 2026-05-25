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
                    # Forward move — empty or 'o' squares only
                    if state.board[new_r][c] in ('_', 'o'):
                        current_moves.append((r, c, new_r, c))
                    # Diagonal left
                    if c - 1 >= 0 and state.board[new_r][c - 1] in ('_', 'o', opponent):
                        current_moves.append((r, c, new_r, c - 1))
                    # Diagonal right
                    if c + 1 < cols and state.board[new_r][c + 1] in ('_', 'o', opponent):
                        current_moves.append((r, c, new_r, c + 1))
                moves.extend(current_moves)
    return moves


# ─── Apply move ────────────────────────────────────────────────────────────────

def apply_move(state, move):
    from_row, from_col, to_row, to_col = move
    new_state = state.copy()
    # Clear previous 'o' markers
    for r in range(new_state.rows):
        for c in range(new_state.cols):
            if new_state.board[r][c] == 'o':
                new_state.board[r][c] = '_'
    piece = new_state.board[from_row][from_col]
    new_state.board[to_row][to_col] = piece
    new_state.board[from_row][from_col] = 'o'
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
    # B moves down — higher r = more advanced
    black_adv = sum(r for r in range(state.rows)
                    for c in range(state.cols) if state.board[r][c] == 'B')
    # W moves up — lower r = more advanced → invert
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


HEURISTICS = {
    '1': heuristic_piece_count,
    '2': heuristic_advancement,
    '3': heuristic_most_advanced_piece,
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

    if state.current_player == 'B':  # maximising
        best_score = float('-inf')
        for move in moves:
            score, _ = minimax(apply_move(state, move), depth - 1, heuristic)
            if score > best_score:
                best_score = score
                best_move = move
        return best_score, best_move

    else:  # minimising
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

    if state.current_player == 'B':  # maximising
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

    else:  # minimising
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


# ─── Main game loop ────────────────────────────────────────────────────────────

def play_game(state, depth, heuristic, use_alphabeta):
    global nodes_visited
    nodes_visited = 0
    rounds = 0
    start_time = time.time()

    while True:
        winner = is_terminal(state)
        if winner:
            elapsed = time.time() - start_time
            # stdout: final board then summary
            print_board_final(state)
            print(f"Rounds: {rounds} Winner: {winner}")
            # stderr: nodes then time
            print(nodes_visited, file=sys.stderr)
            print(f"{elapsed:.3f}", file=sys.stderr)
            return

        if use_alphabeta:
            _, move = alphabeta(state, depth, float('-inf'), float('inf'), heuristic)
        else:
            _, move = minimax(state, depth, heuristic)

        if move is None:
            break

        state = apply_move(state, move)
        rounds += 1


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python3 solution.py <algorithm> <heuristic> <depth>", file=sys.stderr)
        sys.exit(1)

    algorithm  = sys.argv[1]   # "minimax" or "alphabeta"
    heuristic_id = sys.argv[2] # "1", "2", or "3"
    depth      = int(sys.argv[3])

    if heuristic_id not in HEURISTICS:
        print(f"Unknown heuristic '{heuristic_id}'. Use 1, 2, or 3.", file=sys.stderr)
        sys.exit(1)

    heuristic = HEURISTICS[heuristic_id]
    use_alphabeta = algorithm == 'alphabeta'

    board = parse_board_from_stdin()
    if not board:
        board = make_default_board()

    state = GameState(board, 'B')
    play_game(state, depth, heuristic, use_alphabeta)
