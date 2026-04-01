NodeType = str


def dijkstra(graph, start: NodeType, end: NodeType):
    # Проверка дали възлите съществуват
    if start not in graph.nodes or end not in graph.nodes:
        return float('inf'), []

    # Инициализация
    dist = {node: float('inf') for node in graph.nodes}
    dist[start] = 0
    prev = {node: None for node in graph.nodes}
    unvisited = set(graph.nodes)

    while unvisited:
        # Намиране на най-близкия непосетен възел
        current = min(unvisited, key=lambda node: dist[node])

        # Ако най-близкият е на безкрайно разстояние, значи останалите са недостъпни
        if dist[current] == float('inf') or current == end:
            break

        unvisited.remove(current)

        # Обхождане на съседите (използваме .get() за безопасност)
        for neighbor, weight in graph.edges.get(current, {}).items():
            new_distance = dist[current] + weight
            if new_distance < dist[neighbor]:
                dist[neighbor] = new_distance
                prev[neighbor] = current

    # Възстановяване на пътя
    path = []
    curr = end
    if prev[curr] is None and curr != start:  # Няма открит път
        return float('inf'), []

    while curr is not None:
        path.append(curr)
        curr = prev[curr]

    path.reverse()
    return dist[end], path