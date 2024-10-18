import pandas as pd


def createLog():
    # global log
    log = pd.DataFrame(columns = ["entity","resource","operator","activity","timeIn","timeOut"])  
    return log
