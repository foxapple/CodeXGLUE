#!/usr/local/bin/python
import Tkinter
from color import ColorGenerator
from itertools import izip
from tilemap import *

__all__ = ('TileMapGUI',)

class TileMapGUI(object):
    def __init__(self, tile_map, tile_size, tile_colors, rooms=None, walk_graph=None, tk=None):
        self.tk = tk or root_tk
        self.tk.title("Tile map")
        self.tile_size_x = tile_size
        self.tile_size_y = tile_size
        self.tile_colors = dict(tile_colors)
        self.width = self.tile_size_x * tile_map.width
        self.height = self.tile_size_y * tile_map.height
        self.view_width = 640        # tk.winfo_screenwidth()
        self.view_height = 512       # tk.winfo_screenheight()
        self.canvas = Tkinter.Canvas(self.tk,
            width=self.view_width,
            height=self.view_height,
            bg='white',
            scrollregion=(0, 0, self.width, self.height),
            xscrollincrement=5,
            yscrollincrement=5)
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<MouseWheel>', self.scroll)
        self.canvas.bind('<KeyPress>', self.keypress)
        self.create_tile_map(tile_map)
        if rooms:
            self.create_rooms(rooms)
        if walk_graph:
            self.create_walk_graph(walk_graph)
        self.create_grid(self.tile_size_x, self.tile_size_y)
        self.canvas.focus_set()

    def create_tile_map(self, tile_map):
        self.tile_map = tile_map.copy()
        self.tile_objects = []
        for y in range(self.tile_map.height):
            row = []
            for x in range(self.tile_map.width):
                tile = self.canvas.create_rectangle(
                    x * self.tile_size_x,
                    y * self.tile_size_y,
                    (x + 1) * self.tile_size_x,
                    (y + 1) * self.tile_size_y,
                    fill='',
                    outline='',
                    tags='tile')
                row.append(tile)
            self.tile_objects.append(row)
        self.update_tile_map()

    def update_tile_map(self):
        default_color = self.tile_colors[None]
        for y in range(self.tile_map.height):
            for x in range(self.tile_map.width):
                value = self.tile_map[x,y]
                tile = self.tile_objects[y][x]
                color = self.tile_colors.get(value, default_color)
                self.canvas.itemconfig(tile, fill=color)

    def create_rooms(self, rooms):
        self.rooms = list(rooms)
        self.room_objects = []
        color = '#888888'
        outline_width = 1
        for room in self.rooms:
            rect = self.canvas.create_rectangle(
                room.tl.x * self.tile_size_x,
                room.tl.y * self.tile_size_y,
                room.br.x * self.tile_size_x - outline_width,
                room.br.y * self.tile_size_y - outline_width,
                fill='',
                outline=color,
                width=outline_width,
                tags='room')
            self.room_objects.append(rect)

    def create_walk_graph(self, walk_graph):
        self.walk_graph = walk_graph.copy()
        two_way_line_options = dict(
            fill='#00ff00',
            width=2,
            tags='walk_graph')
        one_way_line_options = dict(
            fill='#ff0000',
            width=2,
            tags='walk_graph')
        def tile_center(coord):
            return [(coord.x + 0.5) * self.tile_size_x, (coord.y + 0.5) * self.tile_size_x]
        for y in range(self.tile_map.height):
            for x in range(self.tile_map.width):
                coord = Coord(x, y)
                can_reach = walk_graph.get(coord)
                if not can_reach: continue
                for other_coord in can_reach:
                    two_way = (coord in walk_graph.get(other_coord, []))
                    if two_way:
                        self.canvas.create_line(*(tile_center(coord) + tile_center(other_coord)),
                            **two_way_line_options)
                    else:
                        self.canvas.create_line(*(tile_center(coord) + tile_center(other_coord)),
                            **one_way_line_options)

    def create_grid(self, grid_size_x, grid_size_y):
        grid_coords = []
        even = True
        for x in range(grid_size_x, self.width, grid_size_x):
            line_start = [x, -1]
            line_end = [x, self.height + 1]
            if even:
                grid_coords += line_start
                grid_coords += line_end
            else:
                grid_coords += line_end
                grid_coords += line_start
            even = not even
        if even:
            grid_coords += [-1, -1]
        else:
            grid_coords += [self.width + 1, self.height + 1]
        for y in range(grid_size_y, self.height, grid_size_y):
            line_start = [-1, y]
            line_end = [self.width + 1, y]
            if even:
                grid_coords += line_start
                grid_coords += line_end
            else:
                grid_coords += line_end
                grid_coords += line_start
            even = not even
        if even:
            grid_coords += [-1, -1]
        else:
            grid_coords += [self.width + 1, self.height + 1]
        grid_options = dict(outline='#004400', fill='', tags='grid', state=Tkinter.DISABLED)
        self.canvas.create_polygon(*grid_coords, **grid_options)
        self.bring_to_front()

    def click(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def scroll(self, event):
        if event.state == 0:
            self.canvas.yview(Tkinter.SCROLL, -event.delta, Tkinter.UNITS)
        elif event.state == 1:
            self.canvas.xview(Tkinter.SCROLL, -event.delta, Tkinter.UNITS)

    def keypress(self, event):
        if event.keysym == 'Escape':
            self.tk.destroy()

    def run(self):
        self.tk.mainloop() 

    @staticmethod
    def process_ids():
        # Only works in Mac OS X
        import subprocess
        script = '''tell app "System Events" to return id of every process whose name is "Python"'''
        output = subprocess.check_output(['/usr/bin/osascript', '-e', script])
        return set(s.strip() for s in output.split(','))

    def bring_to_front(self):
        # Only works in Mac OS X
        import subprocess, textwrap
        script = textwrap.dedent('''\
            tell app "System Events"
                repeat with proc in every process whose name is "Python"
                    if id of proc is %(procid)s then
                        set frontmost of proc to true
                        exit repeat
                    end if
                end repeat
            end tell''')
        script %= {
            'procid': root_process_id,
            }
        subprocess.call(['/usr/bin/osascript', '-e', script])

# Set up global `root_tk` and `root_process_id` variables
_process_ids = TileMapGUI.process_ids()
root_tk = Tkinter.Tk()
root_process_id = next(iter(TileMapGUI.process_ids() - _process_ids))
del _process_ids
