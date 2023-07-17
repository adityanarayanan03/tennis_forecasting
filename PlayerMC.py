import numpy as np

import logging
logging.basicConfig()

class PlayerMC:
    '''
    Mostly just a container class for the matrix representation
    of a markov chain for each player. Keeping as separate class
    in case I need to add metadata later
    '''
    def __init__(self, name):
        self.STATE_TRANSITIONS = {0:[1,2], 1:[3,4], 2:[4,5], 3:[6,7], 4:[7,8],
                                  5:[8,9], 6:[18,10], 7:[10,11], 8:[11,12], 9:[12,19],
                                  10:[18,13], 11:[13,14], 12:[14,19], 13:[18,15], 14:[15,17],
                                  15:[16,17], 16:[18,15], 17:[15,19], 18:[0,0], 19:[0,0]}
        
        self.STATE_MAPPING = {0:'0 - 0', 1:'15 - 0', 2:'0 - 15', 3:'30 - 0', 4:'15 - 15', 5:'0 - 30',
                              6:'40 - 0', 7:'30 - 15', 8:'15 - 30', 9:'0 - 40', 10:'40 - 15', 11:'30 - 30',
                              12:'15 - 40', 13:'40 - 30', 14:'30 - 40', 15:'40 - 40', 16:'Ad - 40', 17:'40 - Ad',
                              18:'W', 19:'L'}
        
        #Need to retain both matrix and counts so we can update probabilities
        self.transition_matrix = np.zeros((20, 20))
        self.transition_counts = np.zeros((20, 20))
        self.p_win_on_serve = 0
        
        self.player_name = name

        self.logger = logging.getLogger("PlayerMC")
        self.logger.setLevel(logging.ERROR)
    
    def update_from_pbp(self, pbp):
        if len(pbp) == 1 or len(pbp) == 2:
            self.logger.debug("Tiebreak Detected. Ignoring.")
        else:
            self.logger.debug(f"Updating Markov Chain for player {self.player_name} with pbp {pbp}")

            state = 0
            for point in pbp:
                next_state = state
                if point == 'S' or point == 'A':
                    next_state = self.STATE_TRANSITIONS[state][0]
                
                elif point == 'R' or point == 'D':
                    next_state = self.STATE_TRANSITIONS[state][1]
                
                else:
                    self.logger.warn(f"Got unknown character {point} in pbp")
                    continue

                self.transition_counts[state][next_state] += 1
                state = next_state
            
            #self.logger.debug(f"At the end of update, transition counts are {self.transition_counts}")
            self._compute_probability_matrix()
    
    def _compute_p_win_on_serve(self) -> float:
        '''
        Computes the total probability of winning a point on serve
        Used to simulate tiebreaks
        Returns p_win_on_serve if successful, otherwise returns -1
        '''
        wins = 0
        losses = 0
        for state in self.STATE_TRANSITIONS:
            wins += self.transition_counts[self.STATE_TRANSITIONS[state][0]]
            losses += self.transition_counts[self.STATE_TRANSITIONS[state][1]]
        
        if wins+losses == 0:
            self.logger.warn(f"Player {self.player_name} has no recorded points on serve. Failing to compute p_win_on_serve")
            return -1
        else:
            self.p_win_on_serve = wins/(wins + losses)
            return self.p_win_on_serve

    def _compute_probability_matrix(self):
        sums = self.transition_counts.sum(axis=1, keepdims = True)
        for idx in range(len(sums)):
            if sums[idx][0] == 0:
                sums[idx][0] = 1
        self.transition_matrix = self.transition_counts/sums

    def simulate_game(self) -> bool:
        '''
        Simulates a single game of player serving.

        Returns True if player wins, False otherwise
        '''
        choices = np.arange(20)
        state = 0
        path = ""
        while True:
            probabilities = self.transition_matrix[state]
            #print(probabilities)
            #print(choices)
            next_state = np.random.choice(choices, p = probabilities)

            path += f"{self.STATE_MAPPING[next_state]}, "

            if next_state == 18:
                print(path)
                return True
            elif next_state == 19:
                print(path)
                return False

            state = next_state

    def simulate_point(self) -> bool:
        '''
        Uses the total probability of winning on serve to simulate a single point.
        Returns true if player won the point, false otherwise
        '''
        return np.random.choice([True, False], p = [self.p_win_on_serve, 1 - self.p_win_on_serve])

    
    def __str__(self):
        to_return = f"Player: {self.player_name}\n"
        to_return += str(self.transition_counts)

        return to_return