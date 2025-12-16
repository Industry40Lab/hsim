import cProfile
import pstats
from hsim.GSOM.GSOMGame import main
import pandas as pd


filename = r"data/profiler/GSOM_original.xlsx"

if 1:
    from time import time
    t = time()
    main(filename=filename, app=True)
    print(f"Execution time without profiling: {time()-t} seconds")
    raise SystemExit()

profiler = cProfile.Profile()
try:
    profiler.runcall(main, filename=filename, app=True)
except Exception as e:
    print(f"Error: {e}")
profiler.dump_stats("data/profiler/output.prof")

stats = pstats.Stats(profiler)
stats.sort_stats("cumtime")
data = [
    {
        "Function": f"{func[0]}:{func[1]}({func[2]})",
        "Calls": cc,
        "Total Time": tt,
        "Cumulative Time": ct,
        "Per Call (Total)": tt / nc if nc else 0,
        "Per Call (Cumulative)": ct / nc if nc else 0
    }
    for func, (cc, nc, tt, ct, callers) in stats.stats.items()
]
df = pd.DataFrame(data).to_excel("data/profiler/profiler_stats.xlsx", index=False)


