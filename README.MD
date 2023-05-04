
The model proposed in this thesis is a hierarchical system of leading and following
agents coordinated by a central planning algorithm. It is based on an extended floor field
model. The main contribution of this work lies in analyzing novel strategies and rules for
the leading agent, such as it’s position within the crowd. The crowd structure is modeled
by introducing a pair formation of children moving in queues and examining the leader’s 
influence over the following agents.


# Instructions
The model was developed in Python 3.10.
The maps are available in `src\maps\` folder and the main file `setup.py` needs to be 
run in the same folder as `maps`.

1. Install required libraries from  `src/requirements.txt`.

2. Run `setup.py` in the `src\` folder.
   1. In the `main` function can be uncommented either batch runs (for experiments)
   or visualizations for running the simulation in web browser. You can adjust 
   the global parameters in the `setup.py` or you can use the sliders in visualization.