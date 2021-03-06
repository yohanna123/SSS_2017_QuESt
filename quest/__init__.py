"""
The primary init for the project.
"""

from . import molecule
from . import scf_module
from . import mp2_module
from . import jk
from . import solvers
#from . import core
from . import lj
from . import driver
from . import mc_module

from .mollib import mollib
from .molecule import Molecule
from .wavefunction import Wavefunction
from .mc_module import rdf_func

# Make sure Psi4 respects the global OMP_NUM_THREADS
import psi4
import os
if "OMP_NUM_THREADS" in list(os.environ):
    psi4.set_num_threads(int(os.environ["OMP_NUM_THREADS"]))
psi4.set_output_file("psi_output.out")

# Import default params
default_params = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'default_params.yml')
lj_sample_config = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lj_sample_config_periodic1.txt')
