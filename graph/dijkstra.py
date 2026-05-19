NodeType = str


class Graph:
    def __init__(self, nodes: list[NodeType] = None,
                 edges: list[tuple[NodeType, NodeType, int]] = None) -> None:

        self.nodes: set[NodeType] = set() if nodes is None else set(nodes)
        self.edges: dict[NodeType, dict[NodeType, int]] = {}


        for node in self.nodes:
            self.edges[node] = {}


        if edges is not None:
            for start, end, dist in edges:
                self.add_edge(start, end, dist)

    def add_edge(self, start: NodeType, end: NodeType, dist: int) -> None:
        if start not in self.nodes:
            self.nodes.add(start)
            self.edges[start] = {}
        if end not in self.nodes:
            self.nodes.add(end)
            self.edges[end] = {}


        self.edges[start][end] = dist

    def dijkstra(self, initial: NodeType) -> tuple[dict[NodeType, int], dict[NodeType, NodeType]]:
        visited: dict[NodeType, int] = {initial: 0}
        prev: dict[NodeType, NodeType] = {}
        nodes = set(self.nodes)

        while nodes:
            min_node = None
            for node in nodes:
                if node in visited:
                    if min_node is None or visited[node] < visited[min_node]:
                        min_node = node

            if min_node is None:
                break

            nodes.remove(min_node)
            current_dist = visited[min_node]

            for neighbor, weight in self.edges[min_node].items():
                new_dist = current_dist + weight
                if neighbor not in visited or new_dist < visited[neighbor]:
                    visited[neighbor] = new_dist
                    prev[neighbor] = min_node

        return visited, prev


    def reconstruct_path(self, start: NodeType, end: NodeType, prev: dict[NodeType, NodeType]):
        path = []
        curr = end
        if curr not in prev and curr != start:
            return []

        while curr is not None:
            path.append(curr)
            curr = prev.get(curr)


        return list(reversed(path))

    def __str__(self):
        result = ""
        for node in sorted(self.nodes):
            result += f"{node} -> {self.edges[node]}\n"
        return result