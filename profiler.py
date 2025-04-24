import cProfile
import pstats
from hsim.GSOM.GSOMGame import main
import pandas as pd


filename = r"C:\Users\Lorenzo\DIG Dropbox\Lorenzo Ragazzini\Didattica\MIP-GSOM Game\20230323 GSOM MBA 2023 INDUSTRY40 SIMULATION CASE\GSOM_original.xlsx"

profiler = cProfile.Profile()
try:
    profiler.runcall(main, filename=filename, app=True)
except Exception as e:
    print(f"Error: {e}")
# Save profiler stats to an Excel file using pandas

stats = pstats.Stats(profiler)
stats.sort_stats("cumtime")
data = [
    {
        "Function": f"{func[0]}:{func[1]}({func[2]})",
        "Calls": cc,
        "Total Time": tt,
        "Cumulative Time": ct,
        "Per Call (Total)": tt / nc if nc else 0,
        "Per Call (Cumulative)": ct / nc if nc else 0,
    }
    for func, (cc, nc, tt, ct, callers) in stats.stats.items()
]
df = pd.DataFrame(data).to_excel("profiler_stats.xlsx", index=False)


