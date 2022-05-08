import pathlib
import os
import random
import png
import time as t
import heapq


DIRECTIONS = [(1, 0), (0, 1), (-1, 0), (0, -1)] # West North East South

def load_view_strings() -> dict:
    views_strings = {}
    p = pathlib.Path("views/")
    for filepath in p.iterdir():
        with open(filepath, "r") as file:
            view = ""
            for i, line in enumerate(file):
                if i == 0:
                    view_name = line.strip()
                else:
                    view += line
        views_strings[view_name] = view
    return views_strings

VIEW_STRINGS = load_view_strings()

class Maze():
    def __init__(self, width, height, walls):
        self.height = height
        self.width = width
        self.cells = [(x,y) for x in range(width) for y in range(height)]
        self.walls = walls #stored as {(position): [(0,1), (1,0), (0, -1), (-1, 0)]}
    
    def print_out(self):
        string_map = [["W" for _ in range(self.width * 2 + 1)] for _ in range (self.height * 2 + 1)]
        for cell in self.cells:
            corrected_cell = [cell[0] * 2 + 1, cell[1] * 2 + 1]
            string_map[corrected_cell[1]][corrected_cell[0]] = " "
            for direction in DIRECTIONS:
                if direction not in self.walls[cell]:
                    wall_pos = (corrected_cell[0] + direction[0], corrected_cell[1] + direction[1])
                    row = string_map[wall_pos[1]]
                    row[wall_pos[0]] = " "
        
        rows = []
        for row in string_map:
            rows.append("".join(row))
        return "\n".join(rows)
    
    def calculate_view(self, player_position, player_direction):
        #looks forward
        cells_away = 0
        wall_ahead = False
        distance_wall_map = {}
        while cells_away <= 4 and not wall_ahead:
            current_cell = tuple(player_position[x] + cells_away * player_direction[x] for x in [0,1])
            walls = []
            #Check forward
            if player_direction in self.walls[current_cell]:
                wall_ahead = True
            #Check left
            if DIRECTIONS[DIRECTIONS.index(player_direction) - 1] in self.walls[current_cell]:
                walls.append("L")
            #Check right
            if DIRECTIONS[DIRECTIONS.index(player_direction) - 3] in self.walls[current_cell]:
                walls.append("R")  
            distance_wall_map[cells_away] = walls
            cells_away += 1

        closest_wall = cells_away - 1
        render_strings = ["base"]
        if closest_wall < 4:
            render_strings.append(f"wall{closest_wall}")

        for i in range(min(closest_wall + 1, 4)):
            if "L" not in distance_wall_map[i]:
                render_strings.append(f"open{i}l")
            if "R" not in distance_wall_map[i]:
                render_strings.append(f"open{i}r")
        
        view = ""
        for string in render_strings:
            if not view:
                view = VIEW_STRINGS[string]
            else:
                view = overlay_strings(view, VIEW_STRINGS[string])

        return view

    def okay_to_move_forward(self, player_position, player_direction):
        return not player_direction in self.walls[player_position]
        

def overlay_strings(base, overlay):
    if len(base) != len(overlay):
        raise ValueError
    combined_string = ""
    for i in range(len(base)):
        if overlay[i] == "x":#Clear character
            combined_string += " "
        elif overlay[i] == " ":
            combined_string += base[i]
        else:
            combined_string += overlay[i]
    
    return combined_string
                    
class Stack():
    def __init__(self):
        self.queue = []
    
    def push(self, item):
        self.queue.insert(0, item)
    
    def pop(self):
        return self.queue.pop(0)
    
    def peak(self):
        return self.queue[0]
    
    def is_empty(self):
        return not bool(self.queue)


def make_maze(width, height):
    tic = t.perf_counter()
    visited = {}
    walls = {}
    for x in range(width):
            for y in range(height):
                walls[(x,y)] = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                visited[(x,y)] = False
    
    stack = Stack()
    start = (int(random.random() * width), int(random.random() * height))
    visited[start] = True
    stack.push(start)

    visited_count = 1
    total_count = height * width
    while not stack.is_empty():
        current = stack.peak()
        options = []
        for direction in DIRECTIONS:
            potential_cell = (current[0] + direction[0], current[1] + direction[1])
            if (0 <= potential_cell[0] <= width - 1 and
                0 <= potential_cell[1] <= height -1 and
                not visited[potential_cell]):
               options.append(potential_cell)
        if options:
            chosen_cell = random.choice(options)
            #remove wall
            walls[current].remove((chosen_cell[0] - current[0], chosen_cell[1] - current[1]))
            walls[chosen_cell].remove((current[0] -  chosen_cell[0], current[1] - chosen_cell[1]))
            visited[chosen_cell] = True
            visited_count += 1
            stack.push(chosen_cell)

            percent_done = visited_count/total_count
            if (percent_done * 100) % 1 < 0.00001:
                print(f"{percent_done * 100 :0.1f}% done")
        else:
            stack.pop()

    toc = t.perf_counter()
    print(f"Maze Generated in {toc-tic:0.4f} seconds")
    return walls

def print_out_to_png(print_out, path = None):
    rows = print_out.split("\n")
    
    for i, row in enumerate(rows):
        rows[i] = list(row)

    if path:
        for cell in path:
            rows[cell[1] * 2 + 1][cell[0]* 2 + 1] = "P"
    png_list = []
    for row in rows:
        png_row = []
        for char in row:
            if path and char == "P":
                png_row += [0, 0, 255]
            elif char == "W":
                png_row += [0, 0, 0]
            else:
                png_row += [255, 255, 255]
        png_list.append(png_row)
    png.from_array(png_list, "RGB").save("maze.png")


### PATHFINDING
class Priority_Queue:
    def __init__(self) -> None:
        self.elements = []  # List of tuples of form [priority element]

    def is_empty(self) -> bool:
        return not self.elements

    def put(self, item, priority: float) -> None:
        heapq.heappush(self.elements, (priority, item))

    def get(self) -> "t":
        return heapq.heappop(self.elements)[1]


def a_star_pathfinding(walls, start, end):
    frontier = Priority_Queue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    tic = t.perf_counter()

    while not frontier.is_empty():
        current = frontier.get()

        if current == end:
            break
        adjacent_cells = []
        for direction in DIRECTIONS:
            if direction not in walls[current]:
                adjacent_cell = (current[0] + direction[0], current[1] + direction[1])
                adjacent_cells.append(adjacent_cell)

        for next_cell in adjacent_cells:
            new_cost = cost_so_far[current] + 1
            # if space not already in path or if a better path into space found
            if next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]:
                cost_so_far[next_cell] = new_cost
                priority = new_cost + abs(current[0] - next_cell[0]) + abs(current[1] + next_cell[1])
                frontier.put(next_cell, priority)
                came_from[next_cell] = current

    # Rebuild path :)
    current = end
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    toc = t.perf_counter()
    print(f"Path of length {len(path)} found in {toc - tic:0.4f} seconds")
    return path

if __name__ == "__main__":
    print("welcome to the maze")
    width = int(input("maze width? "))
    height = int(input("maze height? "))
    m = Maze(width, height, make_maze(width, height))
    path = a_star_pathfinding(m.walls, (0, 0), (width - 1, height - 1))
    print_out_to_png(m.print_out(), path)
    player_position = (0, 0)
    player_direction = (1, 0)
    print(m.calculate_view(player_position, player_direction))
    print(f"goal: ({width - 1}, {height - 1})")
    while True:
        if player_position == (width - 1, height  - 1):
            print("You win") 
        print(f"position: {player_position}")
        word_direction = ["east", "south", "west", "north"][DIRECTIONS.index(player_direction)]
        print(f"facing {word_direction}")
        move = input("")
        os.system("cls")
        if move == "w" and m.okay_to_move_forward(player_position, player_direction):
            new_pos = tuple(player_position[i] + player_direction[i] for i in [0, 1])
            player_position = new_pos
        if move == "a":
            player_direction = DIRECTIONS[DIRECTIONS.index(player_direction) - 1]
        if move == "d":
            player_direction = DIRECTIONS[DIRECTIONS.index(player_direction) - 3]
        print(m.calculate_view(player_position, player_direction))
