# main.py
# Authors: Bernard Tourneur & Jonathan Miel
# Version: May 2, 2018

import argparse
import socket
import sys

import game

class QuatroState (game.GameState):
    def __init__(self, initialstate=[None] * 16):
        super().__init__(initialstate)
    
    def update(self, coord, pieceType): #change the state of the game by adding a piece to it
        state = self._state ['visible'] #contains a list of states of all positions on the grid
        line, column = coord
        index = 4 * line + column
        if not (0 <= line <= 3 and 0 <= column <= 3):
            raise game.InvalidMoveException('The move is outside of the board')
        if state[index] is not None:
            raise game.InvalidMoveException('The specified cell is not empty')
        state[index] = pieceType

    def _checkelems(self, state, elems): #check if a list of elems (e.g. a row or column of the grid) has the same state (piece)
        return state is not None and (e == state for e in elems)

    def winner(self):
        state = self._state ['visible']
        #check lines and columns for a row
        for i in range (4):
            if self._checkelems(state[4 * i], [state[4 * i + e] for e in range(4)]): 
                return state[4 * i]
            if self._checkelems(state[i], [state[4 * e + i] for e in range(4)]):
                return state[i]
        # Check diagonals
        if self._checkelems(state[0], [state[5 * e] for e in range(4)]):
            return state[0]
        if self._checkelems(state[3], [state[12 - 3 * e] for e in range(4)]):
            return state[3]
        return None if state.count(None) == 0 else -1
        
    def prettyprint(self): #???
        pass 


class QuatroServer (game.GameServer):
    def __init__(self, verbose=False):
        super().__init__('Quatro', 2, QuatroState(), verbose=verbose)

    def applymove (self, move):
        pass


class QuatroClient (game.GameClient):
    def __init__(self, name, server, verbose=False):
        super().__init__(server, QuatroState, verbose=verbose)
        self.__name = name

    def _handle (self, message):
        pass

    def _nextmove (self, state):
        pass


if __name__ == '__main__':
    # Create the top-level parser
    parser = argparse.ArgumentParser(description='Quatro game')
    subparsers = parser.add_subparsers(description='server client', help='Quatro game components', dest='component')
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
        TicTacToeServer(verbose=args.verbose).run()
    else:
        TicTacToeClient(args.name, (args.host, args.port), verbose=args.verbose)