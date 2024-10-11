import asyncio
import pickle

class AsyncTask:
    def __init__(self, name):
        self.name = name

    async def run(self):
        await asyncio.sleep(1)  # Simulate an asynchronous operation
        return f"Task {self.name} completed"

# Create an instance of AsyncTask
task = AsyncTask("Example")

# Pickle the AsyncTask instance
pickled_task = pickle.dumps(task)

# Unpickle the AsyncTask instance
unpickled_task = pickle.loads(pickled_task)

# Run the unpickled task
async def main():
    result = await task.run()
    pickled_task = pickle.dumps(task)
    print(result)

asyncio.run(main())
