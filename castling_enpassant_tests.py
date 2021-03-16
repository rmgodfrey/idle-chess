'''
Mainly tests castling and en passant.
'''

import unittest
from components import Game, Piece, Move, Space, Player
import main

white, black = main.PLAYERS

def get_king_move(player, end_space):
    return Move(Piece('king', player), Space(end_space[0], 4),
                Space(*end_space), None)

class TestCastling(unittest.TestCase):
    def setUp(self):
        board = main.create_empty_board()
        board[(0, 0)] = board[(0, 7)] = Piece('rook', white)
        board[(7, 0)] = board[(7, 7)] = Piece('rook', black)
        board[(0, 4)] = Piece('king', white)
        board[(7, 4)] = Piece('king', black)
        self.game = Game(board=board,
                         castle_rights=main.CASTLE_RIGHTS,
                         players=main.PLAYERS)

    def switch_players(self):
        self.game.player, self.game.other = black, white

    def test_kingside_castle_permitted_white(self):
        self.assertIn(get_king_move(white, (0, 6)), self.game.find_moves())

    def test_queenside_castle_permitted_white(self):
        self.assertIn(get_king_move(white, (0, 2)), self.game.find_moves())

    def test_kingside_castle_permitted_black(self):
        self.switch_players()
        self.assertIn(get_king_move(black, (7, 6)), self.game.find_moves())

    def test_queenside_castle_permitted_black(self):
        self.switch_players()
        self.assertIn(get_king_move(black, (7, 2)), self.game.find_moves())

    def test_castle_not_permitted_when_king_in_check(self):
        self.game.board[(3, 4)] = Piece('rook', black)
        self.assertNotIn(get_king_move(white, (0, 2)), self.game.find_moves())
    
    def test_normal_king_move_permitted_when_king_in_check(self):
        self.game.board[(3, 4)] = Piece('rook', black)
        self.assertIn(get_king_move(white, (0, 5)), self.game.find_moves())

    def test_castle_not_permitted_when_king_passes_through_check(self):
        self.game.board[(3, 5)] = Piece('rook', black)
        self.assertNotIn(get_king_move(white, (0, 6)), self.game.find_moves())

    def test_castle_not_permitted_when_king_ends_in_check(self):
        self.game.board[(3, 6)] = Piece('rook', black)
        self.assertNotIn(get_king_move(white, (0, 6)), self.game.find_moves())

    def test_castle_not_permitted_when_piece_intervenes_between_start_and_end_space(self):
        self.game.board[(0, 5)] = Piece('bishop', white)
        self.assertNotIn(get_king_move(white, (0, 6)), self.game.find_moves())

    def test_castle_not_permitted_when_piece_is_on_end_space(self):
        self.game.board[(0, 6)] = Piece('bishop', black)
        self.assertNotIn(get_king_move(white, (0, 6)), self.game.find_moves())

    def test_castle_not_permitted_when_piece_intervenes_between_start_space_and_rook_space(self):
        self.game.board[(0, 1)] = Piece('bishop', white)
        self.assertNotIn(get_king_move(white, (0, 2)), self.game.find_moves())

    def test_castle_not_permitted_when_castling_rights_have_been_lost_kingside(self):
        self.game.castle_rights = {white: {'queenside'}, black: {}}
        self.assertNotIn(get_king_move(white, (0, 6)), self.game.find_moves())

    def test_castle_not_permitted_when_castling_rights_have_been_lost_queenside(self):
        self.game.castle_rights = {white: {}, black: {}}
        self.assertNotIn(get_king_move(white, (0, 2)), self.game.find_moves())

    def test_kingside_castle_still_permitted_when_only_queenside_rights_have_been_lost(self):
        self.game.castle_rights = {white: {'kingside'}, black: {}}
        self.assertIn(get_king_move(white, (0, 6)), self.game.find_moves())

    def test_rook_moves_correctly_in_kingside_castle(self):
        game = self.game.move(get_king_move(white, (0, 6)))
        self.assertEqual(game.board.pop((0, 5)), self.game.board.pop((0, 7)))
        self.assertIsNone(game.board.pop((0, 7)))
        self.assertEqual(game.board.pop((0, 0)), Piece('rook', white))

    def test_rook_moves_correctly_in_queenside_castle(self):
        game = self.game.move(get_king_move(white, (0, 2)))
        self.assertEqual(game.board.pop((0, 3)), self.game.board.pop((0, 0)))
        self.assertIsNone(game.board.pop((0, 0)))
        self.assertEqual(game.board.pop((0, 7)), Piece('rook', white))

    def test_castle_eliminates_castling_rights(self):
        self.switch_players()
        self.assertEqual(self.game.castle_rights[black], {'kingside',
                                                          'queenside'})
        game = self.game.move(get_king_move(black, (7, 6)))
        self.assertEqual(game.castle_rights[black], set())

    def test_rook_move_eliminates_appropriate_castling_rights(self):
        self.switch_players()
        self.assertEqual(self.game.castle_rights[black], {'kingside',
                                                          'queenside'})
        game = self.game.move(Move(
            Piece('rook', black),
            Space(7, 0),
            Space(5, 0),
            None,
        ))
        self.assertEqual(game.castle_rights[black], {'kingside'})

class TestEnPassant(unittest.TestCase):
    def setUp(self):
        board = main.create_empty_board()
        self.white_pawn_space = Space(1, 3)
        self.black_pawn_space = Space(3, 4)
        board[self.white_pawn_space] = Piece('pawn', white)
        board[self.black_pawn_space] = Piece('pawn', black)
        # Add kings (otherwise `king_is_in_check` will cause program to crash)
        board[(0, 4)] = Piece('king', white)
        board[(7, 4)] = Piece('king', black)
        self.game = Game(board=board,
                         castle_rights=main.CASTLE_RIGHTS,
                         players=main.PLAYERS)

    def advance_pawn(self):
        self.game = self.game.move(Move(
            Piece('pawn', white),
            self.white_pawn_space,
            Space(self.white_pawn_space.row + 2, self.white_pawn_space.col),
            None,
        ))

    def en_passant_capture(self):
        return Move(self.game.board[self.black_pawn_space],
                    self.black_pawn_space,
                    Space(self.black_pawn_space.row - 1,
                          self.white_pawn_space.col),
                    None)

    def test_en_passant_permitted_on_next_turn(self):
        self.advance_pawn()
        self.assertIn(self.en_passant_capture(),
                      self.game.find_moves())

    def test_en_passant_not_permitted_on_later_turn(self):
        self.advance_pawn()
        self.game = self.game.move(get_king_move(black, Space(7, 5)))
        self.game = self.game.move(get_king_move(white, Space(0, 5)))
        self.assertNotIn(self.en_passant_capture(),
                         self.game.find_moves())

    def test_en_passant_captures_pawn(self):
        self.advance_pawn()
        new_white_pawn_space = Space(self.white_pawn_space.row + 2,
                                     self.white_pawn_space.col)
        self.assertEqual(self.game.board[new_white_pawn_space],
                         Piece('pawn', white))
        self.game = self.game.move(self.en_passant_capture())
        self.assertIsNone(self.game.board[new_white_pawn_space])
        
if __name__ == '__main__':
    unittest.main()
