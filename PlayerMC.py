import numpy as np

import logging
from CustomFormatter import ch

#State transitions and state mapping are used for all PlayerMC's. No need to waste memory.
STATE_TRANSITIONS = {0:[1,2], 1:[3,4], 2:[4,5], 3:[6,7], 4:[7,8],
                    5:[8,9], 6:[18,10], 7:[10,11], 8:[11,12], 9:[12,19],
                    10:[18,13], 11:[13,14], 12:[14,19], 13:[18,15], 14:[15,17],
                    15:[16,17], 16:[18,15], 17:[15,19], 18:[0,0], 19:[0,0]}

STATE_MAPPING = {0:'0 - 0', 1:'15 - 0', 2:'0 - 15', 3:'30 - 0', 4:'15 - 15', 5:'0 - 30',
                6:'40 - 0', 7:'30 - 15', 8:'15 - 30', 9:'0 - 40', 10:'40 - 15', 11:'30 - 30',
                12:'15 - 40', 13:'40 - 30', 14:'30 - 40', 15:'40 - 40', 16:'Ad - 40', 17:'40 - Ad',
                18:'W', 19:'L'}

class PlayerMC:
    '''
    Mostly just a container class for the matrix representation
    of a markov chain for each player. Keeping as separate class
    in case I need to add metadata later
    '''
    def __init__(self, name):
        
        #Need to retain both matrix and counts so we can update probabilities
        self.transition_matrices = {'s': np.zeros((20, 20)), 'r': np.zeros((20, 20))}
        self.transition_counts = {'s': np.zeros((20, 20)), 'r': np.zeros((20, 20))}
        self.point_win_probability = {'s': 0, 'r': 0}
        
        self.player_name = name

        self.logger = logging.getLogger("PlayerMC")
        self.logger.setLevel(logging.WARNING)
        self.logger.addHandler(ch)
    
    def update_from_pbp(self, pbp, is_server=True):
        '''
        Should be called with a pbp for every game played
        (regardless of who serves or receives)
        '''
        if len(pbp) == 1 or len(pbp) == 2:
            self.logger.debug("Tiebreak Detected. Ignoring.")
        else:
            self.logger.debug(f"Updating Markov Chain for player {self.player_name} with pbp {pbp}")

            state = 0
            for point in pbp:
                next_state = state
                if point == 'S' or point == 'A':
                    next_state = STATE_TRANSITIONS[state][0]
                
                elif point == 'R' or point == 'D':
                    next_state = STATE_TRANSITIONS[state][1]
                
                else:
                    self.logger.warn(f"Got unknown character {point} in pbp")
                    continue

                if is_server:
                    self.transition_counts['s'][state][next_state] += 1
                else:
                    self.transition_counts['r'][state][next_state] += 1

                state = next_state
            
            #self.logger.debug(f"At the end of update, transition counts are {self.transition_counts}")
            self._compute_transition_matrices()
            self._compute_point_win_probability()
    
    def _compute_point_win_probability(self) -> float:
        '''
        Computes the total probability of winning a point on serve or return
        Used to simulate tiebreaks
        Returns win probability dictionary if successful, otherwise returns -1
        '''
        for selector in ['s', 'r']:
            wins = 0
            losses = 0
            transition_counts = self.transition_counts[selector]
            for state in STATE_TRANSITIONS:
                if selector == 's':
                    wins += transition_counts[state][STATE_TRANSITIONS[state][0]]
                    losses += transition_counts[state][STATE_TRANSITIONS[state][1]]
                else:
                    #In out state transitions, the first index is LOSSES when returning
                    wins += transition_counts[state][STATE_TRANSITIONS[state][1]]
                    losses += transition_counts[state][STATE_TRANSITIONS[state][0]]
            
            if wins+losses == 0:
                #self.logger.warn(f"Player {self.player_name} has no recorded points on {selector}. Failing to compute win probability")
                return -1
            else:
                self.point_win_probability[selector] = wins/(wins + losses)
        
        return self.point_win_probability

    def _compute_transition_matrices(self):
        #Compute the markov chain matrices for both serving and receiving
        for selector in ['s', 'r']:
            sums = self.transition_counts[selector].sum(axis=1, keepdims = True)
            for idx in range(len(sums)):
                if sums[idx][0] == 0:
                    sums[idx][0] = 1
            self.transition_matrices[selector] = self.transition_counts[selector]/sums

    def simulate_game(self, is_server=True) -> bool:
        '''
        Simulates a single game of player serving.

        Returns True if player wins, False otherwise
        '''
        choices = np.arange(20)
        state = 0
        path = ""
        while True:
            if is_server:
                probabilities = self.transition_matrices['s'][state]
            else:
                probabilities = self.transition_matrices['r'][state]

            if np.sum(probabilities) != 1:
                self.logger.error(f"Player {self.player_name}: Probabilities do not sum to 1. Printing row of transition matrix")
                self.logger.error(f"{probabilities}, (state {state})")

                self.logger.warning(f"Using total win percent on s/r approximation.")

                if is_server:
                    p = self.point_win_probability['s']
                else:
                    p = self.point_win_probability['r']
                probabilities[STATE_TRANSITIONS[state][0]] = p
                probabilities[STATE_TRANSITIONS[state][1]] = 1 - p

            next_state = np.random.choice(choices, p = probabilities)

            path += f"{STATE_MAPPING[next_state]}, "

            if next_state == 18:
                return True if is_server else False
            elif next_state == 19:
                return False if is_server else True

            state = next_state

    def simulate_point(self, is_server=True) -> bool:
        '''
        Uses the total probability of winning on serve to simulate a single point.
        Returns true if player won the point, false otherwise
        '''
        if is_server:
            p = self.point_win_probability['s']
        else:
            p = self.point_win_probability['r']
            
        return np.random.choice([True, False], p = [p, 1 - p])

    
    def __str__(self):
        to_return = f"Player: {self.player_name} Serve Matrix\n"
        to_return += str(self.transition_counts['s'])
        to_return += "\n\n"

        to_return += f"Player: {self.player_name} Return Matrix\n"
        to_return += str(self.transition_counts['r'])

        return to_return