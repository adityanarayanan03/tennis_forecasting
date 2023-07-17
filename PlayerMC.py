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
        
        #Need to retain both matrix and counts so we can update probabilities
        self.transition_matrix = np.zeros((20, 20))
        self.transition_counts = np.zeros((20, 20))
        
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
    
    def simulate(self):
        raise NotImplemented
    
    def __str__(self):
        to_return = f"Player: {self.player_name}\n"
        to_return += str(self.transition_counts)

        return to_return