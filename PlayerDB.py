import pandas as pd

from PlayerMC import PlayerMC

import logging
from CustomFormatter import ch

class PlayerDB:
    '''
    Container for all the players and their MC's
    Should be pickled and saved.
    '''

    def __init__(self):
        self.db = dict()

        self.logger = logging.getLogger("PlayerDB")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)
    
    def add_player(self, name) -> bool:
        '''
        Return True if player was successfully added to the db, 
        false otherwise
        '''
        if self._has_player(name):
            self.logger.warn(f"Attempted to add player {name} to db multiple times.")
            return False

        self.db[name] = PlayerMC(name)
    
    def _has_player(self, name) -> bool:
        return (name in self.db)

    def get_player_mc(self, name) -> PlayerMC:
        if self._has_player(name):
            return self.db[name]
        else:
            self.logger.error(f"Cannot find player {name} in db")
    
    def populate_from_csv(self, filepath):
        '''
        Populate the database from a csv file
        '''
        match_stats = pd.read_csv(filepath)
        
        #iterate over the rows and create PlayerMC for each person
        for idx, row in match_stats.iterrows():
            server1 = row.loc['server1']
            server2 = row.loc['server2']

            if not self._has_player(server1):
                self.add_player(server1)
            
            if not self._has_player(server2):
                self.add_player(server2)
            
            pbp = row.loc['pbp']

            #Replace all the delimiters with "change of serve" character
            pbp = pbp.replace(';', ":")
            pbp = pbp.replace('.', ":")
            pbp = pbp.replace('/', ":")

            games = pbp.split(':')

            for serve_idx, w_l in enumerate(games):
                if serve_idx%2 == 0:
                    #server1 is updating
                    self.db[server1].update_from_pbp(w_l, is_server = True)
                    self.db[server2].update_from_pbp(w_l, is_server = False)
                
                else:
                    #server2 is updating
                    self.db[server2].update_from_pbp(w_l, is_server = True)
                    self.db[server1].update_from_pbp(w_l, is_server = False)