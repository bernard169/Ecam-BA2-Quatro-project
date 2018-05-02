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
    
    def update(self, coord, player):
        pass
    
    def _checkelems(self, state, elems):
        pass

    def winner(self):
        pass
        
    def prettyprint(self):
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