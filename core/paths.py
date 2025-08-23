from collections import defaultdict

def build_graph(markets):
    graph = defaultdict(list)
    for s, m in markets.items():
        if not m.get('active', True):
            continue
        base, quote = m['base'], m['quote']
        graph[quote].append((base, s, 'buy'))
        graph[base].append((quote, s, 'sell'))
    return graph

def find_cycles(graph, start='USDT', max_len=3):
    routes = []
    def dfs(curr, path, depth):
        if depth == 0:
            return
        for (nxt, sym, side) in graph.get(curr, []):
            new_path = path + [(sym, side, curr, nxt)]
            if nxt == start and len(new_path) >= 3:
                routes.append(new_path)
            if len(new_path) < max_len:
                dfs(nxt, new_path, depth-1)
    dfs(start, [], max_len)
    return routes

def invert_route(route):
    inv = []
    for (sym, side, frm, to) in route[::-1]:
        inv.append((sym, 'buy' if side=='sell' else 'sell', to, frm))
    return inv
