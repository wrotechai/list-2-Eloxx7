#!/usr/bin/env python3
"""
Breakthrough – Two-Agent Referee
=================================
Orchestrates a game between two independent agent processes.
Each agent is invoked once per move in "single" mode and communicates
via stdin/stdout; no shared memory between agents.

Usage
-----
    python3 referee.py \\
        --agent-b "<cmd for B>"  \\
        --agent-w "<cmd for W>"  \\
        [--rows 8] [--cols 8]    \\
        [--max-rounds 500]       \\
        [--board path/to/board.txt]  \\
        [--verbose]

Examples
--------
# Two agents, same algorithm, different heuristics:
    python3 referee.py \\
        --agent-b "python3 solution.py alphabeta 4 4" \\
        --agent-w "python3 solution.py alphabeta 1 4"

# Different algorithms:
    python3 referee.py \\
        --agent-b "python3 solution.py alphabeta 4 3" \\
        --agent-w "python3 solution.py minimax   1 3"

# Custom board from file:
    python3 referee.py \\
        --agent-b "python3 solution.py alphabeta 4 3" \\
        --agent-w "python3 solution.py alphabeta 4 3" \\
        --board my_board.txt

Output
------
  stdout – final board + "Rounds: N Winner: X"
  stderr – per-agent node counts and times, then totals
"""

import argparse
import subprocess
import sys
import os
import time


# ── Board helpers ──────────────────────────────────────────────────────────────

VALID_CELLS = {'B', 'W', '_', 'o'}


def make_default_board(rows=8, cols=8):
    board = [['_'] * cols for _ in range(rows)]
    for r in range(2):
        for c in range(cols):
            board[r][c] = 'B'
    for r in range(rows - 2, rows):
        for c in range(cols):
            board[r][c] = 'W'
    return board


def board_to_str(board):
    return '\n'.join(' '.join(row) for row in board)


def parse_board(text):
    lines = []
    for line in text.strip().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            tokens = stripped.split()
            if all(t in VALID_CELLS for t in tokens):
                lines.append(tokens)
    return lines


def load_board_file(path):
    with open(path) as f:
        return parse_board(f.read())


# ── Terminal detection ─────────────────────────────────────────────────────────

def is_terminal(board):
    rows = len(board)
    if not rows:
        return None
    if 'B' in board[rows - 1]:
        return 'B'
    if 'W' in board[0]:
        return 'W'
    flat = [c for row in board for c in row]
    if 'B' not in flat:
        return 'W'
    if 'W' not in flat:
        return 'B'
    return None


# ── Agent invocation ───────────────────────────────────────────────────────────

def call_agent(cmd: str, board: list, player: str, timeout: int = 300):
    """
    Invoke an agent process with the current board on stdin.
    Returns (new_board, nodes_visited, elapsed_time).
    Raises RuntimeError on failure.
    """
    board_str = board_to_str(board)
    full_cmd = cmd.split() + ['single', player]

    try:
        result = subprocess.run(
            full_cmd,
            input=board_str,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Agent '{cmd}' timed out after {timeout}s")

    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(
            f"Agent '{cmd}' exited with code {result.returncode}.\n"
            f"stderr: {result.stderr[:500]}"
        )

    # Parse the updated board from stdout
    new_board = parse_board(result.stdout)
    if not new_board:
        raise RuntimeError(
            f"Agent '{cmd}' produced no valid board.\n"
            f"stdout: {result.stdout[:500]}"
        )

    # Parse node count and time from stderr
    nodes, elapsed = 0, 0.0
    numbers = []
    for token in result.stderr.split():
        try:
            numbers.append(float(token))
        except ValueError:
            pass
    if len(numbers) >= 1:
        nodes = int(numbers[0])
    if len(numbers) >= 2:
        elapsed = numbers[1]

    return new_board, nodes, elapsed


# ── Referee loop ───────────────────────────────────────────────────────────────

def play(agent_b_cmd, agent_w_cmd, board, max_rounds=500, verbose=False):
    """
    Run the full game between two agents. Returns (final_board, winner, rounds,
    total_nodes_b, total_nodes_w, total_time_b, total_time_w).
    """
    total_nodes = {'B': 0, 'W': 0}
    total_time  = {'B': 0.0, 'W': 0.0}
    rounds = 0

    # White moves first per the assignment
    current_player = 'W'
    agents = {'B': agent_b_cmd, 'W': agent_w_cmd}

    wall_start = time.time()

    while rounds < max_rounds:
        winner = is_terminal(board)
        if winner:
            break

        agent_cmd = agents[current_player]

        if verbose:
            print(f"\n── Round {rounds + 1}, player {current_player} ──", file=sys.stderr)
            print(board_to_str(board), file=sys.stderr)

        board, nodes, elapsed = call_agent(agent_cmd, board, current_player)

        total_nodes[current_player] += nodes
        total_time[current_player]  += elapsed
        rounds += 1

        if verbose:
            print(f"   nodes={nodes}  time={elapsed:.3f}s", file=sys.stderr)

        winner = is_terminal(board)
        if winner:
            break

        current_player = 'W' if current_player == 'B' else 'B'

    else:
        # Round limit reached — declare draw or choose by piece count
        winner = _decide_by_score(board)

    wall_elapsed = time.time() - wall_start

    return board, winner, rounds, total_nodes, total_time, wall_elapsed


def _decide_by_score(board):
    """Fallback when max rounds reached: winner by piece count."""
    b = sum(row.count('B') for row in board)
    w = sum(row.count('W') for row in board)
    if b > w:
        return 'B'
    if w > b:
        return 'W'
    return 'B'   # tie-break: B


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Breakthrough two-agent referee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--agent-b', required=True,
                        help='Command for player B (e.g. "python3 solution.py alphabeta 4 3")')
    parser.add_argument('--agent-w', required=True,
                        help='Command for player W (e.g. "python3 solution.py alphabeta 1 3")')
    parser.add_argument('--rows', type=int, default=8)
    parser.add_argument('--cols', type=int, default=8)
    parser.add_argument('--board', default=None,
                        help='Path to a file containing the initial board. '
                             'If omitted, the default Breakthrough setup is used.')
    parser.add_argument('--max-rounds', type=int, default=500,
                        help='Hard cap on number of half-moves (default 500)')
    parser.add_argument('--verbose', action='store_true',
                        help='Print board after every move (to stderr)')
    args = parser.parse_args()

    # Initial board
    if args.board:
        if not os.path.isfile(args.board):
            print(f"ERROR: Board file not found: {args.board}", file=sys.stderr)
            sys.exit(1)
        board = load_board_file(args.board)
    else:
        board = make_default_board(args.rows, args.cols)

    print(f"Referee: B='{args.agent_b}'  W='{args.agent_w}'", file=sys.stderr)
    print(f"Board: {len(board)}x{len(board[0])}  max_rounds={args.max_rounds}", file=sys.stderr)

    try:
        final_board, winner, rounds, total_nodes, total_time, wall = play(
            args.agent_b, args.agent_w, board,
            max_rounds=args.max_rounds,
            verbose=args.verbose,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # ── stdout: final board + summary (autograder-compatible) ──────────────────
    print(board_to_str(final_board))
    print(f"Rounds: {rounds} Winner: {winner}")

    # ── stderr: per-agent stats ────────────────────────────────────────────────
    print(f"\n{'─'*50}", file=sys.stderr)
    print(f"Game over — Winner: {winner}  Rounds: {rounds}  Wall: {wall:.2f}s", file=sys.stderr)
    print(f"  Agent B ({args.agent_b})", file=sys.stderr)
    print(f"    Nodes visited : {total_nodes['B']}", file=sys.stderr)
    print(f"    CPU time      : {total_time['B']:.3f}s", file=sys.stderr)
    print(f"  Agent W ({args.agent_w})", file=sys.stderr)
    print(f"    Nodes visited : {total_nodes['W']}", file=sys.stderr)
    print(f"    CPU time      : {total_time['W']:.3f}s", file=sys.stderr)
    print(f"  Total nodes     : {total_nodes['B'] + total_nodes['W']}", file=sys.stderr)
    total_cpu = total_time['B'] + total_time['W']
    print(f"  Total CPU time  : {total_cpu:.3f}s", file=sys.stderr)

    # Autograder stderr format: total nodes on line 1, wall time on line 2
    print(total_nodes['B'] + total_nodes['W'])
    print(f"{wall:.3f}")


if __name__ == '__main__':
    main()
