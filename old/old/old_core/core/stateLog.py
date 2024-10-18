from pandas import DataFrame


class StateLog(DataFrame):
    def __init__(self):
        columns=['Resource','State','timeIn','timeOut']
        super().__init__(columns=columns)
    def add(self,data):
        pass
    def read(self):
        x = self.copy()     
        for i in range(len(self.env.state_log)):
            x.loc[i].Resource