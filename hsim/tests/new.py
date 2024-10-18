import logging

from hsim.core.core.env import Environment
from hsim.core.core.msg import Message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from FSM import FSM
from states import State
from transitions import MessageTransition, TimeoutTransition


import pickle
import dill

def test1():
    env = Environment()
    fsm = FSM(env)
    fsm._states = [State("Idle", fsm, initial_state=True), State("Active", fsm)]
    fsm._transitions = [TimeoutTransition(fsm, fsm._states[0], fsm._states[1],15), MessageTransition(fsm, fsm._states[1], fsm._states[0], message=None)]
    fsm.start()
    
    env.run(10)
    env=pickle.loads(pickle.dumps(env))
    env.run(20)
    
    
def test2():
    env = Environment()
    fsm = FSM(env)
    fsm._states = [State("Idle", fsm, initial_state=True), State("Active", fsm)]
    fsm._transitions = [TimeoutTransition(fsm, fsm._states[0], fsm._states[1],15), MessageTransition(fsm, fsm._states[1], fsm._states[0], message=None)]
    fsm.start()
    
    env.run(20)
    Message(env,"Test",fsm)
    env.run(30)

def test3():
    env = Environment()
    
    class T(FSM):
        class Idle(State):
            initial_state=True
        class Active(State):
            initial_state=False
        T1 = TimeoutTransition.define(Idle, Active)
        T1.timeout = 15
        T2 = MessageTransition.define(Active, Idle)

        
    fsm = T(env)
    fsm.start()
    
    env.run(20)
    Message(env,"Test",fsm)
    env.run(30)
    print(env.scheduler._queue)

if __name__ == "__main__":
    test1()
    test2()
    test3()

