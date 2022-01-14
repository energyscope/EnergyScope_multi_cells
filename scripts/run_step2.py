from esmc import Esmc
from pathlib import Path

config = {'case_study': 'test7',
          'comment': 'this a test of json version printing',
          'regions_names': ['ES-PT', 'FR', 'IE-UK']}

my_model = Esmc(config, Nbr_TD=10)

my_model.set_esom()

#my_model.esom.read_outputs()
my_model.solve_esom()
my_model.prints_esom()