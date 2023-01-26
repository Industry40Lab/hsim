# -*- coding: utf-8 -*-

import platform
from tkinter import Tk, Canvas
from PIL import Image, ImageTk
from abc import abstractmethod


class ScaledCanvas:
    """overview of canvas methods called from visualizer"""

    def __init__(self, scale: float) -> None:
        self.scale = scale

    @abstractmethod
    def load_image_file(self, path: str):
        """takes file path and returns loaded image file reference"""

    @abstractmethod
    def create_image(self, x_coord: int, y_coord: int, image_file, anchor="c") -> int:
        """places image on canvas and returns image reference"""

    @abstractmethod
    def create_text(
        self,
        x_coord: int,
        y_coord: int,
        text: str = "",
        anchor: str = "se",
        fill: str = "black",
        font: str = "Helvetica 16",
    ) -> int:
        """places text on canvas and returns reference"""

    @abstractmethod
    def delete(self, element_id: int) -> bool:
        """deletes element and returns True if deleted"""

    @abstractmethod
    def set_coords(self, element_id: int, x_y: tuple):
        """places the given element at a given position"""

    @abstractmethod
    def set_text_value(self, element_id: int, text: str):
        """changes the elements text"""

    @abstractmethod
    def get_width(self) -> int:
        """returns width"""

    @abstractmethod
    def get_height(self) -> int:
        """returns heigth"""

    def _scale_coords(self, x_y: tuple):
        """returns tuple values multiplied by factor"""
        return tuple(map(lambda c: int(c * self.scale), x_y))

class ScaledCanvasTk(ScaledCanvas):
    """draws onto tkinter canvas"""

    def __init__(self, tk_gui: Tk, width, height, scale=1.0):
        super().__init__(scale)
        self.tk_gui = tk_gui
        self.width = width
        self.height = height
        self.canvas = Canvas(tk_gui, width=self.width, height=self.height, bg="white")
        self.canvas.pack(side="left")
        self.update()

    def load_image_file(self, path: str):
        """takes file path and returns loaded image file reference"""

        image = (
            Image.open(path).convert("RGBA")
            if platform.system() != "Darwin"
            else Image.open(path).convert("RGB")
        )
        width, height = self._scale_coords(image.size)

        resized_image = image.resize((width, height), Image.ANTIALIAS)
        image_file = ImageTk.PhotoImage(resized_image)

        return image_file

    def create_image(self, x_coord: int, y_coord: int, image_file, anchor="c"):
        x_y = self._scale_coords((x_coord, y_coord))
        image = self.canvas.create_image(*x_y, image=image_file, anchor=anchor)
        self.update()
        return image

    def create_text(
        self,
        x_coord: int,
        y_coord: int,
        text: str = "",
        anchor: str = "c",
        fill: str = "black",
        font: str = "Helvetica 10",
    ):
        x_y = self._scale_coords((x_coord, y_coord))
        created_text = self.canvas.create_text(
            *x_y, font=font, fill=fill, anchor=anchor, text=text
        )
        return created_text

    def set_coords(self, element_id, x_y):
        x_y = self._scale_coords(x_y)
        canvas_coords = self.canvas.coords(element_id, x_y)
        self.update()
        return canvas_coords

    def delete(self, element_id: int) -> bool:
        self.canvas.delete(element_id)
        self.update()
        return True

    def set_text_value(self, element_id: int, text: str):
        self.canvas.itemconfig(element_id, text=text)
        self.update()

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def update(self):
        """updates the canvas containing gui"""
        self.tk_gui.update()
        
        
