
from pymulate import Server, Generator, Terminator
from FSM import FSM
from states import State
from transitions import MessageTransition, TimeoutTransition, EventTransition

class UnreliableMachine(Server):
    class FSM(Server.FSM):
        class Failed(State):
            pass
        
        S2W=MessageTransition.define(FSM.Starving, FSM.Working)
        S2F=MessageTransition.define(FSM.Starving, Failed)
        F2B=TimeoutTransition.define(Failed, FSM.Working)
        W2B=TimeoutTransition.define(FSM.Working, FSM.Blocking)
        B2S=EventTransition.define(FSM.Blocking, FSM.Starving)
        
        
def main():
    pass

if __name__ == "__main__":
    main()