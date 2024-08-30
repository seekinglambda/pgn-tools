#!/usr/bin/env python3

import sys
import chess
import chess.pgn
import io
import os


def truncate_pgn(pgn_string, max_depth):
    game = chess.pgn.read_game(io.StringIO(pgn_string))
    if game is None:
        return None

    def truncate_node(node, current_depth=0):
        if current_depth >= max_depth:
            node.variations.clear()
            return

        for variation in node.variations:
            truncate_node(variation, current_depth + 1)

    truncate_node(game)
    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
    return game.accept(exporter)


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <INPUT_PGN_FILE> <OUTPUT_PGN_FILE> <MAX_DEPTH>")
        sys.exit(1)

    input_pgn_file = sys.argv[1]
    output_pgn_file = sys.argv[2]
    try:
        max_depth = int(sys.argv[3])
    except ValueError:
        print("Error: MAX_DEPTH must be an integer")
        sys.exit(1)

    try:
        with open(input_pgn_file, 'r') as f:
            pgn_string = f.read()
    except IOError:
        print(f"Error: Could not read file {input_pgn_file}")
        sys.exit(1)

    truncated_pgn = truncate_pgn(pgn_string, max_depth)
    if truncated_pgn is None:
        print("Error: Invalid PGN file")
        sys.exit(1)

    try:
        with open(output_pgn_file, 'w') as f:
            f.write(truncated_pgn)
        print(f"Truncated PGN has been written to {output_pgn_file}")
    except IOError:
        print(f"Error: Could not write to file {output_pgn_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
