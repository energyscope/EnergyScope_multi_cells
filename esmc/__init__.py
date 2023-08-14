
import logging.config
import logging
import os

from .common import commons

# Remove old log file:
for filename in (f for f in os.listdir('.') if f.endswith('.energyscope.log')):
    try:
        os.remove(filename)
    except OSError:
        print('Could not erase previous log file ' + filename)

# Logging: #
_LOGCONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)-8s] (%(funcName)s): %(message)s',
            'datefmt': '%y/%m/%d %H:%M:%S'
        },
        'notime': {
            'format': '[%(levelname)-8s] (%(funcName)s): %(message)s',
            'datefmt': '%y/%m/%d %H:%M:%S'
        },
    },
    "handlers": {
        "console": {
            "class": "energyscope.misc.colorstreamhandler.ColorStreamHandler",
            "stream": "ext://sys.stderr",
            # "stream": "sys.stdout",
            "level": "INFO",
            'formatter': 'notime',
        },

        "error_file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            'formatter': 'standard',
            'filename': commons['logfile'],
            'encoding': 'utf8'

        }
    },

    "root": {
        "level": "INFO",
        "handlers": ["console", "error_file"],
    }
}

# Setting logging configuration:
try:
    logging.config.dictConfig(_LOGCONFIG)
except Exception:
    # if it didn't work, it might be due to ipython messing with the output
    # typical error: Unable to configure handler 'console': IOStream has no fileno
    # try without console output:
    logging.warning('The colored console output is failing (possibly because of ipython). '
                    'Switching to monochromatic output')
    _LOGCONFIG['handlers']['console']['class'] = "logging.StreamHandler"
    logging.config.dictConfig(_LOGCONFIG)


from .preprocessing.preprocessing import step1_in, step2_in, set_ampl, run_ampl, run_esmc, update_version
from .preprocessing.dat_print import *
from esmc.utils.region import Region
from esmc.utils.opti_probl import OptiProbl
from esmc.utils.esmc import Esmc
from esmc.utils.df_utils import *
from .postprocessing.amplpy2pd import print_json, read_json
from .postprocessing.postprocessing import get_used, get_var_cases, subgroup, subgroup_on_max, compute_convergence
from .postprocessing.td_analysis import *
from .postprocessing.draw_sankey.ESSankey import drawSankey
from .postprocessing.draw_sankey.output_to_sankey_csv import write_sankey_file
#from .postprocessing.geoplots import *

