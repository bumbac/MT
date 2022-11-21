from collections import deque
from dataclasses import dataclass

import numpy as np
from .constants import MAP_SYMBOLS, MAP_VALUES


def create_grid(width, height, gate=None):
    if width < 3 or height < 3:
        raise ValueError("Map cannot have dimensions lower than 3 due to walls")
    dimensions = (height, width)
    grid = np.zeros(shape=dimensions)
    grid[:, 0] = -1
    grid[:, -1] = -1
    grid[0, :] = -1
    grid[-1, :] = -1
    if gate:
        x, y = gate
        if 0 < x < width and 0 < y < height:
            np_coords = (y, x)
            grid[np_coords] = 100
        else:
            raise ValueError("Gate in invalid position "+str(gate)+" in grid " + str(dimensions))
    return grid


def load_grid(filename):
    with open(filename) as f:
        dimensions = list(map(int, f.readline().split()))
        width, height = dimensions
        dimensions = height, width
        grid = np.zeros(shape=dimensions)
        for row in range(height):
            line = f.readline().strip()
            for column, c in enumerate(line):
                if c not in MAP_SYMBOLS:
                    raise ValueError("Unknown character when loading map from file")
                np_coords = (row, column)
                grid[np_coords] = MAP_SYMBOLS[c]
        return grid


def save_grid(grid, filename):
    columns, rows = grid.shape
    with open(filename, "w+") as f:
        f.write(str(columns)+" "+str(rows)+"\n")
        for row in range(rows):
            for c in grid[row]:
                f.write(MAP_VALUES[c])
            f.write("\n")


def normalize_grid(static_field):
    return static_field / np.nanmax(static_field[static_field != np.inf])


def compute_static_field(grid, normalize=True):
    @dataclass
    class Node:
        coords: (int, int)
        obstacle: bool
        price: int = float("inf")

        def enter(self, parent):
            self.price = parent.price + self.distance(parent)

        def distance(self, other):
            sigma = np.power(self.coords[0] - other.coords[0], 2)
            sigma += np.power(self.coords[1] - other.coords[1], 2)
            return np.sqrt(sigma)

        def neighbours(self, width, height):
            valid_coords = []
            for x in [-1, 0, 1]:
                for y in [-1, 0, 1]:
                    if 0 <= self.coords[0] + x < width and 0 <= self.coords[1] + y < height:
                        if x == 0 and y == 0:
                            continue
                        valid_coords.append((self.coords[0] + x, self.coords[1] + y))
            return valid_coords

    q = deque()
    grid_nodes = []
    gate = None
    height, width = grid.shape
    for y in range(height):
        grid_nodes.append([])
        for x in range(width):
            coords = (x, y)
            np_coords = (y, x)
            node = Node(coords, grid[np_coords] < 0)
            if grid[np_coords] == 100:
                gate = Node(coords, False)
                node = gate
            grid_nodes[y].append(node)

    if not gate:
        raise ValueError("Gate is not present in the map. Can't compute static field.")

    gate.price = 0
    q.append(gate)
    while q:
        current_node = q.pop()
        while current_node.obstacle:
            current_node = q.pop()
        for coords in current_node.neighbours(width, height):
            x, y = coords
            other_node = grid_nodes[y][x]
            if not other_node.obstacle:
                distance = current_node.distance(other_node)
                if current_node.price + distance < other_node.price:
                    other_node.enter(current_node)
                    q.append(other_node)
    static_field = np.zeros(grid.shape)
    for x in range(width):
        for y in range(height):
            np_coords = (y, x)
            static_field[np_coords] = grid_nodes[y][x].price
    if normalize:
        return normalize_grid(static_field)
    return static_field
