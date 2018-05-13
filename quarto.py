#!/usr/bin/env python3
# quarto.py
# Author: Quentin Lurkin; IA edited by Bernard Tourneur & Jonathan Miel
# Version: March 29, 2018

import argparse
import socket
import sys
import random
import json
import copy
from easyAI import TwoPlayersGame, Human_Player, AI_Player, Negamax, id_solve

import game

class QuartoState(game.GameState):
    '''Class representing a state for the Quarto game.'''
    def __init__(self, initialstate=None, currentPlayer=None):
        self.__player = 0
        random.seed()
        if initialstate is None:
            pieces = []
            for shape in ['round', 'square']:
                for color in ['dark', 'light']:
                    for height in ['low', 'high']:
                        for filling in ['empty', 'full']:
                            pieces.append({
                                'shape': shape,
                                'color': color,
                                'height': height,
                                'filling': filling
                            })
            initialstate = {
                'board': [None] * 16,
                'remainingPieces': pieces,
                'pieceToPlay': None,
                'quartoAnnounced': False
            }

        if currentPlayer is None:
            currentPlayer = random.randrange(2)

        super().__init__(initialstate, currentPlayer=currentPlayer) #utilise l'init de GameState

    def applymove(self, move):
        #{pos: 8, quarto: true, nextPiece: 2}
        stateBackup = copy.deepcopy(self._state)
        try:
            state = self._state['visible']
            if state['pieceToPlay'] is not None:
                try:
                    if state['board'][move['pos']] is not None:
                        raise game.InvalidMoveException('The position is not free')
                    state['board'][move['pos']] = state['remainingPieces'][state['pieceToPlay']]
                    del(state['remainingPieces'][state['pieceToPlay']])
                except game.InvalidMoveException as e:
                    raise e
                except:
                    print ('position move : ', move['pos'])
                    raise game.InvalidMoveException("Your move should contain a \"pos\" key in range(16)")

            if len(state['remainingPieces']) > 0:
                try:
                    state['pieceToPlay'] = move['nextPiece']
                except:
                    raise game.InvalidMoveException("You must specify the next piece to play")
            else:
                state['pieceToPlay'] = None

            if 'quarto' in move:
                state['quartoAnnounced'] = move['quarto']
                winner = self.winner()
                if winner is None or winner == -1:
                    raise game.InvalidMoveException("There is no Quarto !")
            else:
                state['quartoAnnounced'] = False
        except game.InvalidMoveException as e:
            self._state = stateBackup
            raise e

    
    def _same(self, feature, elems):
        try:
            elems = list(map(lambda piece: piece[feature], elems))
        except:
            return False
        return all(e == elems[0] for e in elems)

    def _quarto(self, elems):
        return self._same('shape', elems) or self._same('color', elems) or self._same('filling', elems) or self._same('height', elems)
    
    def winner(self):
        state = self._state['visible']
        board = state['board']
        player = self._state['currentPlayer']

        # 00 01 02 03
        # 04 05 06 07
        # 08 09 10 11
        # 12 13 14 15

        if state['quartoAnnounced']:
            # Check horizontal and vertical lines
            for i in range(4):
                if self._quarto([board[4 * i + e] for e in range(4)]):
                    return player
                if self._quarto([board[4 * e + i] for e in range(4)]):
                    return player
            # Check diagonals
            if self._quarto([board[5 * e] for e in range(4)]):
                return player
            if self._quarto([board[3 + 3 * e] for e in range(4)]):
                return player
        return None if board.count(None) == 0 else -1
    
    def displayPiece(self, piece):
        if piece is None:
            return " " * 6
        bracket = ('(', ')') if piece['shape'] == "round" else ('[', ']')
        filling = 'E' if piece['filling'] == 'empty' else 'F'
        color = 'L' if piece['color'] == 'light' else 'D'
        format = ' {}{}{}{} ' if piece['height'] == 'low' else '{0}{0}{1}{2}{3}{3}'
        return format.format(bracket[0], filling, color, bracket[1])

    def prettyprint(self):
        state = self._state['visible']

        print('Board:')
        for row in range(4):
            print('|', end="")
            for col in range(4):
                print(self.displayPiece(state['board'][row*4+col]), end="|")
            print()
        
        print('\nRemaining Pieces:')
        print(", ".join([self.displayPiece(piece) for piece in state['remainingPieces']]))

        if state['pieceToPlay'] is not None:
            print('\nPiece to Play:')
            print ('\n nbrofremaining : ', len (state['remainingPieces']))
            print ('\n index : ', state['pieceToPlay'])
            print(self.displayPiece(state['remainingPieces'][state['pieceToPlay']]))

    def nextPlayer(self):
        self._state['currentPlayer'] = (self._state['currentPlayer'] + 1) % 2


class QuartoServer(game.GameServer):
    '''Class representing a server for the Quarto game.'''
    def __init__(self, verbose=False):
        super().__init__('Quarto', 2, QuartoState(), verbose=verbose)
    
    def applymove(self, move):
        try:
            move = json.loads(move)
        except:
            raise game.InvalidMoveException('A valid move must be a valid JSON string')
        else:
            self._state.applymove(move)


class QuartoClient(game.GameClient):
    '''Class representing a client for the Quarto game.'''
    def __init__(self, name, server, verbose=False):
        super().__init__(server, QuartoState, verbose=verbose)
        self.__name = name

    def _handle(self, message):
        pass

    def _nextmove(self, state):
        visible = state._state['visible']
        move = {}
    
        history = QuartoIA(state).play()
        move = history[0][1]
        # apply the move to check for quarto
        # applymove will raise if we announce a quarto while there is not
        move['quarto'] = True
        try:
            state.applymove(move)
        except:
            del(move['quarto'])
        
        # send the move
        return json.dumps(move)
            

class QuartoIA (TwoPlayersGame) : 
    def __init__ (self, state):
        ai_algo = Negamax (2)
        self.players = [AI_Player(ai_algo), AI_Player(ai_algo)]
        self.__state = copy.deepcopy (state)
        self.board = self.__state._state['visible']['board'] 
        self.nplayer = self.__state._state['currentPlayer'] + 1

    def make_move (self, move):
        state =  self.__state._state['visible']
        '''if state['pieceToPlay'] is not None :
            print (len(state['remainingPieces']),state['pieceToPlay'])
            self.board[move['pos']] = state['remainingPieces'][state['pieceToPlay']]
        state['pieceToPlay'] = move['nextPiece']'''
        self.__state.applymove (move)

    def lose (self):
        # Check horizontal and vertical lines
        for i in range(4):
            if self.__state._quarto([self.board[4 * i + e] for e in range(4)]) and self.__state._state['currentPlayer'] + 1 == self.nopponent :
                return True
            if self.__state._quarto([self.board[4 * e + i] for e in range(4)]) and self.__state._state['currentPlayer'] + 1 == self.nopponent :
                return True
        # Check diagonals
        if self.__state._quarto([self.board[5 * e] for e in range(4)]) and self.__state._state['currentPlayer'] + 1 == self.nopponent:
            return True
        if self.__state._quarto([self.board[3 + 3 * e] for e in range(4)]) and self.__state._state['currentPlayer'] + 1 == self.nopponent:
            return True
        return False
    
    def is_over (self) :
        return self.possible_moves == [] or self.lose()
     
    def scoring (self):
        return -100 if self.lose() else 0

    def possible_moves (self):
        visible = self.__state._state['visible']
        if self.__state._state['visible']['pieceToPlay'] is not None :
            return [{'nextPiece' : i,'pos':j } 
                        for i in range(len(visible['remainingPieces']))
                        for j,e in enumerate(visible['board']) if e == None ]
        else :
            return [{'nextPiece' : i} 
                        for i in range(len(visible['remainingPieces']))]
    
    def show (self):
        pass

class QuartoGame (TwoPlayersGame) : 
    def __init__ (self, players):
        self.players = players
        self.board = self.__state._state['visible']['board'] 
        self.nplayer = self.__state._state['currentPlayer'] + 1

    def make_move (self, move):
        state =  self.__state._state['visible']
        if state['pieceToPlay'] is not None :
            self.board[move['pos']] = state['remainingPieces'][state['pieceToPlay']]
        state['pieceToPlay'] = move['nextPiece']
        del state['remainingPieces'][state['pieceToPlay']]

    def lose (self):
        # Check horizontal and vertical lines
        for i in range(4):
            if self.__state._quarto([self.board[4 * i + e] for e in range(4)]) and self.__state._state['currentPlayer'] + 1 == self.nopponent :
                return True
            if self.__state._quarto([self.board[4 * e + i] for e in range(4)]) and self.__state._state['currentPlayer'] + 1 == self.nopponent :
                return True
        # Check diagonals
        if self.__state._quarto([self.board[5 * e] for e in range(4)]) and self.__state._state['currentPlayer'] + 1 == self.nopponent:
            return True
        if self.__state._quarto([self.board[3 + 3 * e] for e in range(4)]) and self.__state._state['currentPlayer'] + 1 == self.nopponent:
            return True
        return False
    
    def is_over (self) :
        return self.possible_moves == [] or self.lose()
     
    def scoring (self):
        return -100 if self.lose() else 0

    def possible_moves (self):
        visible = self.__state._state['visible']
        if self.__state._state['visible']['pieceToPlay'] is not None :
            return [{'nextPiece' : i,'pos':j } 
                        for i in range(len(visible['remainingPieces']))
                        for j,e in enumerate(visible['board']) if e == None ]
        else :
            return [{'nextPiece' : i} 
                        for i in range(len(visible['remainingPieces']))]
    
    def show (self):
        pass

if __name__ == '__main__' :
    # Create the top-level parser
    parser = argparse.ArgumentParser(description='Quarto game')
    subparsers = parser.add_subparsers(description='server client', help='Quarto game components', dest='component')
    # Create the parser for the 'server' subcommand
    server_parser = subparsers.add_parser('server', help='launch a server')
    server_parser.add_argument('--host', help='hostname (default: localhost)', default='localhost')
    server_parser.add_argument('--port', help='port to listen on (default: 5000)', default=5000)
    server_parser.add_argument('--verbose', action='store_true')
    # Create the parser for the 'client' subcommand
    client_parser = subparsers.add_parser('client', help='launch a client')
    client_parser.add_argument('name', help='name of the player')
    client_parser.add_argument('--host', help='hostname of the server (default: localhost)', default='127.0.0.1')
    client_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    client_parser.add_argument('--verbose', action='store_true')
    # Parse the arguments of sys.args
    args = parser.parse_args()
    if args.component == 'server':
        QuartoServer(verbose=args.verbose).run()
    else:
        QuartoClient(args.name, (args.host, args.port), verbose=args.verbose)