import numpy as np


def strongly_connected_components_path(vertices, edges):
    """
    Find the strongly connected components of a directed graph.

    Uses a recursive linear-time algorithm described by Gabow [1]_ to find all
    strongly connected components of a directed graph.

    Parameters
    ----------
    vertices : iterable
        A sequence or other iterable of vertices.  Each vertex should be
        hashable.

    edges : mapping
        Dictionary (or mapping) that maps each vertex v to an iterable of the
        vertices w that are linked to v by a directed edge (v, w).

    Returns
    -------
    components : iterator
        An iterator that yields sets of vertices.  Each set produced gives the
        vertices of one strongly connected component.

    Raises
    ------
    RuntimeError
        If the graph is deep enough that the algorithm exceeds Python's
        recursion limit.

    Notes
    -----
    The algorithm has running time proportional to the total number of vertices
    and edges.  It's practical to use this algorithm on graphs with hundreds of
    thousands of vertices and edges.

    The algorithm is recursive.  Deep graphs may cause Python to exceed its
    recursion limit.

    `vertices` will be iterated over exactly once, and `edges[v]` will be
    iterated over exactly once for each vertex `v`.  `edges[v]` is permitted to
    specify the same vertex multiple times, and it's permissible for `edges[v]`
    to include `v` itself.  (In graph-theoretic terms, loops and multiple edges
    are permitted.)

    References
    ----------
    .. [1] Harold N. Gabow, "Path-based depth-first search for strong and
       biconnected components," Inf. Process. Lett. 74 (2000) 107--114.

    .. [2] Robert E. Tarjan, "Depth-first search and linear graph algorithms,"
       SIAM J.Comput. 1 (2) (1972) 146--160.

    Examples
    --------
    Example from Gabow's paper [1]_.

    >>> vertices = [1, 2, 3, 4, 5, 6]
    >>> edges = {1: [2, 3], 2: [3, 4], 3: [], 4: [3, 5], 5: [2, 6], 6: [3, 4]}
    >>> for scc in strongly_connected_components_path(vertices, edges):
    ...     print(scc)
    ...
    set([3])
    set([2, 4, 5, 6])
    set([1])

    Example from Tarjan's paper [2]_.

    >>> vertices = [1, 2, 3, 4, 5, 6, 7, 8]
    >>> edges = {1: [2], 2: [3, 8], 3: [4, 7], 4: [5],
    ...          5: [3, 6], 6: [], 7: [4, 6], 8: [1, 7]}
    >>> for scc in  strongly_connected_components_path(vertices, edges):
    ...     print(scc)
    ...
    set([6])
    set([3, 4, 5, 7])
    set([8, 1, 2])

    """
    identified = set()
    stack = []
    index = {}
    boundaries = []

    def dfs(v):
        index[v] = len(stack)
        stack.append(v)
        boundaries.append(index[v])

        for w in edges[v]:
            if w not in index:
                # For Python >= 3.3, replace with "yield from dfs(w)"
                for scc in dfs(w):
                    yield scc
            elif w not in identified:
                while index[w] < boundaries[-1]:
                    boundaries.pop()

        if boundaries[-1] == index[v]:
            boundaries.pop()
            scc = set(stack[index[v]:])
            del stack[index[v]:]
            identified.update(scc)
            yield scc

    for v in vertices:
        if v not in index:
            # For Python >= 3.3, replace with "yield from dfs(v)"
            for scc in dfs(v):
                yield scc


def strongly_connected_components_tree(vertices, edges):
    """
    Find the strongly connected components of a directed graph.

    Uses a recursive linear-time algorithm described by Tarjan [2]_ to find all
    strongly connected components of a directed graph.

    Parameters
    ----------
    vertices : iterable
        A sequence or other iterable of vertices.  Each vertex should be
        hashable.

    edges : mapping
        Dictionary (or mapping) that maps each vertex v to an iterable of the
        vertices w that are linked to v by a directed edge (v, w).

    Returns
    -------
    components : iterator
        An iterator that yields sets of vertices.  Each set produced gives the
        vertices of one strongly connected component.

    Raises
    ------
    RuntimeError
        If the graph is deep enough that the algorithm exceeds Python's
        recursion limit.

    Notes
    -----
    The algorithm has running time proportional to the total number of vertices
    and edges.  It's practical to use this algorithm on graphs with hundreds of
    thousands of vertices and edges.

    The algorithm is recursive.  Deep graphs may cause Python to exceed its
    recursion limit.

    `vertices` will be iterated over exactly once, and `edges[v]` will be
    iterated over exactly once for each vertex `v`.  `edges[v]` is permitted to
    specify the same vertex multiple times, and it's permissible for `edges[v]`
    to include `v` itself.  (In graph-theoretic terms, loops and multiple edges
    are permitted.)

    References
    ----------
    .. [1] Harold N. Gabow, "Path-based depth-first search for strong and
       biconnected components," Inf. Process. Lett. 74 (2000) 107--114.

    .. [2] Robert E. Tarjan, "Depth-first search and linear graph algorithms,"
       SIAM J.Comput. 1 (2) (1972) 146--160.

    Examples
    --------
    Example from Gabow's paper [1]_.

    >>> vertices = [1, 2, 3, 4, 5, 6]
    >>> edges = {1: [2, 3], 2: [3, 4], 3: [], 4: [3, 5], 5: [2, 6], 6: [3, 4]}
    >>> for scc in strongly_connected_components_tree(vertices, edges):
    ...     print(scc)
    ...
    set([3])
    set([2, 4, 5, 6])
    set([1])

    Example from Tarjan's paper [2]_.

    >>> vertices = [1, 2, 3, 4, 5, 6, 7, 8]
    >>> edges = {1: [2], 2: [3, 8], 3: [4, 7], 4: [5],
    ...          5: [3, 6], 6: [], 7: [4, 6], 8: [1, 7]}
    >>> for scc in  strongly_connected_components_tree(vertices, edges):
    ...     print(scc)
    ...
    set([6])
    set([3, 4, 5, 7])
    set([8, 1, 2])

    """
    identified = set()
    stack = []
    index = {}
    lowlink = {}

    def dfs(v):
        index[v] = len(stack)
        stack.append(v)
        lowlink[v] = index[v]

        for w in edges[v]:
            if w not in index:
                # For Python >= 3.3, replace with "yield from dfs(w)"
                for scc in dfs(w):
                    yield scc
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w not in identified:
                lowlink[v] = min(lowlink[v], lowlink[w])

        if lowlink[v] == index[v]:
            scc = set(stack[index[v]:])
            del stack[index[v]:]
            identified.update(scc)
            yield scc

    for v in vertices:
        if v not in index:
            # For Python >= 3.3, replace with "yield from dfs(v)"
            for scc in dfs(v):
                yield scc


def strongly_connected_components_iterative(vertices, edges):
    """
    This is a non-recursive version of strongly_connected_components_path.
    See the docstring of that function for more details.

    Examples
    --------
    Example from Gabow's paper [1]_.

    >>> vertices = [1, 2, 3, 4, 5, 6]
    >>> edges = {1: [2, 3], 2: [3, 4], 3: [], 4: [3, 5], 5: [2, 6], 6: [3, 4]}
    >>> for scc in strongly_connected_components_iterative(vertices, edges):
    ...     print(scc)
    ...
    set([3])
    set([2, 4, 5, 6])
    set([1])

    Example from Tarjan's paper [2]_.

    >>> vertices = [1, 2, 3, 4, 5, 6, 7, 8]
    >>> edges = {1: [2], 2: [3, 8], 3: [4, 7], 4: [5],
    ...          5: [3, 6], 6: [], 7: [4, 6], 8: [1, 7]}
    >>> for scc in  strongly_connected_components_iterative(vertices, edges):
    ...     print(scc)
    ...
    set([6])
    set([3, 4, 5, 7])
    set([8, 1, 2])

    """
    identified = set()
    stack = []
    index = {}
    boundaries = []

    for v in vertices:
        if v not in index:
            to_do = [('VISIT', v)]
            while to_do:
                operation_type, v = to_do.pop()
                if operation_type == 'VISIT':
                    index[v] = len(stack)
                    stack.append(v)
                    boundaries.append(index[v])
                    to_do.append(('POSTVISIT', v))
                    # We reverse to keep the search order identical to that of
                    # the recursive code;  the reversal is not necessary for
                    # correctness, and can be omitted.
                    to_do.extend(
                        reversed([('VISITEDGE', w) for w in edges[v]]))
                elif operation_type == 'VISITEDGE':
                    if v not in index:
                        to_do.append(('VISIT', v))
                    elif v not in identified:
                        while index[v] < boundaries[-1]:
                            boundaries.pop()
                else:
                    # operation_type == 'POSTVISIT'
                    if boundaries[-1] == index[v]:
                        boundaries.pop()
                        scc = set(stack[index[v]:])
                        del stack[index[v]:]
                        identified.update(scc)
                        yield scc


def scc_graph(graph):
    vertices = list(graph[0])
    edges = graph[1]
    sequence = []
    for scc in strongly_connected_components_iterative(vertices, edges):
        sequence.append(scc)
    return sequence


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
