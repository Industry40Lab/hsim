# Auto-generated simulation code from hsim Model Designer
# Model: Manufacturing Line Demo
# Version: 1.0

from hsim.core.core.env import Environment
from hsim.core.des.pymulate import Buffer
from hsim.core.des.pymulate import Generator
from hsim.core.des.pymulate import Server
from hsim.core.des.pymulate import Terminator
from hsim.core.des.resources import QualityMachine
import numpy as np

def main():
    # Create environment
    env = Environment()

    # Create blocks
    raw_material_arrivals = Generator(env, 'Raw Material Arrivals', serviceTime=5.0, serviceTimeFunction=np.random.exponential)
    input_queue = Buffer(env, 'Input Queue', capacity='10', queueType='standard')
    processing_machine = Server(env, 'Processing Machine', serviceTime=8.0, serviceTimeFunction=np.random.normal)
    quality_inspection = QualityMachine(env, 'Quality Inspection', serviceTime=2.0, serviceTimeFunction=None, quality_threshold=0.95)
    output_queue = Buffer(env, 'Output Queue', capacity=np.inf, queueType='standard')
    finished_goods = Terminator(env, 'Finished Goods')

    # Create connections
    raw_material_arrivals.connections['next'] = input_queue
    input_queue.connections['next'] = processing_machine
    processing_machine.connections['next'] = quality_inspection
    quality_inspection.connections['next'] = output_queue
    output_queue.connections['next'] = finished_goods

    # Activate FSMs
    processing_machine.activate_fsm()
    quality_inspection.activate_fsm()

    # Run simulation
    env.run(100)  # Adjust simulation time as needed


if __name__ == '__main__':
    main()