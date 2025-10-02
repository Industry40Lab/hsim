"""
Core data model for simulation
Represents the complete simulation model with blocks, connections, and FSMs
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import uuid


@dataclass
class Position:
    """2D position for visual elements"""
    x: float
    y: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Size:
    """Size for visual elements"""
    width: float
    height: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.width, self.height)


@dataclass
class Block:
    """A DES block instance in the model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    name: str = "Block"
    position: Position = field(default_factory=lambda: Position(0, 0))
    size: Size = field(default_factory=lambda: Size(100, 80))
    properties: Dict[str, Any] = field(default_factory=dict)
    fsm_id: Optional[str] = None  # Reference to FSM if this block has one

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'position': {'x': self.position.x, 'y': self.position.y},
            'size': {'width': self.size.width, 'height': self.size.height},
            'properties': self.properties,
            'fsm_id': self.fsm_id
        }

    @staticmethod
    def from_dict(data: dict) -> 'Block':
        """Deserialize from dictionary"""
        return Block(
            id=data['id'],
            type=data['type'],
            name=data['name'],
            position=Position(data['position']['x'], data['position']['y']),
            size=Size(data['size']['width'], data['size']['height']),
            properties=data.get('properties', {}),
            fsm_id=data.get('fsm_id')
        )


@dataclass
class Connection:
    """Connection between two blocks"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_block: str = ""  # Block ID
    to_block: str = ""    # Block ID
    label: str = ""
    control_points: List[Position] = field(default_factory=list)  # For curved connections

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'from': self.from_block,
            'to': self.to_block,
            'label': self.label,
            'control_points': [{'x': p.x, 'y': p.y} for p in self.control_points]
        }

    @staticmethod
    def from_dict(data: dict) -> 'Connection':
        """Deserialize from dictionary"""
        return Connection(
            id=data['id'],
            from_block=data['from'],
            to_block=data['to'],
            label=data.get('label', ''),
            control_points=[Position(p['x'], p['y']) for p in data.get('control_points', [])]
        )


@dataclass
class State:
    """FSM State"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "State"
    position: Position = field(default_factory=lambda: Position(0, 0))
    size: Size = field(default_factory=lambda: Size(120, 60))
    is_initial: bool = False
    is_final: bool = False
    parent_state_id: Optional[str] = None  # For hierarchical states
    on_enter: str = ""  # Python code
    on_exit: str = ""   # Python code
    color: str = "#3B82F6"  # Blue default

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'position': {'x': self.position.x, 'y': self.position.y},
            'size': {'width': self.size.width, 'height': self.size.height},
            'is_initial': self.is_initial,
            'is_final': self.is_final,
            'parent_state_id': self.parent_state_id,
            'on_enter': self.on_enter,
            'on_exit': self.on_exit,
            'color': self.color
        }

    @staticmethod
    def from_dict(data: dict) -> 'State':
        """Deserialize from dictionary"""
        return State(
            id=data['id'],
            name=data['name'],
            position=Position(data['position']['x'], data['position']['y']),
            size=Size(data['size']['width'], data['size']['height']),
            is_initial=data.get('is_initial', False),
            is_final=data.get('is_final', False),
            parent_state_id=data.get('parent_state_id'),
            on_enter=data.get('on_enter', ''),
            on_exit=data.get('on_exit', ''),
            color=data.get('color', '#3B82F6')
        )


@dataclass
class Transition:
    """FSM Transition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_state: str = ""  # State ID
    to_state: str = ""    # State ID
    label: str = ""
    transition_type: str = "message"  # message, timeout, condition, event
    timeout: Optional[float] = None
    condition: str = ""  # Python expression
    on_transition: str = ""  # Python code
    control_points: List[Position] = field(default_factory=list)  # For curved transitions

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'from': self.from_state,
            'to': self.to_state,
            'label': self.label,
            'type': self.transition_type,
            'timeout': self.timeout,
            'condition': self.condition,
            'on_transition': self.on_transition,
            'control_points': [{'x': p.x, 'y': p.y} for p in self.control_points]
        }

    @staticmethod
    def from_dict(data: dict) -> 'Transition':
        """Deserialize from dictionary"""
        return Transition(
            id=data['id'],
            from_state=data['from'],
            to_state=data['to'],
            label=data.get('label', ''),
            transition_type=data.get('type', 'message'),
            timeout=data.get('timeout'),
            condition=data.get('condition', ''),
            on_transition=data.get('on_transition', ''),
            control_points=[Position(p['x'], p['y']) for p in data.get('control_points', [])]
        )


@dataclass
class FSM:
    """Finite State Machine"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "FSM"
    owner_block_id: Optional[str] = None  # Block that owns this FSM
    states: Dict[str, State] = field(default_factory=dict)
    transitions: List[Transition] = field(default_factory=list)

    def add_state(self, state: State):
        """Add a state to the FSM"""
        self.states[state.id] = state

    def remove_state(self, state_id: str):
        """Remove a state and its transitions"""
        if state_id in self.states:
            del self.states[state_id]
            # Remove transitions involving this state
            self.transitions = [t for t in self.transitions
                              if t.from_state != state_id and t.to_state != state_id]

    def add_transition(self, transition: Transition):
        """Add a transition"""
        self.transitions.append(transition)

    def remove_transition(self, transition_id: str):
        """Remove a transition"""
        self.transitions = [t for t in self.transitions if t.id != transition_id]

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'owner_block_id': self.owner_block_id,
            'states': {sid: state.to_dict() for sid, state in self.states.items()},
            'transitions': [t.to_dict() for t in self.transitions]
        }

    @staticmethod
    def from_dict(data: dict) -> 'FSM':
        """Deserialize from dictionary"""
        fsm = FSM(
            id=data['id'],
            name=data['name'],
            owner_block_id=data.get('owner_block_id')
        )
        fsm.states = {sid: State.from_dict(sdata)
                     for sid, sdata in data.get('states', {}).items()}
        fsm.transitions = [Transition.from_dict(tdata)
                          for tdata in data.get('transitions', [])]
        return fsm


@dataclass
class SimulationModel:
    """Complete simulation model"""
    name: str = "New Model"
    version: str = "1.0"
    blocks: Dict[str, Block] = field(default_factory=dict)
    connections: List[Connection] = field(default_factory=list)
    fsms: Dict[str, FSM] = field(default_factory=dict)

    def add_block(self, block: Block):
        """Add a block to the model"""
        self.blocks[block.id] = block

    def remove_block(self, block_id: str):
        """Remove a block and its connections"""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            del self.blocks[block_id]

            # Remove connections
            self.connections = [c for c in self.connections
                              if c.from_block != block_id and c.to_block != block_id]

            # Remove associated FSM
            if block.fsm_id and block.fsm_id in self.fsms:
                del self.fsms[block.fsm_id]

    def add_connection(self, connection: Connection):
        """Add a connection"""
        self.connections.append(connection)

    def remove_connection(self, connection_id: str):
        """Remove a connection"""
        self.connections = [c for c in self.connections if c.id != connection_id]

    def add_fsm(self, fsm: FSM):
        """Add an FSM"""
        self.fsms[fsm.id] = fsm

    def get_block_by_id(self, block_id: str) -> Optional[Block]:
        """Get block by ID"""
        return self.blocks.get(block_id)

    def get_connections_from(self, block_id: str) -> List[Connection]:
        """Get all connections from a block"""
        return [c for c in self.connections if c.from_block == block_id]

    def get_connections_to(self, block_id: str) -> List[Connection]:
        """Get all connections to a block"""
        return [c for c in self.connections if c.to_block == block_id]

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'blocks': {bid: block.to_dict() for bid, block in self.blocks.items()},
            'connections': [c.to_dict() for c in self.connections],
            'fsms': {fid: fsm.to_dict() for fid, fsm in self.fsms.items()}
        }

    @staticmethod
    def from_dict(data: dict) -> 'SimulationModel':
        """Deserialize from dictionary"""
        model = SimulationModel(
            name=data.get('name', 'New Model'),
            version=data.get('version', '1.0')
        )
        model.blocks = {bid: Block.from_dict(bdata)
                       for bid, bdata in data.get('blocks', {}).items()}
        model.connections = [Connection.from_dict(cdata)
                           for cdata in data.get('connections', [])]
        model.fsms = {fid: FSM.from_dict(fdata)
                     for fid, fdata in data.get('fsms', {}).items()}
        return model
