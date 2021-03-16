from collections import namedtuple
import re

from components import Game, Move, Piece, Player, Space
from components import BACK_RANK, BOARD_SIZE
from board_printer import print_board

class MoveError(ValueError):
    'Used for invalid moves.'
    pass

def create_board():
    'Creates the default starting board.'
    board = create_empty_board()
    for player in PLAYERS:
        for column, piece in enumerate(BACK_RANK):
            board[(player.perspective(0), column)] = Piece(BACK_RANK[column],
                                                           player)
            board[(player.perspective(1), column)] = Piece('pawn', player)
    return board
def create_empty_board():
    rows = columns = range(BOARD_SIZE)
    return dict.fromkeys(Space(row, column)
                         for row in rows for column in columns)

PLAYERS = (
    Player('white', lambda row: row),
    Player('black', lambda row: BOARD_SIZE - 1 - row),
)
BOARD = create_board()
CASTLE_RIGHTS = {p: frozenset({'kingside', 'queenside'}) for p in PLAYERS}

PIECE_DICT = {
    'B': 'bishop',
    'N': 'knight',
    'R': 'rook',
    'Q': 'queen',
    'K': 'king',
    'P': 'pawn',
}

FILES, RANKS = ([chr(ord(character) + i) for i in range(BOARD_SIZE)]
                for character in ('a', '1'))

def ask_board_type():
    while True:
        board_type = input(
            '\nShould the board rotate between turns, or should it be '
            'stationary?\n'
            '(Type "R" for rotating board, "S" for stationary board.)\n'
        ).strip().upper()
        if board_type == 'R':
            return 'rotating'
        elif board_type == 'S':
            return 'static'
        else:
            print("I don't understand... Try again.") 

def find_move(move, moves):
    '''
    Searches for a unique Move in `moves` equal to `move`. If found, returns the
    Move. Otherwise, raises MoveError.
    '''
    moves = filter(lambda m: (
        m.end == move.end
        and m.piece == move.piece
    ), moves)
    
    if move.start.col is not None:
        moves = filter(lambda m: m.start.col == move.start.col, moves)
    if move.start.row is not None:
        moves = filter(lambda m: m.start.row == move.start.row, moves)

    moves = set(moves)
    moves_without_promotion = {(move.start, move.end) for move in moves}
    if len(moves_without_promotion) == 1:
        if move.promotion is None and move.piece_can_be_promoted():
            move = Move(*move[:-1], promote_pawn())
        return next(m for m in moves if m.promotion == move.promotion)
    elif len(moves_without_promotion) == 0:
        raise MoveError('This is not a possible move.')
    elif len(moves_without_promotion) > 1:
        raise MoveError('Be more specific.')

"""
def find_move(move, moves):
    '''
    Searches for a unique Move in `moves` equal to `move`. If found, returns the
    Move. Otherwise, raises MoveError.
    '''
    if move.promotion is None and move.piece_can_be_promoted():
        # Small bug-like behavior: In some circumstances, player will be
        # prompted to choose what they want to promote their pawn to even
        # if the move is invalid. Not a big deal, as the move still gets
        # rejected, but potentially confusing.
        move = Move(*move[:-1], promote_pawn())
        
    moves = filter(lambda m: (
        m.end == move.end
        and m.piece == move.piece
        and m.promotion == move.promotion
    ), moves)
    
    if move.start.col is not None:
        moves = filter(lambda m: m.start.col == move.start.col, moves)
    if move.start.row is not None:
        moves = filter(lambda m: m.start.row == move.start.row, moves)

    moves = set(moves)
    if len(moves) == 1:
        return moves.pop()
    elif len(moves) == 0:
        raise MoveError('This is not a possible move.')
    elif len(moves) > 1:
        raise MoveError('Be more specific.')
"""

def ordinary_move(match, player):
    '''
    Expects a re.match object with groups named 'piece', 'from_file',
    'from_rank', 'to_file', 'to_rank', and 'promotion'. Returns the appropriate
    Move.
    '''
    try:
        start_row = RANKS.index(match.group('from_rank'))
    except ValueError:
        start_row = None
    try:
        start_col = FILES.index(match.group('from_file'))
    except ValueError:
        start_col = None
    
    return Move(Piece(PIECE_DICT.get(match.group('piece'), 'pawn'), player),
                Space(start_row, start_col),
                Space(RANKS.index(match.group('to_rank')),
                      FILES.index(match.group('to_file'))),
                PIECE_DICT.get(match.group('promotion'), None))

# Character sets used in multiple places in the regex pattern below.
PIECE_CHARSET = r'[BNKQRP]'
FILE_CHARSET = r'[a-h]'
RANK_CHARSET = r'[1-8]'
ORDINARY_MOVE = (rf'(?P<ordinary_move>'
                     rf'(?P<piece>{PIECE_CHARSET})?'
                     rf'(?P<from_file>{FILE_CHARSET})?'
                     rf'(?P<from_rank>{RANK_CHARSET})?'
                     rf'x?'
                     rf'(?P<to_file>{FILE_CHARSET})'
                     rf'(?P<to_rank>{RANK_CHARSET})'
                     rf'=?(?P<promotion>{PIECE_CHARSET})?'
                     rf'\+?'
                 rf')')
CASTLE = r'(?P<castle>[0oO]{2,})'
DRAW_OFFER = r'(?P<draw_offer>\(=\))'
RESIGNATION = r'(?P<resignation>\W*[rR]\W*)'
HELP = r'(?P<help>\W*[hH]\W*)'
REGEX_PATTERN = re.compile(
    rf'({ORDINARY_MOVE}|{CASTLE}){DRAW_OFFER}?|{RESIGNATION}|{HELP}'
)

def parse_input(player_input, pattern=REGEX_PATTERN):
    """
    `pattern` should contain groups with the following names:
        `piece`, `from_file`, `from_rank`, `to_file`, `promotion`,
        `castle`, `draw_offer`, `resignation`, `help`.
    If input is successfully matched, this function will return a match object
    with the above-mentioned group names (some of which may have the value
    None, if they played no role in the match).
    """
    # Remove whitespace and '-' from player input.
    player_input = re.sub(r'[-\s]*', '', player_input)
    parsed_input = re.fullmatch(pattern, player_input)
    if parsed_input is None:
        raise MoveError('Input is not valid. Try again.')
    return parsed_input

def promote_pawn():
    '''Asks player what they want their pawn promoted to, returns result.'''
    while True:
        promotion = input(
            '\nWhat would you like to promote your pawn to?\n'
            '("B" for bishop, "N" for knight, "R" for rook, "Q" for queen)\n'
        ).strip().upper()
        if promotion in {'B', 'N', 'R', 'Q'}:
            return PIECE_DICT[promotion]
        else:
            print("I don't understand... Try again.")

def make_move(parsed_input, game, moves):
    # Exceptions should be handled by caller.
    return game.move(find_move(ordinary_move(parsed_input, game.player),
                               moves))

def make_castle(parsed_input, game, moves):
    castle_type = ('kingside' if len(parsed_input.group('castle')) <= 2
                   else 'queenside')
    return game.move(find_move(get_castle(game, castle_type), moves))

def get_castle(game, castle_type):
    offset = 2 if castle_type == 'kingside' else -2
    return Move(Piece('king', game.player),
                start := Space(game.player.perspective(0), 4),
                Space(start.row, start.col + offset),
                None)                
    
def get_input_type(parsed_input, input_types):
    '''
    For a given player input, figures out what kind of input has been
    provided (e.g., ordinary move, castle, resignation, help request).
    '''
    return next(input_type for input_type in input_types
                if parsed_input.groupdict()[input_type])

def resign(game):
    print(f'\n{game.player.color.title()} resigns. '
          f'{game.other_player.color.title()} wins!')
    return 'done'

def new_game():
    while True:
        choice = input('\nType "N" to start a new game, "Q" to quit.\n')
        choice = choice.strip().upper()
        if choice in {'N', 'Q'}:
            break
        print("I don't understand...")
    return True if choice == 'N' else False
    
def get_help():
    print("""
Type an upper-case letter corresponding to the piece you wish to move
(P for pawn, N for knight, B for bishop, R for rook, Q for queen, K for king),
followed by a lower-case letter and number, indicating the space you wish
to move the piece to (e.g., "e4", "a3", etc.). If you are moving a pawn,
you can omit the letter "P". Examples: "Bf6" moves a bishop to space f6.
"Kd2" moves a king to space d2. "g7" moves a pawn to space g7.

In case of ambiguity, you can also specify the file and/or rank that you are
moving the piece *from*. For example, suppose you were to enter "Na3", but there
were two knights which could potentially move to that space. By typing "Nba3",
you would specify that the knight that is currently on file b should move to
space a3. Alternatively, by typing "N1a3", you would specify that the knight
that is currently on rank 1 should move to space a3. And by typing "Nb1a3", you
would specify that the knight that is currently on space b1 should move to space
a3.

To castle, enter "O-O" for a kingside castle, or "O-O-O" for a queenside
castle.

To offer a draw, type "(=)" at the end of your move. For example, by entering
"Qc4(=)", you move your queen to space c4, and offer your opponent a draw.

Enter "r" to resign.""")

def number_of_repetitions(game):
    return game.states.count(game.states[-1])

def draw_offer_accepted(player, other):
    return draw_claimed(player, other, 'offer')

def draw_claimed(player, other, *args, repeat=True):
    '''
    Provides various ways for `player` to claim a draw in a game against
    `other`.
    
    For `player` to accept a draw offered by `other`, pass in the string
    argument "offer".
    
    To claim a draw by threefold repetition, pass in the string argument
    "repetition", followed by an integer argument representing the number
    of times the board position has repeated.

    To claim a draw by the fifty-move rule, pass in the string argument
    "fifty_moves", followed by an integer argument representing the number
    of turns since the last capture or pawn move.
    '''
    if not args:
        return False
    if repeat:
        if 'repetition' in args:
            num_reps = args[args.index('repetition') + 1]
            print(f'\nThis board position has now repeated {num_reps} '
                  f'times.')
        if 'fifty_moves' in args:
            num_moves = args[args.index('fifty_moves') + 1]
            print(f'\nThere have now been {num_moves} straight turns in '
                  f'which neither player has made a pawn move or a '
                  f'capture.')
    while True:
        if {'repetition', 'fifty_moves'} & set(args):
            # sys.stdin = standard_input
            prompt = (f'\nWould {other.color.title()} like to claim a '
                      f'draw? (Y/N)\n')
        elif 'offer' in args:
            repeat = False
            prompt = (f'\n{other.color.title()} is offering a draw. Does '
                      f'{player.color.title()} accept? (Y/N)\n')
        response = input(prompt).strip().upper()
        if response in {'Y', 'N'}:
            break
        print("I don't understand...")
    if response == 'Y':
        return True
    if not repeat:
        return False
    return draw_claimed(other, player, *args, repeat=False)        

def main():
    # The following dictionary maps each type of player input to its associated
    # function. Keys are group names of REGEX_PATTERN.
    instructions = {
        'ordinary_move': make_move,
        'castle': make_castle,
        'resignation': None,
        'help': None,
    }
    
    game = Game(board_type=ask_board_type(),
                board=BOARD,
                castle_rights=CASTLE_RIGHTS,
                players=PLAYERS)
    print_board(game, RANKS, FILES)
    # Will be set to False after the first pass through the main loop.
    first_pass = True
    while True:
        moves = set(game.find_moves())
        if not moves:
            break
        draw_claimed_args = []
        if (num_rep := number_of_repetitions(game)) >= 3:
            if num_rep >= 5:
                print('\nGame ends in a draw due to fivefold repetition.')
                return
            draw_claimed_args += ['repetition', num_rep]
        if (num_moves := game.moves_since_pawn_move_or_capture // 2) >= 50:
            if num_moves >= 75:
                print('\nGame ends in a draw due to the 75-move rule.')
                return
            draw_claimed_args += ['fifty_moves', num_moves]
        if draw_claimed(game.player, game.other_player, *draw_claimed_args):
            print('\nGame ends in a draw.')
            return
        while True:
            try:
                parsed_input = parse_input(input('\nMake your move. '
                                                 '(Type "h" for help.)\n'))
                # Execute appropriate instructions depending on content of
                # parsed_input.
                input_type = get_input_type(parsed_input, instructions)
                if input_type == 'resignation':
                    resign(game)
                    return
                if input_type == 'help':
                    get_help()
                    continue
                game = instructions[input_type](parsed_input, game, moves)
                break
            except MoveError as e:
                print(e)
        print_board(game, RANKS, FILES)
        if parsed_input.group('draw_offer'):
            if draw_offer_accepted(game.player, game.other_player):
                print('\nGame ends in a draw.')
                return
    if game.king_is_in_check():
        print(f'\nCheckmate! {game.other_player.color.title()} wins.')
    else:
        print('\nGame ends in a draw due to stalemate.')

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        standard_input = sys.stdin
        sys.stdin = open(sys.argv[1])
    main()
    while new_game():
        main()
