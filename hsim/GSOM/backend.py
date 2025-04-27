if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))
import pandas as pd
from io import BytesIO
import hsim.GSOM.GSOMGame

from hsim.GSOM.flask.config import RESULTS_FOLDER
ADD_TO_FILE = True

def scores_server(throughput, excel, folder, player='myself'):
    from datetime import datetime
    new = pd.read_excel(excel, sheet_name='Main', header=None, index_col=0)[1:].transpose().reset_index(drop=True)
    new.insert(0, 'Name', player)
    new.insert(0, 'Time', datetime.now())
    new['Productivity'] = throughput
    new = new[['Name', 'Time', 'Productivity', 'Number of operators', 'Redesign costs']]
    new['Time'] = pd.to_datetime(new['Time']).dt.strftime('%d/%m/%Y %H:%M:%S')
    new['Redesign costs'] = new['Redesign costs'].astype(str) + ' €'
    new['Number of operators'] = new['Number of operators'].astype(int)
    new.to_csv(folder + 'results.csv', index=False, mode='a', header=False)
    
def runner(file, username):
    processed_data: dict = hsim.GSOM.GSOMGame.main(file)
    scores_server(processed_data['TH']["mean"], file, RESULTS_FOLDER, username)
    output = BytesIO()
    
    if ADD_TO_FILE:
        file.seek(0)
        file = BytesIO(file.read())
        file.seek(0)
        output.write(file.read())
        output.seek(0)
        
    with pd.ExcelWriter(output, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        for sheet_name, sheet_df in processed_data.items():
            try:
                sheet_df.to_excel(writer, sheet_name=sheet_name)
            except Exception:
                pass
    output.seek(0)
    return processed_data, output