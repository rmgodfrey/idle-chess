'''
Can read chess matches from chessgames.com and turn them into a file that
can be read by the main program.
'''

import re
from main_temp import ORDINARY_MOVE, CASTLE

MOVE = rf'({ORDINARY_MOVE}|{CASTLE})'

def read_chess_game(file):
    game = open(file + '.txt').read()
    game = re.sub(r'\{.*?\}', '', game, flags=re.DOTALL)
    res = []
    sub = '1.'
    pos = game.find(sub) + len(sub)
    s = game[pos:]
    num = 2
    while True:
        sub = str(num) + '.'
        pos = s.find(sub)
        if pos >= 0:
            res.append(s[:pos])
            s = s[pos + len(sub):]
            num += 1
        else:
            res.append(s)
            break
    res = ''.join(res).replace(' ', '\n')
    res = re.sub(r'\n+', '\n', res).lstrip()
    open(file + '_fixed.txt', 'w').write(res)

if __name__ == '__main__':
    read_chess_game('testgame')
