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
#from simpleai import SearchProblem, greedy

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

    def isBadPiece (self, state, pieceIndex, prevMove): # a bad piece makes the oponent win
        stateCopy = copy.deepcopy (state) 
        if (prevMove >=0):                              #allows to take into account the move the player just made
            prevMove = {'pos': prevMove, 'nextPiece':0}
            stateCopy.applymove (prevMove)  

        nextPiece = state._state['visible']['remainingPieces'][pieceIndex]
        for i in range(4):
            elements = [stateCopy._state['visible']['board'][4 * i + e] for e in range(4)]
            try : 
                elements[elements.index (None)] = nextPiece # put the next piece in an available spot for a combinaison
            except ValueError : # ValueError is raised if no None available in the list of elements => all spots are taken 
                pass
            if stateCopy._quarto(elements):
                return True
            elements = [stateCopy._state['visible']['board'][4 * e + i] for e in range(4)]
            try :
                elements[elements.index (None)] = nextPiece
            except ValueError :
                pass
            if stateCopy._quarto(elements):
                return True
            # Check diagonals
            elements = [stateCopy._state['visible']['board'][5 * e] for e in range(4)]
            try:
                elements[elements.index (None)] = nextPiece
            except ValueError :
                pass
            if stateCopy._quarto(elements):
                return True
            elements = [stateCopy._state['visible']['board'][3 + 3 * e] for e in range(4)]
            try :
                elements[elements.index (None)] = nextPiece
            except ValueError:
                pass
            if stateCopy._quarto(elements):
                return True
        del (stateCopy)
        return False 
    
    
    def winningMove (self, state, pieceToPlay): # recognise a move that ends the game
        stateCopy = copy.deepcopy (state) 
        
        for i in range(4):
            #Check lines
            elements = [stateCopy._state['visible']['board'][4 * i + e] for e in range(4)] 
            try : 
                winPos = 4 * i + elements.index (None) # position for the winning move ; if a quarto move is possible,
                elements[elements.index (None)] = pieceToPlay    # it will be in an empty space of the grid 
            except ValueError : 
                pass
            if stateCopy._quarto(elements):
                return winPos
            #Check columns
            elements = [stateCopy._state['visible']['board'][4 * e + i] for e in range(4)] 
            try :
                winPos = 4 * elements.index (None) + i
                elements[elements.index (None)] = pieceToPlay
            except ValueError :
                pass
            if stateCopy._quarto(elements):
                return winPos
            # Check diagonals
            elements = [stateCopy._state['visible']['board'][5 * e] for e in range(4)]
            try:
                winPos = 5 * elements.index (None)
                elements[elements.index (None)] = pieceToPlay
            except ValueError :
                pass
            if stateCopy._quarto(elements):
                return winPos
            elements = [stateCopy._state['visible']['board'][3 + 3 * e] for e in range(4)]
            try :
                winPos = 3 + 3 * elements.index (None)
                elements[elements.index (None)] = pieceToPlay
            except ValueError:
                pass
            if stateCopy._quarto(elements):
                return winPos
        del (stateCopy)
        return None


    def moveStrategies (self, state): # homemade strategies
        stateCopy = copy.deepcopy (state) 
        pieceToPlay = stateCopy._state['visible']['pieceToPlay']
        board = stateCopy._state['visible']['board']
        nbrOfPieces = len (stateCopy._state['visible']['remainingPieces'])

        if self.winningMove(stateCopy, pieceToPlay) is not None :           # First, check if there is a winning move available
                return self.winningMove(stateCopy, pieceToPlay) 

        dangerousPieces = 0
        dangerousPos = -1
        for pI in range (nbrOfPieces):                                      # Then, check if you are in a dangerous situation where 
            piece = stateCopy._state['visible']['remainingPieces'][pI]      # you need to block the opponent with your move because there
            if self.winningMove (stateCopy, piece) is not None :            # will be no other way than to give a winning piece afterwards
                dangerousPieces +=1
                dangerousPos = self.winningMove (stateCopy, piece)          # You can only cover one dangerous position (the last of the loop),f 
        if dangerousPieces == nbrOfPieces :                                 # if there are more, you have lost anyway
            return dangerousPos
        
        del(stateCopy)
        return None 

            

    def _nextmove(self, state):
        visible = state._state['visible']
        move = {}
        movePos = -1

        # select the first free position
        if visible['pieceToPlay'] is not None:
            if self.moveStrategies (state) is not None :
                move['pos'] = self.moveStrategies (state)
            else : 
                move['pos'] =  visible['board'].index(None)
            movePos = move['pos']

        # select the first remaining piece that won't let the oponent win
        nbrOfPieces = len(visible['remainingPieces'])
        for p in range (nbrOfPieces):
            print ('p : ', p,' = ', visible['remainingPieces'][p], self.isBadPiece (state, p, movePos) )
            if not self.isBadPiece (state, p, movePos):
                move ['nextPiece'] = p
                break
            elif (p == (nbrOfPieces-1)): # after testing all possible solutions, if none are good moves,
                move ['nextPiece'] = p   # you probably lost => choose the last piece anyway 
                                         # (it doesn't make a difference whether it's a good or a bad piece)

        # apply the move to check for quarto
        # applymove will raise if we announce a quarto while there is not
        move['quarto'] = True
        try:
            state.applymove(move)
        except:
            del(move['quarto'])
        
        # send the move
        return json.dumps(move)


if __name__ == '__main__':
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