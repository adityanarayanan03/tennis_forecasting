import itertools

from PlayerDB import PlayerDB
from PlayerMC import PlayerMC

import logging
logging.basicConfig()

class Match:
    '''
    Represents a single match between two players.
    '''
    def __init__(self, server1, server2, match_format = 0, court = 0):
        '''
        Format and court are unused right now
        '''
        self.players = {1: server1, 2: server2}

        self.format = match_format
        self.court = court

        self.logger = logging.getLogger("Match")
        self.logger.setLevel(logging.DEBUG)
    
    def _other_player(self, server):
        '''
        returns the other player from server
        '''
        return 2 if server == 1 else 1
    
    def simulate_tiebreak_with_server_chains(self, pts, serve_order):
        '''
        serve_order of 1 indicates server1 serves first in tiebreak.
        pts is 7 or 10 depending on what kind of tiebreak we simulate

        returns tuple (winner, score)
        '''        
        score = {1:0, 2:0}
        server_idx = serve_order
        for serve_idx in itertools.count():
            if serve_idx == 0:
                serves = 1
            else:
                serves = 2
            
            for _ in range(serves):
                server = self.players[server_idx]
                if server.simulate_point():
                    score[server_idx] += 1
                else:
                    score[self._other_player(server_idx)] += 1
                
                #Check for winners
                if score[1] >= pts and score[1] - score[2] >= 2:
                    return (1, score)
                elif score[2] >= pts and score[2] - score[1] >= 2:
                    return (2, score)
                
                self.logger.debug(f'Score is currently {score}')
                
            
            #swap the server
            server_idx = self._other_player(server_idx)
    
    def simulate_set_with_server_chains(self, server1_mc, server2_mc):
        #Have to go implement tiebreak mc first
        raise NotImplemented

    def simulate_match_with_server_chains(self, db=None, server1_mc=None, server2_mc=None):
        raise NotImplemented
        

        

