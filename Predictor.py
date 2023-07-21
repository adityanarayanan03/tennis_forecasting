import pandas as pd

from PlayerDB import PlayerDB
from Match import Match

import logging
from CustomFormatter import ch

class Predictor:
    '''
    Generic that each type of predictor inherits from
    '''
    def __init__(self, dataset=None) -> None:
        if dataset:
            self.dataset = dataset
            self.df = pd.read_csv(self.dataset)
            self.db = PlayerDB()
            self.db.populate_from_csv(self.dataset)
        else:
            self.dataset = None
            self.df = None
            self.db = PlayerDB()

        self.columns = ['server1', 'server2', 'prediction', 'p', 'true']
        self.raw_data = pd.DataFrame(columns=self.columns)
        self.accuracy = 0

    def save(self, filename):
        '''
        Saves the self.raw_data as a csv at filename
        '''
        pd.DataFrame(self.raw_data).to_csv(filename, index=True)
    
    def load(self, filename):
        self.raw_data = pd.read_csv(filename, index_col=0)


class ServerChainPredictor(Predictor):
    def __init__(self, dataset=None):
        super().__init__(dataset)
        self.logger = logging.getLogger(f"Server Chain Predictor")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)

    def evaluate(self, max_evals = None):
        '''
        Evaluates
        '''
        if not self.dataset:
            self.logger.error("Cannot evaluate without dataset. Reconstruct ServerChainPredictor instance with dataset.")
            return 
        
        num_correct = 0
        accuracy = 0

        raw_data = {column:[] for column in self.columns}

        #iterate over the rows and create PlayerMC for each person
        for idx, row in self.df.iterrows():

            if max_evals and idx >= max_evals:
                break

            server1 = row.loc['server1']
            server2 = row.loc['server2']

            #simulate a match between server1 and server2
            player_1_mc = self.db.get_player_mc(server1)
            player_2_mc = self.db.get_player_mc(server2)

            #Create a match between the two players
            match = Match(player_1_mc, player_2_mc)
            p, interval = match.sample_match_with_server_chains(confidence_level=.80, max_width=.05, min_trials=30)

            #Make the actual prediction
            prediction = 1 if p > 0.5 else 2

            #update the raw data storage
            raw_data['server1'].append(server1)
            raw_data['server2'].append(server2)
            raw_data['prediction'].append(prediction)
            raw_data['p'].append(p)
            raw_data['true'].append(row['winner'])

            self.logger.debug(f"{(server1, server2, prediction, row['winner'])}, {self.accuracy:.3f}")

            #Check if our prediction was right
            if prediction == row['winner']:
                num_correct += 1
            
            self.accuracy = num_correct / (idx+1)
        
        raw_data_df = pd.DataFrame(raw_data)
        self.raw_data = pd.concat([self.raw_data, raw_data_df])


def t_evaluate_with_server_chains(dataset):
    sc_pred = ServerChainPredictor(dataset)
    sc_pred.evaluate(max_evals=30)
    sc_pred.save('predictions/sc_predictor_80_05_30evals.csv')
    logger.info(f'Accuracy on dataset is {sc_pred.accuracy}')

if __name__ == '__main__':
    logger = logging.getLogger('Evaluator.py')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    
    t_evaluate_with_server_chains('tennis_pointbypoint/pbp_matches_atp_main_current.csv')