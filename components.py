'''
Classes and constants for use in the main program.
'''

from collections import namedtuple

BOARD_SIZE = 8
BACK_RANK = ('rook', 'knight', 'bishop', 'queen',
             'king', 'bishop', 'knight', 'rook')
PROMOTION_OPTIONS = {'rook', 'knight', 'bishop', 'queen'}

class Game:
    def __init__(self, *, board, board_type='static', castle_rights, 
                 en_passant=None, players, prev_states=None, move_num=0,
                 moves_since_pawn_move_or_capture=0):
        '''
        Fills in the following attributes for the Game `self`:
            `self.board`: A dictionary representing a board. Keys are Spaces
                and values are Pieces.
            `self.board_type`: Either 'static' (a stationary board) or
                'rotating' (a rotating board). The default is 'static'.
            `self.castle_rights`: A dictionary representing the castling
                rights for each player. Keys are Players. Values are (frozen)
                subsets of {'queenside', 'kingside'}, representing the available
                castles for a given Player.
            `self.en_passant`: The space, if any, that a pawn has passed over
                in the previous turn. Defaults to None, which should also be
                provided if there is no en passant space.
            `self.players`: A tuple of Players. The order in which the Players
                appear represents the turn order.
            `self.move_num`: An integer representing the amount of moves that
                have occurred thus far in the game. Default is 0.
            `self.moves_since_pawn_move_or_capture`: An integer representing
                the amount of moves since the last time a pawn has moved or a
                piece has been captured. (Note that there are two moves in a
                turn.)
            `self.player` represents the current Player.
            `self.other_player` represents the opposing Player.
            `self.states` is a list of tuples of the form (<board>, <player>
                <castle_rights>, <en_passant>), representing the history of
                the game, useful for determining whether the threefold
                repetition rule is applicable. Note that <en_passant> is only
                recorded if a piece can actually be captured en passant. For
                example, if there is an en passant space (e.g., a space that
                a pawn has just passed over), but no pawn can actually move
                to that space, `None` is recorded instead of the en passant
                space.
        '''
        self.board = board
        self.board_type = board_type
        self.castle_rights = castle_rights
        self.en_passant = en_passant
        self.move_num = move_num
        self.moves_since_pawn_move_or_capture = moves_since_pawn_move_or_capture
        self.players = players
        
        self.player = players[move_num % 2]
        self.other_player = players[(move_num + 1) %2]
        
        self.states = prev_states or []
        self.states += [(
            self.board,
            self.player, 
            self.castle_rights, 
            # E.P. space only recorded if it is a conceivable
            # target for an E.P. capture.
            en_passant if self.ep_capture_possible(en_passant) else None,
        )]

    def castle_rook(self, move):
        '''
        Assumes that `move` is a castle. Returns a Move of the appropriate
        rook from its original space to the new space, depending on the type
        of castle (queenside or kingside).
        '''
        start_space = move.castling_rook_space()
        end_space = Space(start_space.row, BACK_RANK.index('king') + (
            1 if move.type_of_castle() == 'kingside' else -1
        ))
        return Move(self.board[start_space], start_space, end_space, None)

    def ep_capture_possible(self, ep_space):
        '''
        Returns True if a piece can move to `ep_space` to capture a
        pawn en passant, and False otherwise. Assumes that `ep_space` has just
        been passed over by a pawn moving two spaces (i.e., that `ep_space`
        could in principle be an E.P. target). If `ep_space` is None, returns
        False.
        '''
        return bool(ep_space) and any(move.piece.kind == 'pawn'
                                      and move.end == ep_space
                                      for move in self.find_moves())

    def find_moves(self):
        '''
        Returns the set of Moves which the player is permitted to make
        (i.e., those that are legal for each of the player's pieces, and do
        not put the player's own king in check).
        '''
        old_spaces = self.get_piece_spaces(self.player)
        for old_space in old_spaces:
            piece_kind = self.board[old_space].kind
            for new_space in self.board:
                move = Move(Piece(piece_kind, self.player), 
                            old_space, new_space, None)
                if move.is_legal(self):
                    hypothetical_state = self.move(move, hypothetical=True)
                    # Don't yield moves that put your king in check.
                    # (It's fine to ignore pawn promotion options here---
                    # promoting your pawn won't have any effect on whether a
                    # move puts your king in check.)
                    if hypothetical_state.king_is_in_check():
                        continue
                    if move.piece_can_be_promoted():
                        promotions = PROMOTION_OPTIONS
                    else:
                        promotions = {None}
                    for promotion in promotions:
                        yield Move(*move[:-1], promotion)

    def get_piece_spaces(self, player):
        '''
        Given a Game `self` and a Player `player`, yields each Space on the
        game's board that contains a Piece of the same color as `player`.
        '''
        board = self.board
        return (space for space in board
                if board[space] and board[space].player == player)

    def king_is_in_check(self):
        '''
        Returns True if current player's own king is in check,
        and False otherwise.
        '''
        player, other = self.player, self.other_player
        board = self.board
        king_space = next(space
                          for space in self.get_piece_spaces(player)
                          if board[space].kind == 'king')
        for old_space in self.get_piece_spaces(other):
            move = Move(board[old_space], old_space, king_space, None)
            if move.is_legal(self):
                return True
        return False

    def move(self, move, hypothetical=False):
        '''
        Given a Game instance and a Move, returns a new Game, updated to
        take into account the effects of the move (e.g., the board is updated,
        castling rights are updated, it becomes the other player's turn, etc.).

        If `hypothetical=True` is provided, then only the board and castling
        rights are updated---it does not become the other player's turn, and
        nothing else about the game changes. This is useful for testing the
        effects of "hypothetical moves," e.g. to see whether or not a move
        puts the player's own king in check.
        '''
        if hypothetical:
            return Game(
                board=self.update_board(move),
                castle_rights=self.castle_rights,
                players=self.players,
                move_num=self.move_num,
            )
        self.moves_since_pawn_move_or_capture += 1
        if move.piece.kind == 'pawn' or move.is_capture(self.board):
            self.moves_since_pawn_move_or_capture = 0
        return Game(
            board=self.update_board(move),
            board_type=self.board_type,
            castle_rights=self.update_castle_rights(
                self.player, move.get_lost_castling_rights()
            ),
            en_passant=move.get_en_passant(),
            players=self.players,
            prev_states=self.states,
            move_num=self.move_num + 1,
            moves_since_pawn_move_or_capture=
                self.moves_since_pawn_move_or_capture,
        )

    def update_board(self, move):
        '''
        Assumes that `move.start` contains `move.piece`, and that the move
        is legal. Returns a new dictionary representing the updated state
        of the board.
        '''
        # Update rook position if move was a castle.
        if move.is_castle():
            board = self.update_board(self.castle_rook(move))
        else:
            board = self.board.copy()
        # This test must be ordered before pawn is moved, as `move
        # .is_en_passant` relies on the fact that the space moved to is empty.
        if move.is_en_passant(board):
            board[(move.start.row, move.end.col)] = None
        # Occupy new space with piece that was on old space, promoting
        # it if applicable.
        board[move.end] = move.piece.promote(move.promotion)
        # Vacate old space.
        board[move.start] = None
        return board
    
    def update_castle_rights(self, player, lost_rights):
        '''
        `lost_rights` is a a subset of {'queenside', 'kingside'},
        specifying which castle rights `player` has lost.
        '''
        castle_rights = self.castle_rights.copy()
        castle_rights[player] -= lost_rights
        return castle_rights

class Move(namedtuple('Move', 'piece, start, end, promotion')):
    def bishop_move(self, game):
        '''
        Determines whether the Move is a valid move for bishops. (Does not take
        into account things that are illegal across many piece types. For
        example, this will return `True` for all diagonal moves, even if there
        are pieces intervening between the start space and the end space.)
        The `game` parameter is not used, but is included for parallelism with
        other similar methods (`king_move`, `pawn_move`).
        '''
        return any(direction() for direction in (
            self.is_diagonal_45,
            self.is_diagonal_135,
        ))

    def castling_rook_space(self):
        '''
        Assumes the move is a castle. Returns the space of the appropriate rook.
        '''
        back_rank = self.piece.player.perspective(0)
        type_of_castle = self.type_of_castle()
        if type_of_castle == 'queenside':
            return Space(back_rank, BACK_RANK.index('rook'))
        if type_of_castle == 'kingside':
            return Space(back_rank,
                         BOARD_SIZE - 1 - BACK_RANK[::-1].index('rook'))
    
    def get_en_passant(self):
        '''
        Returns the space which has become an 'en passant space' as a result
        of the move---that is, the space just passed over by a pawn moving
        two spaces.
        '''
        if (self.piece.kind == 'pawn'
            and abs(self.end.row - self.start.row)) == 2:
            return next(self.get_intervening_spaces())
        return None

    def get_intervening_spaces(self):
        '''
        Yields all Spaces that lie between the move's start space and end space.
        (For moves that are not horizontal, vertical, or diagonal---e.g. knight
        moves---there are no such spaces, and nothing is yielded.)
        '''
        # `low_space` is the space closer to White's back rank.
        # If both spaces are equally close, then `low_space` is the space
        # closer to queenside.
        low_space, high_space = sorted((self.start, self.end))
        
        row_range = range(low_space.row + 1, high_space.row)
        col_range = range(low_space.col + 1, high_space.col)
        reverse_col_range = range(low_space.col - 1, high_space.col, -1)

        # Each direction is mapped to a generator that will yield
        # every space intervening between `old_space` and `new_space`.
        directions = {
            self.is_horizontal: (Space(low_space.row, col)
                                      for col in col_range),
            self.is_vertical: (Space(row, low_space.col)
                                    for row in row_range),
            self.is_diagonal_45: (
                Space(row, col) for row, col in zip(row_range, col_range)
            ),
            self.is_diagonal_135: (
                Space(row, col) for row, col in zip(row_range,
                                                    reverse_col_range)
            ),
        }
        for direction in directions:
            if direction():
                # Returns the appropriate generator depending on the
                # direction of the move.
                return directions[direction]
        # Return an "empty iterator" if the move is not horizontal, vertical,
        # or diagonal (e.g., if it's a knight move).
        return iter(())

    def get_lost_castling_rights(self):
        '''
        Returns the set of castling rights which the move causes the moving
        player to relinquish. (Note that the set returned may include castles
        which, in fact, have already been lost. The function makes no guarantees
        against this.)
        '''
        if self.piece.kind == 'king':
            return {'kingside', 'queenside'}
        if self.piece.kind == 'rook':
            if self.start.col == 0:
                return {'queenside'}
            return {'kingside'}
        return set()
    
    def king_move(self, game):
        '''
        Given a Game instance, determines whether the move is a valid move for
        kings. (Does not take into account things that are illegal across many
        piece types. For example, this will return `True` even if the start and
        end space are the same.)
        '''
        # If the king has moved two files over...
        if self.is_castle():
            type_of_castle = self.type_of_castle()
            return (
                self.start.row == self.end.row
                and type_of_castle in game.castle_rights[self.piece.player]
                and not game.king_is_in_check()
                and not self.piece_passes_through_check(game)
                and not Move(
                    self.piece,
                    self.start,
                    self.castling_rook_space(),
                    self.promotion
                ).pieces_intervene(game)
                # No need to check if king is on its starting space---if it's
                # not, then castling rights will have been lost anyhow, and move
                # will already have been filtered out.
            )
        return (self.queen_move(game)
                and abs(self.end.row - self.start.row) < 2
                and abs(self.end.col - self.start.col) < 2)

    def knight_move(self, game):
        '''
        Determines whether the move is a valid move for knights. (Does not take
        into account things that are illegal across many piece types. For
        example, this function may return `True` even if there is a piece of the
        player's color on the end space.)

        `game` has no effect on the result, but is part of the signature to
        make the function parallel with `Move.king_move` and `Move.pawn_move`,
        where the `game` argument is relevant.
        '''
        return {abs(self.end.row - self.start.row),
                abs(self.end.col - self.start.col)} == {1, 2}

    def is_capture(self, board):
        '''
        Assumes the move is valid. Returns True if it is a capturing
        move, and False otherwise.
        '''
        return board[self.end] or self.is_en_passant(board)

    def is_castle(self):
        '''
        Assumes the move is valid.
        Returns True if it is a castle, and False otherwise.
        '''
        return (self.piece.kind == 'king'
                and abs(self.end.col - self.start.col) == 2)

    def is_diagonal_135(self):
        '''
        Returns True if the move is diagonal in a "135-degree" (or
        "315-degree") direction (e.g., E4-B7, D5-F3).
        Returns False otherwise.
        '''
        return self.end.row - self.start.row == -(self.end.col - self.start.col)

    def is_diagonal_45(self):
        '''
        Returns True if the move is diagonal in a "45-degree" (or "225-degree")
        direction (e.g., E4-H7, D5-B3).
        Returns False otherwise.
        '''
        return self.end.row - self.start.row == self.end.col - self.start.col
    
    def is_horizontal(self):
        '''
        Returns True if the move is horizontal. Returns False otherwise.
        '''
        return self.start.row == self.end.row
        
    def is_en_passant(self, board):
        '''
        Assumes the move is valid.
        Returns True if it is an en passant capture, and False otherwise.
        '''
        return (self.piece.kind == 'pawn'
                and self.start.col != self.end.col
                and board[self.end] is None)

    def is_vertical(self):
        '''
        Returns True if the move is vertical. Returns False otherwise.
        '''
        return self.start.col == self.end.col

    def is_legal(self, game):
        '''
        Returns True if move is legal, False otherwise.
        Assumes that `move.piece` is on `move.start`; ignores `move.promotion`.
        Note that this function does NOT take into account whether a move
        puts/leaves a player's own king in check (i.e., this function can
        return True even if the move puts the player's own king in check).
        '''
        moves_by_piece = {
            'pawn': self.pawn_move,
            'knight': self.knight_move,
            'bishop': self.bishop_move,
            'rook': self.rook_move,
            'queen': self.queen_move,
            'king': self.king_move,
        }
        
        new_piece = game.board[self.end] # i.e. piece (if any) on new space.
        
        # Moves that are illegal for any piece:
        if any((
            # First conjunct ensures that second is only evaluated if
            # `new_piece` is not None (would raise AttributeError otherwise).
            new_piece and new_piece.player == self.piece.player,
            self.start == self.end,
            # `self.pieces_intervene` only operative for pieces that move
            # in straight line (e.g., bishops, rooks, but not knights).
            self.pieces_intervene(game),
        )):
            return False
        
        # Returns True if move is valid according to its piece type (e.g.,
        # if a bishop has made a proper bishop move, knight a proper knight
        # move, etc.), and False otherwise.
        return moves_by_piece[self.piece.kind](game)

    def pawn_capture(self):
        '''
        Returns True if the move is a valid capturing move for pawns,
        False otherwise.
        '''
        old_row = self.piece.player.perspective(self.start.row)
        new_row = self.piece.player.perspective(self.end.row)
        old_col, new_col = self.start.col, self.end.col
        return new_row == old_row + 1 and abs(new_col - old_col) == 1
    
    def pawn_move(self, game):
        '''
        Returns True if the move is valid for pawns, False otherwise.
        (Does not take into account things that are illegal across many piece
        types. For example, this may return `True` even if there is a piece
        of the player's color on the end space.)
        '''
        # `self.player.perspective` ensures that absolute row is mapped
        # to relative row (necessary for determining whether pawn has moved
        # forwards or backwards.
        if (game.board[self.end]
            and game.board[self.end].player != self.piece.player
            # The following condition assumes that the only way for a pawn to
            # move to an E.P. target is to move into that space diagonally.
            # This happens to be correct, due to the logic that determines
            # when a space is an E.P. target---a pawn can't move forward to
            # such a space, as the opponent's pawn will necessarily be in the
            # way.
            or self.end == game.en_passant):
                return self.pawn_capture()
        
        old_row = self.piece.player.perspective(self.start.row)
        new_row = self.piece.player.perspective(self.end.row)
        permitted_steps = (
            # One step forward.
            new_row == old_row + 1,
            # Two steps forward permitted if pawn on its starting row.
            old_row == 1 and new_row == old_row + 2,
        )
        return (self.end.col == self.start.col
                and any(permitted_steps))

    def piece_can_be_promoted(self):
        '''
        Given a Move `self`, returns True iff the `self.end`
        is such that `self.piece` can be promoted.
        '''
        return (
            self.piece.kind == 'pawn'
            and self.end.row
                == self.piece.player.perspective(BOARD_SIZE - 1)
        )

    def pieces_intervene(self, game):
        '''
        Returns True if `self.end` can be reached from `self.start` by a
        horizontal, vertical, or diagonal move, and there is at least one piece
        on a space intervening between `self.end` and `self.start`. Returns
        False otherwise.
        '''
        board = game.board
        # Maps each intervening space to either the piece it contains,
        # or to None (if it does not contain a piece).
        pieces = map(lambda space: board[space],
                     self.get_intervening_spaces())
        # Returns True iff `pieces` contains any actual pieces.
        return any(pieces)

    def piece_passes_through_check(self, game):
        '''
        Returns True if `self.piece` would have to pass through check to get
        from `self.start` to `self.end`, where a piece "passes through check"
        iff there is an intervening space between `self.start` and `self.end`
        such that, if the piece were to stop on that space, it could be captured
        on the opponent's next move.
        
        This function assumes that `self` is a horizontal, vertical, or diagonal
        (by 45 or 135 degrees) move. For other moves (e.g., knight moves), the
        function always returns False.
        '''
        for space in self.get_intervening_spaces():
            hypothetical_state = game.move(
                Move(self.piece, self.start, space, self.promotion),
                hypothetical=True
            )
            if hypothetical_state.king_is_in_check():
                return True
        return False

    def queen_move(self, game):
        '''
        Returns True if the move is valid for queens, False otherwise.
        (Does not take into account things that are illegal across many piece
        types. For example, this may return `True` even if there is a piece
        of the player's color on the end space.)
        The `game` parameter is not used, but is included for parallelism with
        other similar methods (`king_move`, `pawn_move`).
        '''
        return any(move_type(game)
                   for move_type in (self.bishop_move, self.rook_move))
    
    def rook_move(self, game):
        '''
        Returns True if the move is valid for rooks, False otherwise.
        (Does not take into account things that are illegal across many piece
        types. For example, this returns `True` for all horizontal or vertical
        moves, even if there is a piece intervening between the beginning and
        end space.
        The `game` parameter is not used, but is included for parallelism with
        other similar methods (`king_move`, `pawn_move`).
        '''
        return any(direction() for direction in (
            self.is_horizontal,
            self.is_vertical,
        ))
    
    def type_of_castle(self):
        '''
        Assumes move is a castle.
        Returns 'queenside' if move is a queenside castle, and 'kingside' if
        move is a kingside castle.
        '''
        if self.end.col < self.start.col:
            return 'queenside'
        return 'kingside'

class Piece(namedtuple('Piece', 'kind, player')):
    def promote(self, new_kind):
        '''
        Returns a new piece whose kind is `new_kind`, and whose color is the
        same as that of `self`. If `new_kind` is None, returns `self`.
        '''
        if new_kind is None:
            return self
        return Piece(new_kind, self.player)

# The 'perspective' field should be filled by a function
# mapping absolute row to relative row (so that, e.g.,
# moving from row 3 to row 4 is considered a forward step
# for White, but a backward step for Black.
Player = namedtuple('Player', ('color', 'perspective'))
Space = namedtuple('Space', ('row', 'col'))
