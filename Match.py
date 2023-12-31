import itertools
import collections
from scipy.stats import norm
import numpy as np

from PlayerDB import PlayerDB
from PlayerMC import PlayerMC

import logging
from CustomFormatter import ch

class Match:
    '''
    Base match class that all other simulatino methods will inherit from
    '''
    def __init__(self, server1, server2, match_format = 'tour', court = 'hard'):
        
        if match_format == 'tour':
            self.sets_to_win = 2
        else:
            self.sets_to_win = 3
        
        self.players = {1: server1, 2: server2}
        self.court = court
    
    def _other_player(self, server):
        return 2 if server == 1 else 1




class ServerChainSimulator(Match):
    '''
    Match where each game is simulated using only server's markov chain
    '''
    def __init__(self, server1, server2, match_format = 'tour', court = 0):
        '''
        Format and court are unused right now
        '''
        super().__init__(server1, server2, match_format, court)

        self.logger = logging.getLogger("Match Class")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)
    
    def simulate_tiebreak(self, pts, serve_order):
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
                if server.simulate_point(is_server = True):
                    score[server_idx] += 1
                else:
                    score[self._other_player(server_idx)] += 1
                
                #Check for winners
                if score[1] >= pts and score[1] - score[2] >= 2:
                    return 1, score
                elif score[2] >= pts and score[2] - score[1] >= 2:
                    return 2, score
                
                #self.logger.debug(f'Score is currently {score}')
                
            
            #swap the server
            server_idx = self._other_player(server_idx)
    
    def simulate_game(self, server_idx):
        return self.players[server_idx].simulate_game()

    def simulate_set(self, serve_order):
        '''
        Returns winner, score where winner is an index of player and 
        score is set score as a dictionary.
        '''
        score = {1:0, 2:0}
        server_idx = serve_order
        for serve_idx in itertools.count():
            server = self.players[server_idx]
            
            #Do we go to tiebreak?
            if score[1] == 6 and score[2] == 6:
                tb_winner, tb_score = self.simulate_tiebreak(7, server_idx)
                score[tb_winner] += 1
                return tb_winner, score
            
            #Simulate normal game (not tiebreak)
            if self.simulate_game(server_idx):
                score[server_idx] += 1
            else:
                score[self._other_player(server_idx)] += 1

            #Did somebody win on that game?
            if score[1] >= 6 and score[1] - score[2] >= 2:
                return 1, score
            elif score[2] >= 6 and score[2] - score[1] >= 2:
                return 2, score

            #rotate servers
            server_idx = self._other_player(server_idx)

    def simulate_match(self):
        '''
        Returns winner, score where winner is an index of player 
        and score is a list of set scores.
        '''

        set_count = {1:0, 2:0}
        score = []
        server_idx = 1

        for set_idx in itertools.count():
            #Simulate a set
            set_winner, set_score = self.simulate_set(server_idx)

            #Update score counting variables
            set_count[set_winner] += 1
            score.append(set_score)

            #check for wins
            if set_count[1] == self.sets_to_win:
                return 1, set_count, score
            elif set_count[2] == self.sets_to_win:
                return 2, set_count, score

            #update server_idx appropriately
            if (set_score[1] + set_score[2])%2 == 0:
                server_idx = 1
            else:
                server_idx = 2

    def sample_match(self, confidence_level = 0.95, max_width = 0.01, min_trials = 30):
        '''
        Makes repeated simulatins of a match until confidence interval of 
        given confidence is less than or equal to max_width
        '''
        #Compute the inverse normal of confidence level first (2 sided)
        z = norm.ppf(confidence_level + (1-confidence_level)/2)
        #self.logger.debug(f"z is {z}")

        #Simulate a bunch of trials
        p = 0
        wins = 0
        history = []
        for idx in itertools.count():
            winner, set_count, score = self.simulate_match()
            history.append(set_count[1] - set_count[2])

            if winner == 1:
                wins += 1
            
            p = wins/(idx + 1)
            interval_width = z * np.sqrt((p * (1-p))/(idx+1))

            #self.logger.info(f"At iteration {idx} p is currently {p:.3f} and total interval width is {interval_width:.5f}")

            if interval_width <= max_width and idx > min_trials:
                return p, interval_width

        

def t_simulate_set(name_1, name_2):
    '''
    Returns 1 if runs til end. 
    Note: Doesn't validate output itself.
    '''
    from PlayerDB import PlayerDB

    db = PlayerDB()
    db.populate_from_csv('tennis_pointbypoint/pbp_matches_atp_main_current.csv')

    player_1 = db.get_player_mc(name_1)
    player_2 = db.get_player_mc(name_2)

    #Simulate a match between player1 and player2
    simulator = ServerChainSimulator(player_1, player_2)
    set_winner, set_score = simulator.simulate_set(1)
    print(f'Set won by player {set_winner} with score {set_score}')
    return 1

def t_simulate_match(name_1, name_2):
    from PlayerDB import PlayerDB

    db = PlayerDB()
    db.populate_from_csv('tennis_pointbypoint/pbp_matches_atp_main_current.csv')

    player_1 = db.get_player_mc(name_1)
    player_2 = db.get_player_mc(name_2)

    simulator = ServerChainSimulator(player_1, player_2, match_format='grand slam')
    winner, set_count, score = simulator.simulate_match()
    print(f"Match won by player {winner}, {set_count[winner]} sets to {set_count[simulator._other_player(winner)]}, {score}")

def t_inspect_distribution(name_1, name_2, trials):
    from PlayerDB import PlayerDB
    import matplotlib.pyplot as plt
    import collections

    db = PlayerDB()
    db.populate_from_csv('tennis_pointbypoint/pbp_matches_atp_main_current.csv')

    player_1 = db.get_player_mc(name_1)
    player_2 = db.get_player_mc(name_2)

    match = Match(player_1, player_2, match_format='grand slam')

    #Simulate a bunch of trials
    history = []
    for _ in range(trials):
        winner, set_count, score = match.simulate_match_with_server_chains()
        history.append(set_count[1] - set_count[2])

    #Create a histogram of the trials
    freq_list = collections.Counter(history)

    logger.info(f"Frequency list after simulation is {freq_list}")

    plt.bar(freq_list.keys(), freq_list.values())
    plt.title(f"{name_1} vs {name_2}")
    plt.ylabel("Matches won in simulation")
    plt.xlabel(f"Sets won by {name_1} - sets won by {name_2}")
    plt.show()

def t_sample_match_distribution(name_1, name_2):
    from PlayerDB import PlayerDB
    import matplotlib.pyplot as plt
    import collections

    db = PlayerDB()
    db.populate_from_csv('tennis_pointbypoint/pbp_matches_atp_main_current.csv')

    player_1 = db.get_player_mc(name_1)
    player_2 = db.get_player_mc(name_2)

    match = Match(player_1, player_2, match_format='grand slam')

    p, interval = match.sample_match_with_server_chains()

    logger.info(f"Probability of player 1 winning the match is {p:.3f} +- {interval:.5f}")


if __name__ == '__main__':
    logger = logging.getLogger('Match.py')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    logger.info('Match.py was run directly, running through tests')

    #t_simulate_set('Roger Federer', 'John Isner')
    t_simulate_match('Roger Federer', 'John Isner')
    #t_inspect_distribution('Serena Williams', 'Fangzhou Liu', 1000)
    #t_sample_match_distribution('Roger Federer', 'Rafael Nadal')