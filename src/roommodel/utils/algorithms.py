import numpy as np


def dist(start, goal):
    """Manhattan distance from start to goal.

    Args:
        start Tuple[int,int]: xy coordinates of start position.
        goal Tuple[int,int]: xy coordinates of goal position.

    """
    return np.abs(start[0] - goal[0]) + np.abs(start[1] - goal[1])


def make_graph(grid):
    v = set()
    e = {}
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            e[(i, j)] = set()
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            if grid[i, j] == 0:
                # no agent is present
                del e[(i, j)]
                continue
            v.add((i, j))
            # check agent to the right
            ni = i + 1
            nj = j
            if 0 <= ni < grid.shape[0]:
                if grid[ni, nj] == 1:
                    e[(i, j)].add((ni, nj))
                    e[(ni, nj)].add((i, j))
            # check agent to the left
            ni = i - 1
            nj = j
            if 0 <= ni < grid.shape[0]:
                if grid[ni, nj] == 1:
                    e[(i, j)].add((ni, nj))
                    e[(ni, nj)].add((i, j))
            # check agent on the top
            ni = i
            nj = j + 1
            if 0 <= nj < grid.shape[1]:
                if grid[ni, nj] == 1:
                    e[(i, j)].add((ni, nj))
                    e[(ni, nj)].add((i, j))
            # check agent below
            ni = i
            nj = j - 1
            if 0 <= nj < grid.shape[1]:
                if grid[ni, nj] == 1:
                    e[(i, j)].add((ni, nj))
                    e[(ni, nj)].add((i, j))
    return v, e


def lower_degrees(v, e):
    deg = []
    for key in e:
        d = len(e[key])
        deg.append((d, key))
    if len(deg) == 0:
        return v, e
    DEGREE = 0
    VERTEX = 1
    TOP = 0
    deg = sorted(deg, key=lambda x: x[DEGREE], reverse=True)
    while deg[TOP][DEGREE] > 1:
        top_vertex = deg[TOP][VERTEX]
        edges = e[top_vertex]
        top_degree, top_edge = sorted([(len(e[edge]), edge) for edge in edges], key=lambda x: x[DEGREE], reverse=True)[
            TOP]
        e[top_vertex].remove(top_edge)
        e[top_edge].remove(top_vertex)
        deg = []
        for key in e:
            d = len(e[key])
            deg.append((d, key))
        deg = sorted(deg, key=lambda x: x[DEGREE], reverse=True)
    return v, e


def show_pairs(v, e):
    cnt = 1
    pairs = []
    for key in list(v):
        if len(e[key]) > 0:
            i, j = key
            ni, nj = e[key].pop()
            pairs.append(((i, j), (ni, nj)))
        cnt += 1
    return pairs


def pair_positions(grid):
    v, e = make_graph(grid)
    v, e = lower_degrees(v, e)
    return show_pairs(v, e)
