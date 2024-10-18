import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))



if __name__ == "__main__":
    from hsim.tests.new import test1, test2, test3       
    test1(), test2(), test3()
    from hsim.core.des.pymulate import test1, test2, test3
    test1(), test2(), test3()
    from hsim.core.des.switch import test1
    test1()
    from hsim.core.des.manual import test4
    test4()