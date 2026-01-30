import heapq

def dijkstra(graph, start_id, end_id):
    distances = {node: float('inf') for node in graph.nodes}
    distances[start_id] = 0

    previous = {node: None for node in graph.nodes}

    queue = [(0, start_id)]

    while queue:
        current_distance, current_node = heapq.heappop(queue)

        if current_distance > distances[current_node]:
            continue

        for neighbor, weight in graph.edges[current_node].items():
            distance = current_distance + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current_node
                heapq.heappush(queue, (distance, neighbor))

    # възстановяване на пътя
    path = []
    node = end_id
    while node is not None:
        path.append(node)
        node = previous[node]

    path.reverse()
    return distances[end_id], path
