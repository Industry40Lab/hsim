if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))
import pandas as pd
from io import BytesIO
import GSOMGame

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
    processed_data: dict = GSOMGame.main(file)
    scores_server(processed_data['TH']["mean"], file, "", username)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, sheet_df in processed_data.items():
            try:
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
            except:
                pass
    output.seek(0)
    return processed_data, output