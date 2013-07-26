# This is an example to demonstrate how the output of abstracting a switched
# system, where the mode of the system depends on a combination of environment
# and system controlled modes. We assume within each mode there is some rich
# control authority that can be used to establish deterministic reachability 
# relations through the use of low-level control.
# We will assume, we have the 6 cell robot example.

#
#     +---+---+---+
#     | 3 | 4 | 5 |
#     +---+---+---+
#     | 0 | 1 | 2 |
#     +---+---+---+
#

from tulip import *
from tulip import spec
import numpy as np
from scipy import sparse as sp


###########################################
# Hybrid system with 2 env, 2 system modes:
###########################################

sys_hyb = transys.oFTS()

# We assume robots ability to transition between cells depends both on
# discrete controlled modes (e.g., gears) and environment modes (e.g., surface
# conditions).

sys_hyb.sys_actions.add_from({'gear0','gear1'})
sys_hyb.env_actions.add_from({'slippery','normal'})

# first environment chooses a mode, than the system chooses a mode and within
# each mode there exists a low level controller to take any available transition
# deterministically

# gear0 basically stops the robot no matter what the enviornment does so
# we take the transitions to be identity
trans1 = np.eye(6)

sys_hyb.transitions.add_labeled_adj(sp.lil_matrix(trans1),('gear0','normal'))
sys_hyb.transitions.add_labeled_adj(sp.lil_matrix(trans1),('gear0','slippery'))

# gear1 dynamics are similar to the environment switching example
transmat1 = np.array([[1,1,0,1,0,0],
                     [1,1,1,0,1,0],
                     [0,1,1,0,1,1],
                     [1,0,0,1,1,0],
                     [0,1,0,1,1,1],
                     [0,0,1,0,1,1]])

sys_hyb.transitions.add_labeled_adj(sp.lil_matrix(transmat1),('gear1','normal'))

transmat2 = np.array([[0,0,1,1,0,0],
                     [1,0,1,0,1,0],
                     [1,0,0,0,1,1],
                     [1,0,0,0,0,1],
                     [0,1,0,1,0,1],
                     [0,0,1,1,0,0]])

sys_hyb.transitions.add_labeled_adj(sp.lil_matrix(transmat2),('gear1','slippery'))

# Decorate TS with state labels (aka atomic propositions)
sys_hyb.atomic_propositions.add_from(['home','lot'])
sys_hyb.atomic_propositions.label_per_state(range(6),[{'home'},set(),set(),set(),set(),{'lot'}])

# This is what is visible to the outside world (and will go into synthesis method)
print sys_hyb

#
# Environment variables and specification
#
# The environment can issue a park signal that the robot just respond
# to by moving to the lower left corner of the grid.  We assume that
# the park signal is turned off infinitely often.
#
env_vars = {'park'}
env_init = set()                # empty set
env_prog = '[]<>(!park)'
env_safe = set()                # empty set

# 
# System specification
#
# The system specification is that the robot should repeatedly revisit
# the upper right corner of the grid while at the same time responding
# to the park signal by visiting the lower left corner.  The LTL
# specification is given by 
#
#     []<> home && [](park -> <>lot)
#
# Since this specification is not in GR(1) form, we introduce the
# variable X0reach that is initialized to True and the specification
# [](park -> <>lot) becomes
#
#     [](next(X0reach) == X0 || (X0reach && !park))
#

# Augment the environmental description to make it GR(1)
#! TODO: create a function to convert this type of spec automatically
env_vars |= {'X0reach'}
env_init |= {'X0reach'}

# Define the specification
#! NOTE: maybe "synthesize" should infer the atomic proposition from the 
# transition system?
sys_vars = set()                # part of TS
sys_init = set()                # empty set
sys_prog = 'home'               # []<>X5
sys_safe = {'next(X0reach) == lot || (X0reach && !park)'}

# Possible additional specs
# It is unsafe to "break" (switch to gear0) when road is slippery
# sys_safe |= {'gear1 && slippery -> next(gear1)'}

# Create the specification
specs = spec.GRSpec(env_vars, sys_vars, env_init, sys_init,
                    env_safe, sys_safe, env_prog, sys_prog)
                    
# Controller synthesis
#
# At this point we can synthesize the controller using one of the available
# methods.  Here we make use of JTLV.
#
ctrl = synthesize('jtlv', specs, sys_hyb)
