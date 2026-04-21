NodeType = str





class Graph:
    def __init__(self, nodes: list[NodeType] = None,
                 edges: list[tuple[NodeType, NodeType, int]] = None) -> None:

        self.nodes: set[NodeType] = set() if nodes is None else set(nodes)
        self.edges: dict[NodeType, dict[NodeType, int]] = {}

        # за всеки възел създаваме празен речник със съседи
        for node in self.nodes:
            self.edges[node] = {}

        # добавяме ребрата, ако има подадени
        if edges is not None:
            for start, end, dist in edges:
                self.add_edge(start, end, dist)

    def __str__(self):
        result = ""
        for node in sorted(self.nodes):
            result += f"{node} -> {self.edges[node]}\n"
        return result

    def add_edge(self, start: NodeType, end: NodeType, dist: int) -> None:
        self.edges[start][end] = dist

    
    def dijkstra(self, initial: NodeType) -> tuple[dict[NodeType, int], dict[NodeType, NodeType]]:
        visited: dict[NodeType, int] = {initial: 0}   # най-кратко разстояние до всеки възел
        prev: dict[NodeType, NodeType] = {}           # предишен възел по най-краткия път

        nodes = set(self.nodes)                       # всички необработени възли

        while nodes:
            min_node = None

            # намираме възела с най-малко текущо разстояние
            for node in nodes:
                if node in visited:
                    if min_node is None or visited[node] < visited[min_node]:
                        min_node = node

            if min_node is None:
                break  # няма достижими възли

            nodes.remove(min_node)
            current_dist = visited[min_node]

            # обхождаме съседите на min_node
            for neighbor, weight in self.edges[min_node].items():
                new_dist = current_dist + weight

                # ако намерим по-кратък път → обновяваме
                if neighbor not in visited or new_dist < visited[neighbor]:
                    visited[neighbor] = new_dist
                    prev[neighbor] = min_node

        return visited, prev

# Възстановяване на пътя — трябва за логистичната система
def reconstruct_path(start: NodeType, end: NodeType, prev: dict[NodeType, NodeType]):
    path = []
    curr = end

    if curr not in prev and curr != start:
        return []  # няма път

    while curr is not None:
        path.append(curr)
        curr = prev.get(curr)

    return list(reversed(path))