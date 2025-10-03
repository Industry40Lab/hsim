# Bug Fix: Properties Panel AttributeError

## Problem
When selecting any block, the properties panel crashed with:
```
AttributeError: 'SimulationModel' object has no attribute 'get_fsm_by_id'
```

## Root Causes

### 1. Missing `get_fsm_by_id()` method
The `SimulationModel` class had an `fsms` dictionary and `add_fsm()` method, but no getter method.

### 2. Inconsistent `connections` data structure
The model used `List[Connection]` but code elsewhere expected `Dict[str, Connection]`.

## Solutions

### File: `hsim/gui/models/model.py`

#### 1. Added `get_fsm_by_id()` method (line 286-288):
```python
def get_fsm_by_id(self, fsm_id: str) -> Optional[FSM]:
    """Get FSM by ID"""
    return self.fsms.get(fsm_id)
```

#### 2. Changed connections from List to Dict (line 249):
```python
# BEFORE:
connections: List[Connection] = field(default_factory=list)

# AFTER:
connections: Dict[str, Connection] = field(default_factory=dict)
```

#### 3. Updated all connection methods:

**add_connection()** - Changed from append to dict assignment:
```python
# BEFORE:
def add_connection(self, connection: Connection):
    self.connections.append(connection)

# AFTER:
def add_connection(self, connection: Connection):
    self.connections[connection.id] = connection
```

**remove_connection()** - Changed from list comprehension to dict deletion:
```python
# BEFORE:
def remove_connection(self, connection_id: str):
    self.connections = [c for c in self.connections if c.id != connection_id]

# AFTER:
def remove_connection(self, connection_id: str):
    if connection_id in self.connections:
        del self.connections[connection_id]
```

**remove_block()** - Updated to iterate over dict:
```python
# Remove connections
to_remove = [cid for cid, c in self.connections.items()
            if c.from_block == block_id or c.to_block == block_id]
for cid in to_remove:
    del self.connections[cid]
```

**get_connections_from() / get_connections_to()** - Added `.values()`:
```python
# BEFORE:
return [c for c in self.connections if c.from_block == block_id]

# AFTER:
return [c for c in self.connections.values() if c.from_block == block_id]
```

#### 4. Updated serialization methods:

**to_dict()** - Serialize connections as dict:
```python
'connections': {cid: c.to_dict() for cid, c in self.connections.items()}
```

**from_dict()** - Handle backward compatibility:
```python
# Handle both old list format and new dict format
connections_data = data.get('connections', {})
if isinstance(connections_data, list):
    # Old format - convert to dict
    model.connections = {c['id']: Connection.from_dict(c) for c in connections_data}
else:
    # New dict format
    model.connections = {cid: Connection.from_dict(cdata)
                       for cid, cdata in connections_data.items()}
```

## Benefits

1. ✅ **Properties panel works correctly** - Can display FSM info for selected blocks
2. ✅ **Consistent data structures** - All entity collections now use Dict (blocks, connections, fsms)
3. ✅ **Better performance** - O(1) lookup for connections by ID instead of O(n) search
4. ✅ **Backward compatibility** - Old saved files with list-based connections still load correctly
5. ✅ **Clean API** - Consistent getter methods: `get_block_by_id()`, `get_fsm_by_id()`, `get_connection_by_id()` (future)

## Testing
- [x] Select Generator → Properties panel shows parameters
- [x] Select Server → Properties panel shows FSM info
- [x] Edit Statechart button works
- [x] Connections displayed in properties
- [x] No AttributeError on any block selection
