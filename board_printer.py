'''
Contains a function that prints a chess board.
'''

from components import Space

PIECE_TYPES = ('king', 'queen', 'rook', 'bishop', 'knight', 'pawn')
FIRST_CHESS_CODEPOINT = 0x2654

# Construct a dictionary mapping each piece type to a tuple containing the
# appropriate unicode symbols (white first, then black). For example, 'king'
# is mapped to ('♔', '♚').
PIECE_TO_STRING = {
    piece_type: (chr(FIRST_CHESS_CODEPOINT + i), 
                 chr(FIRST_CHESS_CODEPOINT + i + len(PIECE_TYPES)))
    for (i, piece_type) in enumerate(PIECE_TYPES)
}

def space_printer(space, game):
    piece = game.board[space]
    if piece is None:
        return '■' if space.col % 2 == space.row % 2 else '□'
    else:
        return PIECE_TO_STRING[piece.kind][game.players.index(piece.player)]

def print_board(game, ranks, files):
    """
    Prints a board. `ranks` and `files` are sequences of rank and file
    identifiers, respectively.
    """
    if game.board_type == 'static':
        direction = -1
    else:
        direction = 1 if game.players.index(game.player) else -1
    print_strings = []
    for i, rank in enumerate(ranks):
        row_num = rank + ' '
        row_string = ''
        for space in (Space(i, j) for j in range(len(files))):
            row_string += space_printer(space, game)
        row_string = row_string[::direction * -1]
        print_strings.append(row_num + row_string + '\n')
    print_strings = print_strings[::direction]
    print_strings.append('  ' + ''.join(files[::direction*-1]))
    print('\n' + ''.join(print_strings))
