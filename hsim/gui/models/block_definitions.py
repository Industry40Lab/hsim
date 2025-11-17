"""
Block definitions for all DES components
Metadata for each block type including properties, icons, and generation logic
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class BlockType(Enum):
    """DES Block Types"""
    # Basic DES
    GENERATOR = "generator"
    BUFFER = "buffer"
    SERVER = "server"
    STORE = "store"
    TERMINATOR = "terminator"
    EMPTY_BUFFER = "empty_buffer"

    # Resources
    UNRELIABLE_MACHINE = "unreliable_machine"
    QUALITY_MACHINE = "quality_machine"
    SU_MACHINE = "su_machine"
    MANUAL_STATION = "manual_station"
    OPERATOR = "operator"

    # Advanced
    ASSEMBLY = "assembly"
    SWITCH = "switch"

    # Agents
    AGENT = "agent"


class PropertyType(Enum):
    """Property input types"""
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOL = "bool"
    CHOICE = "choice"
    CODE = "code"


@dataclass
class PropertyDefinition:
    """Definition of a block property"""
    name: str
    label: str
    type: PropertyType
    default: Any
    description: str = ""
    choices: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class BlockDefinition:
    """Complete definition of a DES block type"""
    type: BlockType
    name: str
    category: str
    description: str
    color: str  # Hex color
    shape: str  # 'rectangle', 'circle', 'rounded'
    icon: str  # Emoji or icon name
    properties: List[PropertyDefinition] = field(default_factory=list)
    python_class: str = ""
    python_module: str = ""
    has_fsm: bool = False


# Define all block types
BLOCK_DEFINITIONS = {
    BlockType.GENERATOR: BlockDefinition(
        type=BlockType.GENERATOR,
        name="Generator",
        category="DES Blocks",
        description="Creates entities at specified intervals",
        color="#10B981",  # Green
        shape="circle",
        icon="⚡",
        python_class="Generator",
        python_module="hsim.core.des.pymulate",
        has_fsm=True,  # All agents have FSMs
        properties=[
            PropertyDefinition(
                name="serviceTime",
                label="Interarrival Time",
                type=PropertyType.FLOAT,
                default=1.0,
                description="Mean time between entity arrivals",
                min_value=0.0
            ),
            PropertyDefinition(
                name="serviceTimeFunction",
                label="Distribution",
                type=PropertyType.CHOICE,
                default="exponential",
                description="Probability distribution for interarrival times",
                choices=["exponential", "constant", "normal", "uniform"]
            ),
        ]
    ),

    BlockType.BUFFER: BlockDefinition(
        type=BlockType.BUFFER,
        name="Buffer",
        category="DES Blocks",
        description="Stores entities in a queue",
        color="#3B82F6",  # Blue
        shape="rectangle",
        icon="📦",
        python_class="Buffer",
        python_module="hsim.core.des.pymulate",
        has_fsm=True,  # All agents have FSMs
        properties=[
            PropertyDefinition(
                name="capacity",
                label="Capacity",
                type=PropertyType.STRING,
                default="inf",
                description="Maximum number of entities (or 'inf')",
            ),
            PropertyDefinition(
                name="queueType",
                label="Queue Type",
                type=PropertyType.CHOICE,
                default="standard",
                description="Queueing discipline",
                choices=["standard", "priority", "locked"]
            ),
        ]
    ),

    BlockType.SERVER: BlockDefinition(
        type=BlockType.SERVER,
        name="Server",
        category="DES Blocks",
        description="Processes entities for a service time",
        color="#F59E0B",  # Amber
        shape="rectangle",
        icon="⚙️",
        python_class="Server",
        python_module="hsim.core.des.pymulate",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="serviceTime",
                label="Service Time",
                type=PropertyType.FLOAT,
                default=1.0,
                description="Mean service time per entity",
                min_value=0.0
            ),
            PropertyDefinition(
                name="serviceTimeFunction",
                label="Distribution",
                type=PropertyType.CHOICE,
                default="constant",
                description="Probability distribution for service times",
                choices=["exponential", "constant", "normal", "uniform"]
            ),
        ]
    ),

    BlockType.STORE: BlockDefinition(
        type=BlockType.STORE,
        name="Store",
        category="DES Blocks",
        description="Forwards all entities immediately",
        color="#6366F1",  # Indigo
        shape="rectangle",
        icon="📫",
        python_class="Store",
        python_module="hsim.core.des.pymulate",
        has_fsm=True,  # All agents have FSMs
        properties=[
            PropertyDefinition(
                name="capacity",
                label="Capacity",
                type=PropertyType.STRING,
                default="inf",
                description="Maximum number of entities (or 'inf')",
            ),
        ]
    ),

    BlockType.TERMINATOR: BlockDefinition(
        type=BlockType.TERMINATOR,
        name="Terminator",
        category="DES Blocks",
        description="Destroys entities (exit point)",
        color="#EF4444",  # Red
        shape="circle",
        icon="🛑",
        python_class="Terminator",
        python_module="hsim.core.des.pymulate",
        has_fsm=True,  # All agents have FSMs
        properties=[]
    ),

    BlockType.EMPTY_BUFFER: BlockDefinition(
        type=BlockType.EMPTY_BUFFER,
        name="EmptyBuffer",
        category="DES Blocks",
        description="Buffer that starts empty and refills",
        color="#06B6D4",  # Cyan
        shape="rectangle",
        icon="📭",
        python_class="EmptyBuffer",
        python_module="hsim.core.des.pymulate",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="capacity",
                label="Capacity",
                type=PropertyType.STRING,
                default="inf",
                description="Maximum number of entities (or 'inf')",
            ),
        ]
    ),

    BlockType.UNRELIABLE_MACHINE: BlockDefinition(
        type=BlockType.UNRELIABLE_MACHINE,
        name="Unreliable Machine",
        category="Resources",
        description="Server with random failures (MTTF/MTTR)",
        color="#F97316",  # Orange
        shape="rectangle",
        icon="🔧",
        python_class="UnreliableMachine",
        python_module="hsim.core.des.resources",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="serviceTime",
                label="Service Time",
                type=PropertyType.FLOAT,
                default=1.0,
                description="Mean service time per entity",
                min_value=0.0
            ),
            PropertyDefinition(
                name="serviceTimeFunction",
                label="Distribution",
                type=PropertyType.CHOICE,
                default="constant",
                description="Service time distribution",
                choices=["exponential", "constant", "normal"]
            ),
            PropertyDefinition(
                name="failure_rate",
                label="Failure Rate",
                type=PropertyType.FLOAT,
                default=0.1,
                description="Probability of failure per cycle",
                min_value=0.0,
                max_value=1.0
            ),
            PropertyDefinition(
                name="TTRvalue",
                label="Time to Repair",
                type=PropertyType.FLOAT,
                default=1.0,
                description="Mean time to repair",
                min_value=0.0
            ),
        ]
    ),

    BlockType.QUALITY_MACHINE: BlockDefinition(
        type=BlockType.QUALITY_MACHINE,
        name="Quality Machine",
        category="Resources",
        description="Server with quality inspection and rejection",
        color="#EC4899",  # Pink
        shape="rectangle",
        icon="✓",
        python_class="QualityMachine",
        python_module="hsim.core.des.resources",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="serviceTime",
                label="Service Time",
                type=PropertyType.FLOAT,
                default=1.0,
                description="Mean service time per entity",
                min_value=0.0
            ),
            PropertyDefinition(
                name="serviceTimeFunction",
                label="Distribution",
                type=PropertyType.CHOICE,
                default="constant",
                description="Service time distribution",
                choices=["exponential", "constant", "normal"]
            ),
            PropertyDefinition(
                name="quality_threshold",
                label="Quality Threshold",
                type=PropertyType.FLOAT,
                default=0.9,
                description="Pass threshold (0-1)",
                min_value=0.0,
                max_value=1.0
            ),
        ]
    ),

    BlockType.SU_MACHINE: BlockDefinition(
        type=BlockType.SU_MACHINE,
        name="SUMachine",
        category="Resources",
        description="Machine with setup and operation phases",
        color="#8B5CF6",  # Purple
        shape="rectangle",
        icon="🔄",
        python_class="SUMachine",
        python_module="hsim.core.des.resources",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="setupTime",
                label="Setup Time",
                type=PropertyType.FLOAT,
                default=0.5,
                description="Time required for setup",
                min_value=0.0
            ),
            PropertyDefinition(
                name="operationTime",
                label="Operation Time",
                type=PropertyType.FLOAT,
                default=2.0,
                description="Time for operation phase",
                min_value=0.0
            ),
        ]
    ),

    BlockType.MANUAL_STATION: BlockDefinition(
        type=BlockType.MANUAL_STATION,
        name="ManualStation",
        category="Resources",
        description="Manual workstation requiring operator",
        color="#F97316",  # Orange
        shape="rectangle",
        icon="👷",
        python_class="ManualStation",
        python_module="hsim.core.des.manual",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="serviceTime",
                label="Service Time",
                type=PropertyType.FLOAT,
                default=1.5,
                description="Mean service time",
                min_value=0.0
            ),
            PropertyDefinition(
                name="operatorsRequired",
                label="Operators Required",
                type=PropertyType.INT,
                default=1,
                description="Number of operators needed",
                min_value=1,
                max_value=10
            ),
        ]
    ),

    BlockType.OPERATOR: BlockDefinition(
        type=BlockType.OPERATOR,
        name="Operator",
        category="Resources",
        description="Human operator for manual stations",
        color="#FB923C",  # Light orange
        shape="circle",
        icon="👤",
        python_class="Operator",
        python_module="hsim.core.des.manual",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="skillLevel",
                label="Skill Level",
                type=PropertyType.CHOICE,
                default="medium",
                description="Operator skill level",
                choices=["low", "medium", "high"]
            ),
        ]
    ),

    BlockType.ASSEMBLY: BlockDefinition(
        type=BlockType.ASSEMBLY,
        name="Assembly",
        category="Advanced",
        description="Joins multiple entities into one",
        color="#A855F7",  # Purple (lighter)
        shape="rectangle",
        icon="🔗",
        python_class="Assembly",
        python_module="hsim.core.des.assembly",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="num_inputs",
                label="Number of Inputs",
                type=PropertyType.INT,
                default=2,
                description="Number of input connections required",
                min_value=2,
                max_value=10
            ),
        ]
    ),

    BlockType.SWITCH: BlockDefinition(
        type=BlockType.SWITCH,
        name="Switch",
        category="Advanced",
        description="Routes entities based on conditions",
        color="#06B6D4",  # Cyan
        shape="rectangle",
        icon="🔀",
        python_class="Switch",
        python_module="hsim.core.des.switch",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="num_outputs",
                label="Number of Outputs",
                type=PropertyType.INT,
                default=2,
                description="Number of output paths",
                min_value=2,
                max_value=10
            ),
        ]
    ),

    BlockType.AGENT: BlockDefinition(
        type=BlockType.AGENT,
        name="Custom Agent",
        category="Agents",
        description="Agent with custom FSM behavior",
        color="#14B8A6",  # Teal
        shape="rounded",
        icon="🤖",
        python_class="Agent",
        python_module="hsim.core.agent.agent",
        has_fsm=True,
        properties=[
            PropertyDefinition(
                name="custom_class",
                label="Custom Class Name",
                type=PropertyType.STRING,
                default="CustomAgent",
                description="Python class name for this agent",
            ),
        ]
    ),
}


def get_block_definition(block_type: BlockType) -> BlockDefinition:
    """Get the definition for a block type"""
    return BLOCK_DEFINITIONS.get(block_type)


def get_blocks_by_category() -> Dict[str, List[BlockDefinition]]:
    """Get blocks organized by category"""
    categories = {}
    for block_def in BLOCK_DEFINITIONS.values():
        if block_def.category not in categories:
            categories[block_def.category] = []
        categories[block_def.category].append(block_def)
    return categories
