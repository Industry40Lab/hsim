"""
Undo/Redo system for model editing
"""

from typing import List, Callable, Any


class Command:
    """Base class for undoable commands"""
    
    def __init__(self, description: str):
        self.description = description
    
    def execute(self):
        """Execute the command"""
        raise NotImplementedError
    
    def undo(self):
        """Undo the command"""
        raise NotImplementedError


class CreateBlockCommand(Command):
    """Command for creating a block"""
    
    def __init__(self, model, block, canvas):
        super().__init__(f"Create {block.name}")
        self.model = model
        self.block = block
        self.block_id = block.id
        self.canvas = canvas
    
    def execute(self):
        """Add block to model and canvas"""
        if self.block_id not in self.model.blocks:
            self.model.blocks[self.block_id] = self.block
            self.canvas.add_block_to_canvas(self.block)
    
    def undo(self):
        """Remove block from model and canvas"""
        if self.block_id in self.model.blocks:
            del self.model.blocks[self.block_id]
            self.canvas.remove_block_from_canvas(self.block_id)


class DeleteBlockCommand(Command):
    """Command for deleting a block"""
    
    def __init__(self, model, block, canvas, connections):
        super().__init__(f"Delete {block.name}")
        self.model = model
        self.block = block
        self.block_id = block.id
        self.canvas = canvas
        self.connections = connections  # Store connections to restore
    
    def execute(self):
        """Remove block from model and canvas"""
        if self.block_id in self.model.blocks:
            del self.model.blocks[self.block_id]
            self.canvas.remove_block_from_canvas(self.block_id)
    
    def undo(self):
        """Restore block to model and canvas"""
        if self.block_id not in self.model.blocks:
            self.model.blocks[self.block_id] = self.block
            self.canvas.add_block_to_canvas(self.block)
            # Restore connections
            for conn in self.connections:
                self.model.connections[conn.id] = conn
                self.canvas.add_connection_to_canvas(conn)


class MoveBlockCommand(Command):
    """Command for moving a block"""
    
    def __init__(self, block_id, old_pos, new_pos, canvas):
        super().__init__(f"Move block")
        self.block_id = block_id
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.canvas = canvas
    
    def execute(self):
        """Move block to new position"""
        self.canvas.move_block(self.block_id, self.new_pos)
    
    def undo(self):
        """Move block back to old position"""
        self.canvas.move_block(self.block_id, self.old_pos)


class CreateConnectionCommand(Command):
    """Command for creating a connection"""
    
    def __init__(self, model, connection, canvas):
        super().__init__("Create connection")
        self.model = model
        self.connection = connection
        self.conn_id = connection.id
        self.canvas = canvas
    
    def execute(self):
        """Add connection to model and canvas"""
        if self.conn_id not in self.model.connections:
            self.model.connections[self.conn_id] = self.connection
            self.canvas.add_connection_to_canvas(self.connection)
    
    def undo(self):
        """Remove connection from model and canvas"""
        if self.conn_id in self.model.connections:
            del self.model.connections[self.conn_id]
            self.canvas.remove_connection_from_canvas(self.conn_id)


class UndoStack:
    """Manages undo/redo operations"""
    
    def __init__(self, limit: int = 100):
        self.limit = limit
        self.commands: List[Command] = []
        self.current_index = -1
    
    def push(self, command: Command):
        """Push a new command onto the stack"""
        # Remove any commands after current index (they were undone)
        self.commands = self.commands[:self.current_index + 1]
        
        # Add new command
        self.commands.append(command)
        
        # Limit stack size
        if len(self.commands) > self.limit:
            self.commands.pop(0)
        else:
            self.current_index += 1
    
    def undo(self):
        """Undo the last command"""
        if self.can_undo():
            command = self.commands[self.current_index]
            command.undo()
            self.current_index -= 1
            return command.description
        return None
    
    def redo(self):
        """Redo the next command"""
        if self.can_redo():
            self.current_index += 1
            command = self.commands[self.current_index]
            command.execute()
            return command.description
        return None
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_index < len(self.commands) - 1
    
    def clear(self):
        """Clear the undo stack"""
        self.commands = []
        self.current_index = -1
    
    def get_undo_text(self) -> str:
        """Get description of command that would be undone"""
        if self.can_undo():
            return self.commands[self.current_index].description
        return ""
    
    def get_redo_text(self) -> str:
        """Get description of command that would be redone"""
        if self.can_redo():
            return self.commands[self.current_index + 1].description
        return ""
