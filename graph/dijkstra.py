NodeType = str

class Graph:
    def __init__(self):
        self.nodes: set[NodeType] = set()
        self.edges: dict[NodeType, dict[NodeType, int]] = {}
        self.distances: dict[tuple[NodeType, NodeType], int] = {}

    def add_node(self, node: NodeType):
        self.nodes.add(node)
        self.edges[node] = {}

    def add_edge(self, from_node: NodeType, to_node: NodeType, distance: int):
        self.edges[from_node][to_node] = distance
        self.distances[(from_node, to_node)] = distance


def dijkstra(graph: Graph, start: NodeType, end: NodeType):
    # начални разстояния
    dist = {node: float('inf') for node in graph.nodes}
    dist[start] = 0

    # предходни възли
    prev = {node: None for node in graph.nodes}

    # множество от непосетени възли
    unvisited = set(graph.nodes)

    while unvisited:
        # намираме възела с най-малко текущо разстояние
        current = None
        for node in unvisited:
            if current is None or dist[node] < dist[current]:
                current = node

        # ако сме стигнали края — прекратяваме
        if current == end:
            break

        unvisited.remove(current)

        # обхождаме съседите
        for neighbor, weight in graph.edges[current].items():
            new_distance = dist[current] + weight

            if new_distance < dist[neighbor]:
                dist[neighbor] = new_distance
                prev[neighbor] = current

    # възстановяване на пътя
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = prev[node]

    path.reverse()
    return dist[end], path
