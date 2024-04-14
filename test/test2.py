
from hsim.core.chfsm import CHFSM, CompositeState, State, Transition
from hsim.core.core import Environment

if __name__ == "__main__" and 1:
    '''
    class Boh(StateMachine):
        def build(self):
            Idle = State('Idle',True)
            @do(Idle)
            def printt(self):
                print('%s is Idle' %self.sm._name)
                return self.env.timeout(10)
            @do(Idle)
            def todo(self,Event):
                print('%s waited 10s' %self.sm._name)
            @on_exit(Idle)
            def print_ciao(self):
                print('Idle state exit')
            @on_interrupt(Idle)
            def interrupted_ok(self):
                print('%s idle state interrupted ok'  %self.sm._name)
            class Idle_SM(CompositeState):
                Sub = State('Sub',True)
                @do(Sub)
                def printt(self):
                    print('%s will print this something in 20 s'  %self.sm._name)
                    return self.env.timeout(20)
                @do(Sub)
                def todo(self,Event):
                    print('Printing this only once')
                    raise
                @on_exit(Sub)
                def print_ciao(self):
                    print('Substate exit')
            Idle.set_composite_state(Idle_SM)
            return [Idle]
    
    class Boh2(CHFSM):
        def build(self):
            Work = State('Work',True)
            @do(Work)
            def printt(self):
                print('Start working. Will finish in 10s')
                return self.env.timeout(10)
            @do(Work)
            def d(self,Event):
                print("Finished!")
                return Work
            @on_exit(Work)
            def exiting(self):
                print('Leaving working state')
            @on_entry(Work)
            def entering(self):
                print('Entering working state')
            return [Work]
        
    class Boh3(CHFSM):
        pass
    Work = State('Work',True)
    @do(Work)
    def printt(self):
        print('Start working. Will finish in 10s')
        return self.env.timeout(10)
    @do(Work)
    def d(self,Event):
        print("Finished!")
        return self.Work
    add_states(Boh3,[Work])
    
    class Boh4(CHFSM):
        pass
    Work = State('Work',True)
    Work._do = lambda self:print('Start working. Will finish in 10s')
    t = Transition(Work, None, lambda self: self.env.timeout(10))
    Work._transitions = [t]
    add_states(Boh4,[Work])
    
    '''
    class Boh5(CHFSM):
        class Work(State):
            initial_state=True
            _do = lambda self: print('Start working at %d. Will finish in 10s' %env.now)
            class WorkSM(CompositeState):
                class Work0(State):
                    initial_state=True
                    _do = lambda self:print('Inner SM start working at %d. Will finish in 5s' %env.now)
                T1=Transition(Work0, None, lambda self: self.env.timeout(5))
        T1=Transition(Work, None, lambda self: self.env.timeout(10))
    
    class Boh6(CHFSM):
        class Work(State):
            initial_state=True
            _do = lambda self: print('Start working at %d. Will finish in 10s' %self.env.now)
        class Rest(State):
            _do = lambda self: print('Start resting at %d. Will finish in 10s' %self.env.now)
        T1=Transition(Work, Rest, lambda self: self.env.timeout(10))
        T2=Transition(Rest, Work, lambda self: self.env.timeout(10))
    
    class Boh7(CHFSM):
        class Work(State):
            initial_state=True
            _do = lambda self: print('Start working at %d. Will finish in 10s' %self.env.now)
        class Rest(State):
            _do = lambda self: print('Start resting at %d. Will finish in 10s' %self.env.now)
        T1=Transition(Work, Rest, lambda self: self.E,action=print(100))
        T1a=Transition(Work, Rest, lambda self: self.E,action=print(100))
        T2=Transition(Rest, Work, lambda self: self.env.timeout(10))
    
    # class Boh7(CHFSM):
    #     class Work(State):
    #         initial_state=True
    #         _do = lambda self: print('Start working at %d. ' %self.env.now)
    #     class Rest(State):
    #         _do = lambda self: print('Start resting at %d. ' %self.env.now)
    #     T1=Transition(Work, Rest, lambda self: self.E,action=print('I will rest'))
    #     T1a=Transition(Rest, Work, lambda self: self.E,action=print('I will work'))

    
    
    
    
    # env = Environment()
    # foo = Boh6(env,1)
    # env.run(50)
    # foo.interrupt()
    # env.run(200)

    env = Environment()
    foo2 = Boh7(env,1)
    foo2.E = env.event()
    env.run(50)
    print('go')
    foo2.E.succeed()
    env.run(10)
    


