    """TEST

    Returns:
        _type_: _description_
    """

import arcade
from typing import Dict

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "2D Simulation Visualization"

class GraphicAgent:
    def __init__(self, x, y, color):
        self._x = x
        self._y = y
        self.color_map: Dict[str, arcade.Color] = {
            "Starving": arcade.color.ORANGE,
            "Working": arcade.color.GREEN,
            "Blocking": arcade.color.BLUE
        }

    @property
    def get_coordinates(self):
        return self._x, self._y

    def get_color(self, state: str):
        return self.color_map[state] if state in self.color_map else arcade.color.WHITE

class VisualizationEngine(arcade.Window):
    def __init__(self, state_provider):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.sprite_list = arcade.SpriteList()
        self.state_provider = state_provider
        self.selected_sprite = None
        self.setup()

    def setup(self):
        # Initialize sprites based on the initial state
        initial_state = self.state_provider.get_initial_state()
        for obj in initial_state:
            sprite = arcade.Sprite(":resources:images/space_shooter/playerShip1_green.png", 0.5)
            sprite.center_x = obj['x']
            sprite.center_y = obj['y']
            self.sprite_list.append(sprite)

    def on_draw(self):
        arcade.start_render()
        self.sprite_list.draw()

    def update(self, delta_time):
        # Update sprite positions or states based on the current state
        current_state = self.state_provider.get_current_state()
        for sprite, obj in zip(self.sprite_list, current_state):
            sprite.center_x = obj['x']
            sprite.center_y = obj['y']
            sprite.color = obj['color']  # Assuming obj has a 'color' attribute

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Create a new sprite at the mouse position
            sprite = arcade.Sprite(":resources:images/space_shooter/playerShip1_green.png", 0.5)
            sprite.center_x = x
            sprite.center_y = y
            self.sprite_list.append(sprite)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            # Select a sprite at the mouse position
            sprites = arcade.get_sprites_at_point((x, y), self.sprite_list)
            if sprites:
                self.selected_sprite = sprites[0]

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.selected_sprite and buttons == arcade.MOUSE_BUTTON_RIGHT:
            # Move the selected sprite
            self.selected_sprite.center_x += dx
            self.selected_sprite.center_y += dy

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.selected_sprite = None

def main(state_provider):
    game = VisualizationEngine(state_provider)
    arcade.run()

if __name__ == "__main__":
    # Example state provider
    class StateProvider:
        def get_initial_state(self):
            return [{'x': 100, 'y': 100, 'color': arcade.color.WHITE},
                    {'x': 200, 'y': 200, 'color': arcade.color.RED}]
        
        def get_current_state(self):
            # This should return the current state of objects
            # For example, it could return updated positions and colors
            return [{'x': 150, 'y': 150, 'color': arcade.color.BLUE},
                    {'x': 250, 'y': 250, 'color': arcade.color.GREEN}]
    
    state_provider = StateProvider()
    main(state_provider)