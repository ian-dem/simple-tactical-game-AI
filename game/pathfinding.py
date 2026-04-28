import heapq

def astar(gs, start, goal):
    sx, sy = start
    gx, gy = goal

    open_set = []
    heapq.heappush(open_set, (0, (sx, sy)))


    came_from = {}
    g_score = { (sx, sy): 0 }

    def neighbors(x, y):
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x+dx, y+dy
            if not gs.in_bounds(nx, ny):
                continue
            if gs.is_obstacle(nx, ny):
                continue
            if gs.get_unit_at(nx, ny) is not None and (nx, ny) != goal:
                continue
            yield (nx, ny)

    # MANHATTAN
    def heuristic(x, y):
        return abs(x - gx) + abs(y - gy)

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == (gx, gy):
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for n in neighbors(*current):
            tentative = g_score[current] + 1
            if n not in g_score or tentative < g_score[n]:
                came_from[n] = current
                g_score[n] = tentative
                f = tentative + heuristic(*n)
                heapq.heappush(open_set, (f, n))

    # no path return none
    return None  