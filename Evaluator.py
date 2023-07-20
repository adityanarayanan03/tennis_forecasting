import pandas as pd

from PlayerDB import PlayerDB
from Match import Match

import logging
from CustomFormatter import ch

class Evaluator:
    def __init__(self, dataset, name = 'default'):
        self.dataset = dataset
        self.db = PlayerDB()
        self.db.populate_from_csv(self.dataset)

        self.name = name
        self.SIM_METHODS = {'server_chains'}

        self.logger = logging.getLogger(f"Evaluator {name}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)

    def evaluate(self, sim_method='server_chains'):
        if sim_method not in self.SIM_METHODS:
            self.logger.error(f"Received unknown sim_method {sim_method}")
            return
    
        if sim_method == 'server_chains':
            return self._evaluate_server_chains()

    def _evaluate_server_chains(self):
        df = pd.read_csv(self.dataset)
        
        num_correct = 0
        accuracy = 0
        #iterate over the rows and create PlayerMC for each person
        for idx, row in df.iterrows():
            server1 = row.loc['server1']
            server2 = row.loc['server2']

            #simulate a match between server1 and server2
            player_1_mc = self.db.get_player_mc(server1)
            player_2_mc = self.db.get_player_mc(server2)

            #Create a match between the two players
            match = Match(player_1_mc, player_2_mc)
            p, interval = match.sample_match_with_server_chains(confidence_level=.80, max_width=.05, min_trials=30)

            prediction = 1 if p > 0.5 else 2
            self.logger.debug(f"{(server1, server2, prediction, row['winner'])}, {accuracy:.3f}")

            #Check if our prediction was right
            if prediction == row['winner']:
                num_correct += 1
            
            accuracy = num_correct / (idx+1)
            
        return accuracy

def t_evaluate_with_server_chains(dataset):
    evaluator = Evaluator(dataset)
    accuracy = evaluator.evaluate()
    logger.info(f'Accuracy on dataset is {accuracy}')

if __name__ == '__main__':
    logger = logging.getLogger('Evaluator.py')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    
    t_evaluate_with_server_chains('tennis_pointbypoint/pbp_matches_atp_main_current.csv')