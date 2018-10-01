import socket
import sys
from copy import deepcopy
import time

t1 = time.time()

############### init ###############

def init_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 31415))
    return s

def init_map(node):                 # character gets with relative direction '^'
    time.sleep(0.1)
    for i in range(-2, 3):
        game_map[node[0]][node[1]] = ' '
        if i == 0:
            game_map[node[0]][node[1] - 2: node[1]] = [a for a in s.recv(2).decode('utf-8')]
            game_map[node[0]][node[1] + 1: node[1] + 2 + 1] = [a for a in s.recv(2).decode('utf-8')]
        else:
            game_map[node[0] + i][node[1] - 2: node[1] + 2 + 1] = [a for a in s.recv(5).decode('utf-8')]


############### print map ###############

def print_map(node, direction):                                     
    char_direction = {0: '^', 1: '>', 2: 'v', 3: '<'}
    game_map_print = deepcopy(game_map)                                     # deepcopy, remeber to remove all print_map before submitting   
    game_map_print[node[0]][node[1]] = char_direction[direction]
    for i in game_map_print:
        for j in i:
            print(j, end='')
        print()


############### get map and move ###############

def auto_agent(vertex, direction, special=0):           # speical == 1: cruising auto agent; special == 2: remove 'T' which contain '?' around after original auto agent 
    path = [vertex]
    while path:
        path = get_path(vertex, special)
        if path:
            vertex, direction = path_move(path, direction)
            if game_map[vertex[0]][vertex[1]] == '$':
                break
    return vertex, direction


def get_path(node, special):         # bfs to get next node and the path
    goal = ['?']
    tool_list = ['a', 'k', 'd', '$']
    all_path = set()
    all_path.add(node)
    queue = [(node, [node])]
    while queue:
        vertex, path = queue.pop(0)

        mark = 0
        if special == 1 and len(path) >= 2:
            for i in range(1, len(path)):
                if mark == 0 and game_map[path[i - 1][0]][path[i - 1][1]] == '~' and game_map[path[i][0]][path[i][1]] != '~':
                    mark = 1            # no raft
                if mark == 1 and game_map[path[i][0]][path[i][1]] == '~':
                    mark = 2            # no raft but cruising
                    break
                if mark == 1 and game_map[path[i][0]][path[i][1]] == 'T':
                    mark = 0            # have raft
        if mark == 2:
            continue 

        for next_vertex in get_next_vertices(vertex, special):
            if next_vertex in set(get_next_vertices(vertex, special)) - set(path) - all_path:
                if special != 2:
                    extra_list = [a for a in '-' if tools['k'] > 0] + [a for a in 'T' if tools['a'] > 0]        # extra_list for after corresponding tools collection
                else:
                    extra_list = [a for a in '-' if tools['k'] > 0]         # dont eliminate 'T' without '?' around

                if game_map[next_vertex[0]][next_vertex[1]] in tool_list + extra_list:       # higher priority for tools collection
                    return path + [next_vertex]
                elif unknow_check(next_vertex):
                    return path + [next_vertex]
                elif unknow_check_for_trees(next_vertex) and special == 2:
                    return path + [next_vertex]
                else:
                    queue.append((next_vertex, path + [next_vertex]))
                    all_path.add(next_vertex)


def get_next_vertices(vertex, special):
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    priority = {'$': 0, 'k': 1, 'd': 2, 'a': 3, ' ': 5, 'r': 6}         # delete '?', ok? -- '?': 4,
    if tools['k'] > 0:
        priority['-'] = len(priority) + 1
    if tools['a'] > 0 and tools['r'] < 1:       # keep 1 raft in hand in map discovering phase
        priority['T'] = len(priority) + 1
    if tools['r'] > 0 and priority.get('T') is not None:                          # no auto water move in auto_agent phase
        del priority['T']
    if special == 2 and tools['a'] > 0:
        priority['T'] = len(priority) + 1

    if special == 1 and tools['r'] > 0:
        priority['~'] = len(priority) + 1

    pending_list = []
    for c in [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list]:
        if game_map[c[0]][c[1]] in priority:
            pending_list.append([c, priority[game_map[c[0]][c[1]]]])                    # ((r, c), value for priority)
    pending_list = [a[0] for a in sorted(pending_list, key = lambda x: x[1])]           # return (r, c) ony
    return pending_list
            

def unknow_check(vertex):                   
    for i in range(-2, 3, 1):
        for j in range(-2, 3, 1):
            if game_map[vertex[0] + i][vertex[1] + j] == '?':
                return True

def unknow_check_for_trees(node):
    if game_map[node[0]][node[1]] == 'T':
        priority = {'$': 0, 'k': 1, 'd': 2, 'a': 3, '?': 4, ' ': 5, 'r': 6}
        if tools['k'] > 0:
            priority['-'] = len(priority) + 1
    
        direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        all_path = set()
        all_path.add(node)
        queue = [(node, [node])]
        while queue:
            vertex, path = queue.pop(0)
            next_vertices = [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list]
            for next_vertex in set(next_vertices) - set(path) - all_path:
                if game_map[next_vertex[0]][next_vertex[1]] in priority:
                    if game_map[next_vertex[0]][next_vertex[1]] == '?':
                        return True
                    else:
                        queue.append((next_vertex, path + [next_vertex]))
                        all_path.add(next_vertex)


def path_move(path, direction):
    if path:
        if len(path) > 1:
            for i in range(len(path) - 1):
                direction = step_move(path[i], path[i + 1], direction)
        return path[-1], direction


def step_move(cur_node, next_node, direction):
    if game_map[next_node[0]][next_node[1]] in tools:                   # tools collection while step moving
        tools[game_map[next_node[0]][next_node[1]]] += 1

    if game_map[cur_node[0]][cur_node[1]] == '~' and game_map[next_node[0]][next_node[1]] != '~':       # special tools consuming
        tools['r'] = 0


    direction_dict = {(-1, 0): 0, (0, 1): 1, (1, 0): 2, (0, -1): 3}
    new_direction = direction_dict[(next_node[0] - cur_node[0], next_node[1] - cur_node[1])]
    var = direction - new_direction
    if abs(var) == 3:
        var = int(abs(var)/var) * (-1)
    action_list = ['l'] * var + ['f'] if var >= 0 else ['r'] * (var * (-1)) + ['f']

    switch = 0          # dedicate for C or B or U before moving
    switch_dict = {'T': 'C', '-': 'U', '*': 'B'}
    if game_map[next_node[0]][next_node[1]] in switch_dict:
        switch = switch_dict[game_map[next_node[0]][next_node[1]]]

    for i in range(len(action_list)):

        if switch != 0 and i == len(action_list) - 1:
            s.send(bytes(switch, 'utf-8'))
            receive = []
            for k in range(24):
                while len(receive) < k + 1:
                    receive.append(s.recv(1).decode('utf-8'))

            if switch == 'B':
                tools['d'] -= 1             # tools consuming
            if switch == 'C':
                if tools['r'] < 1:
                    tools['r'] += 1         # special tools collection, only 1 raft maximum in hand

            if game_map[cur_node[0]][cur_node[1]] == '~' and game_map[next_node[0]][next_node[1]] != '~':       # repeat codes for agent chopping on boat
                tools['r'] = 0

        action = action_list[i]
        s.send(bytes(action, 'utf-8'))
        receive = []
        for k in range(24):
            while len(receive) < k + 1:
                receive.append(s.recv(1).decode('utf-8'))

        if action == 'f':
            visited.add(tuple(next_node))       # record visited nodes
            if game_map[next_node[0]][next_node[1]] != '~':
               game_map[next_node[0]][next_node[1]] = ' '
            if new_direction  == 0:
                game_map[next_node[0] - 2][next_node[1] - 2: next_node[1] + 2 + 1] = receive[0:5]
            elif new_direction == 1:
                for i in range(-2, 3):
                    game_map[next_node[0] + i][next_node[1] + 2] = receive[i + 2]
            elif new_direction == 2:
                game_map[next_node[0] + 2][next_node[1] - 2: next_node[1] + 2 + 1] = receive[0:5][::-1]
            else:                               # new_direction == 3:
                for i in range(-2, 3):
                    game_map[next_node[0] - i][next_node[1] - 2] = receive[i + 2]
        elif action == 'r':
            direction = (direction + 1) % 4 
        elif action == 'l':
            direction = (direction - 1) % 4
        else:                                   # for tool collection and obstacle removal
            pass

    return direction



############### target path, end node can be wall or tree and so on ###############

def path_node_to_node(node, end_node):          # although the end_node is wall or T, it will go on
    if node == end_node:
        return [node]
    weight = {'*': 1000, 'a': 10, 'k': 10, 'd': 10, '$': 10, ' ': 1}
    if tools['k'] > 0:
        weight['-'] = 10
    if tools['a'] > 0:
        weight['T'] = 10
    if tools['r'] > 0:
        weight['~'] = 20

    all_path_node = set()
    all_path_node.add(node)
    queue = [(node, [node], weight[game_map[node[0]][node[1]]])]
    while queue:
        queue = sorted(queue, key = lambda x: x[2])
        vertex, path, cost = queue.pop(0)
        for next_vertex in set(pps_get_next_vertices(vertex, end_node)) - set(path) - all_path_node:
            if next_vertex == end_node:                                    # higher priority for tools collection
                return path + [next_vertex]
            else:
                queue.append((next_vertex, path + [next_vertex], cost + weight[game_map[next_vertex[0]][next_vertex[1]]]))
                all_path_node.add(next_vertex)

def pps_get_next_vertices(vertex, end_node):
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    priority = {'$': 0, 'k': 1, 'd': 2, 'a': 3, ' ': 4}

    if tools['k'] > 0:
        priority['-'] = len(priority) + 1
    if tools['a'] > 0:
        priority['T'] = len(priority) + 1
    if tools['r'] > 0:
        priority['~'] = len(priority) + 1

    pending_list = []
    vertices = [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list]
    if end_node in vertices:
        return [end_node]
    for c in vertices:
        if game_map[c[0]][c[1]] in priority:
            pending_list.append([c, priority[game_map[c[0]][c[1]]]])                    # ((r, c), value for priority)
    pending_list = [a[0] for a in sorted(pending_list, key = lambda x: x[1])]           # return (r, c) ony
    return pending_list



############### tools ###############

def item_not_get_check():
    for i in item_not_get:
        item_not_get[i] = []                # wipe due data before re-check
    for i in range(len(game_map)):
        for j in range(len(game_map[0])):
            if game_map[i][j] in item_not_get:
                item_not_get[game_map[i][j]].append((i, j))


############### wall_connect ###############

def wall_connect(*arg):
    item_not_get_check()
    item_check = list(arg)
    item_nodes = []
    connect_nodes = set()
    for char in item_check:
        item_nodes.extend(item_not_get[char])
    for node in item_nodes:
        if node not in connect_nodes:
            connect_nodes = connect_nodes | dfs_wall_connect(node, item_check)
    return connect_nodes

def dfs_wall_connect(node, item_check):
    all_path = set()
    all_path.add(node)
    queue = [(node, [node])]
    while queue:
        vertex, path = queue.pop(0)
        for next_vertex in set(def_wall_connect_get_next_vertices(vertex, item_check)) - set(path) - all_path:
            queue.append((next_vertex, path + [next_vertex]))
            all_path.add(next_vertex)
    return all_path

def def_wall_connect_get_next_vertices(vertex, item_check):
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    pending_list = []
    for c in [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list]:
        if game_map[c[0]][c[1]] in item_check + ['*']:
            pending_list.append(c)
    return pending_list


############### rehearsal - method - shrink map/ change coordination ###############

def target_plan(current_node, target_node, back_node, available_nodes):            # bfs for shrinked map

    all_known_nodes = set()
    all_known_nodes.add(current_node)
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    queue = [(current_node, [current_node])]
    while queue:
        vertex, path = queue.pop(0)
        for next_vertex in set([(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list]) - set(path) - all_known_nodes:
            if game_map[next_vertex[0]][next_vertex[1]] not in ['?', '.']:
                queue.append((next_vertex, path + [next_vertex]))
                all_known_nodes.add(next_vertex)
    r_data = [a[0] for a in all_known_nodes]
    r1 = min(r_data)
    r2 = max(r_data)
    c_data = [a[1] for a in all_known_nodes]
    c1 = min(c_data)
    c2 = max(c_data)

    new_tools = deepcopy(tools)
    new_tools['%'] = 0              # dedicated for back node

    new_column = c2 - c1 + 1
    new_row = r2 - r1 + 1
    shrinked_map = [['?' for i in range(new_column)] for j in range(new_row)]
    for i in range(new_row):
        for j in range(new_column):
            char = game_map[i + r1][j + c1]
            shrinked_map[i][j] = char

    new_current_node = (current_node[0] - r1, current_node[1] - c1)
    new_target_node = (target_node[0] - r1, target_node[1] - c1)
    new_back_node = (back_node[0] - r1, back_node[1] - c1)
    new_available_nodes = [(a[0] - r1, a[1] - c1) for a in available_nodes]
    shrinked_map[new_back_node[0]][new_back_node[1]] = '%'
    
    try:
        scatter_path, process_game_map_copy, process_tools_copy, new_available_nodes = \
                dfs_for_rehearsal(new_target_node, shrinked_map, new_tools, [new_current_node], new_available_nodes, new_row, new_column)
    except TypeError:
        scatter_path = []
        
    if scatter_path:
        return [(a[0] + r1, a[1] + c1) for a in scatter_path]
        

# dfs for rehearsal #

def dfs_for_rehearsal(target_node, process_game_map_copy, process_tools_copy, jump_path, available_nodes, nr, nc, back_mark=0):   # target node for referece only, no change
    process_game_map_copy = deepcopy(process_game_map_copy)
    process_tools_copy = deepcopy(process_tools_copy)

    for i in jump_path:
        process_char = process_game_map_copy[i[0]][i[1]]
        if back_mark == 0:
            if process_char not in ['~', '%']:
                process_game_map_copy[i[0]][i[1]] = ' '
        else:
            if process_char != '~':
                process_game_map_copy[i[0]][i[1]] = ' '

    edge_list = []
    process_tools_nodes = []
    if process_game_map_copy[jump_path[-1][0]][jump_path[-1][1]] != '~':
        edge_list, process_game_map_copy, process_tools_copy, process_tools_nodes, water_edge_list = \
                bfs_for_edge_and_tools(jump_path[-1], target_node, process_game_map_copy, process_tools_copy, nr, nc, back_mark)
    else:               # on water, after cruising
        water_edge_list = jump_path

    if back_mark == 0:
        if process_tools_copy['$'] == 1:
            back_mark = 1   
    if back_mark == 1:
        if process_tools_copy['%'] == 1:
            return jump_path + process_tools_nodes, process_game_map_copy, process_tools_copy, available_nodes
    
    landing_routines = []
    if process_tools_copy['r'] > 0:
        landing_routines = available_islands(process_game_map_copy, process_tools_copy, water_edge_list, back_mark)

    weight = {'$': 3, 'd': 1, 'a': 1, 'k': 1}           # weight, tools not get 

    if back_mark == 1:
        weight['%'] = 3

    item_and_weight_list = []
    for i in range(len(process_game_map_copy)):
        for j in range(len(process_game_map_copy[0])):
            if process_game_map_copy[i][j] in weight:
                item_and_weight_list.append((i, j, weight[process_game_map_copy[i][j]]))        # (i, j, weight of itself)
    d_para = process_tools_copy['d']

    item_weight_surrounding = []
    for i in item_and_weight_list:
        item_weight_surrounding.append((i[0], i[1], i[2], obstacle_surrounding(i, process_game_map_copy, process_tools_copy, nr, nc)))
    
    edge_list_process = []
    if [a for a in item_weight_surrounding if a[3]]:
        edge_list_process = sorted([[a, weight_cal(a, item_weight_surrounding, d_para, process_game_map_copy)] for a in edge_list], \
                key = lambda x: (-x[1], abs(target_node[0] - x[0][0]) + abs(target_node[1] - x[0][1])))


    edge_list = [a[0] for a in edge_list_process if a[1] >= d_para]
 
    full_attempt_lines = []
    if process_tools_copy['d'] > 0:
        full_attempt_lines.extend([process_tools_nodes + [a] for a in edge_list])
    if process_tools_copy['r'] > 0:
        full_attempt_lines.extend([process_tools_nodes + a for a in landing_routines])

    if full_attempt_lines:
        for attempt_line in full_attempt_lines:
            process_tools_copy_copy = deepcopy(process_tools_copy)
            if attempt_line[-1] in edge_list:
                process_tools_copy_copy['d'] -= 1

            elif process_game_map_copy[attempt_line[-2][0]][attempt_line[-2][1]] == '~':
                process_tools_copy_copy['r'] = 0
                if process_game_map_copy[attempt_line[-1][0]][attempt_line[-1][1]] == '*' and process_tools_copy_copy['d'] > 0:
                    process_tools_copy_copy['d'] -= 1
            
            try:
                scatter_path, process_game_map_copy, process_tools_copy, available_nodes = \
                        dfs_for_rehearsal(target_node, process_game_map_copy, process_tools_copy_copy, jump_path + attempt_line, available_nodes, nr, nc, back_mark)
            except TypeError:
                scatter_path = []

            if scatter_path:
                return scatter_path, process_game_map_copy, process_tools_copy, available_nodes

   
   
# bfs for edge and collect tools at the same time #

def bfs_for_edge_and_tools(node, target_node, process_game_map_copy, process_tools_copy, nr, nc, bm):      # node is current node in jump_nodes, for a* in bfs

    process_tools_nodes = []
    edge_list = []
    water_edge_list = []
    goal = ['*']
    all_path_nodes = set()
    all_path_nodes.add(node)
    queue = [(node, [node])]
    while queue:
        vertex, path = queue.pop(0)
        next_vertices, process_tools_copy, available = bfs_get_next_vertices(vertex, node, target_node, process_game_map_copy, process_tools_copy, nr, nc, bm)
        if next_vertices:
            for next_vertex in next_vertices:
                if next_vertex in set(next_vertices) - set(path) - all_path_nodes - set(edge_list):
                    next_char = process_game_map_copy[next_vertex[0]][next_vertex[1]]
    
                    obstacle_list = [a for a in set(['*', '-', 'T']) - (set(available.keys()) - set(['*']))]
                    if next_char in obstacle_list:
                        edge_list.append(next_vertex)
                    
                    elif next_char == '~':
                        water_edge_list.append(next_vertex)

                    else:
                        queue.append((next_vertex, path + [next_vertex]))
                        all_path_nodes.add(next_vertex)

                        if process_tools_copy['a'] > 0 and next_char == 'T':
                            if process_tools_copy['r'] == 0:
                                process_tools_copy['r'] += 1
                                process_tools_nodes.append(next_vertex)
                        if next_char in process_tools_copy:             # if it is not back to init node process, '%' cannot be eliminated
                            if next_char != '%' or bm == 1:
                                process_tools_copy[next_char] += 1
                                process_tools_nodes.append(next_vertex)
                            if next_char == '%' and bm == 1:
                                return edge_list, process_game_map_copy, process_tools_copy, process_tools_nodes, water_edge_list
                            if next_char == '$':            # '$' and '%' in the same bfs area
                                bm = 1    
                        if (next_char != '%' or bm == 1) and not (process_tools_copy['r'] > 0 and next_char == 'T'):
                            process_game_map_copy[next_vertex[0]][next_vertex[1]] = ' '
    return edge_list, process_game_map_copy, process_tools_copy, process_tools_nodes, water_edge_list


def bfs_get_next_vertices(vertex, node, target_node, process_game_map_copy, process_tools_copy, nr, nc, bm):           # node is current node in jump_nodes, for A*
    process_tools_copy = deepcopy(process_tools_copy)
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    priority = {'$': 0, 'k': 1, 'd': 2, 'a': 3, '*': 4, ' ': 5}

    if process_tools_copy['a'] > 0:                     # with axe in hand, tree is not obstacle any more
        priority['T'] = len(priority) + 1
    if process_tools_copy['k'] > 0:                     # with key in hand, door is not obstacle any more
        priority['-'] = len(priority) + 1

    priority['~'] = 10      # record water edge in current island
    priority['%'] = 0       # dedicate for back to start node while it should be put into list otherwise it will become obstacle

    pending_list = []
    for c in [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list if 0 <= vertex[0] + a[0] < nr and 0 <= vertex[1] + a[1] < nc]:
        if process_game_map_copy[c[0]][c[1]] in priority:
            pending_list.append([c, priority[process_game_map_copy[c[0]][c[1]]]])                    # ((r, c), value for priority)
    pending_list = [a[0] for a in sorted(pending_list, key = lambda x: (x[1], abs(node[0] - x[0][0]) + \
            abs(node[1] - x[0][1]) + abs(target_node[0] - x[0][0]) + abs(target_node[1] - x[0][1])))]           # return (r, c) only, a star
    return pending_list, process_tools_copy, priority


# bfs+dfs after bfs_for_edge_and_tools(...) to find tools on other islands

def available_islands(process_game_map_copy, process_tools_copy, water_edge_list, bm):

    priority = {'$': 3, 'd': 1, 'a': 1, 'k': 1}
    if bm == 1:
        priority['%'] = 3

    tree_list = []
    item_not_get_list = []
    for i in range(len(process_game_map_copy)):
        for j in range(len(process_game_map_copy[0])):
            if process_game_map_copy[i][j] in priority:
                item_not_get_list.append((i, j))
            if process_game_map_copy[i][j] == 'T':
                tree_list.append((i, j))
    
    landing_routines = []
    for item in item_not_get_list:
        landing_routine = bfs_for_item_on_islands(item, water_edge_list, process_game_map_copy, process_tools_copy, bm)
        if landing_routine:
            landing_routines.append(landing_routine)
    return landing_routines



def bfs_for_item_on_islands(item, water_edge_list, process_game_map_copy, process_tools_copy, bm):     # from item to water_edge_list, uniform-cost search

    weight = {'*': 10000, '~': 1, 'a': 10, 'k': 10, 'd': 10, '$': 10, ' ':-1000}
    if process_tools_copy['a'] > 0:
        weight['T'] = 15                 # tree is extremely important
    if process_tools_copy['k'] > 0:
        weight['-'] = 10
    if bm == 1:
        weight['%'] = 10
    
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)] 
    all_path_nodes = set()		
    all_path_nodes.add(item)
    queue = [(item, [item], weight[process_game_map_copy[item[0]][item[1]]])]
    while queue:

        queue = sorted(queue, key = lambda x: x[2])             # uniform cost search
        vertex, path, cost = queue.pop(0)
        
        weight_copy = deepcopy(weight)
        water_land = 0
        land_water = 0
        mark = 0
        if len(path) >= 2:
            for p in range(len(path) - 1):
                if mark == 0 and process_game_map_copy[path[p][0]][path[p][1]] == ' ':
                    weight_copy[' '] = 5
    
                if process_game_map_copy[path[p][0]][path[p][1]] == '~' and process_game_map_copy[path[p + 1][0]][path[p + 1][1]] != '~':
                    water_land = p          # water value
                    if process_game_map_copy[path[p + 1][0]][path[p + 1][1]] != 'T':
                        weight_copy['T'] = -1000
                        mark = 1
                    else:
                        weight_copy[' '] = -1000
                        mark = 2

                if mark == 1 and process_game_map_copy[path[p][0]][path[p][1]] == 'T':
                    weight_copy['T'] = 15
                    weight_copy[' '] = -1000
                    mark = 2

                if mark == 2 and process_game_map_copy[path[p][0]][path[p][1]] == ' ':
                    weight_copy[' '] = 5
                    mark = 3
 
        next_vertices = [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list \
                if 0 <= vertex[0] + a[0] <= len(process_game_map_copy) - 1 and 0 <=  vertex[1] + a[1] <= len(process_game_map_copy[0]) - 1]

        next_vertices = [a for a in next_vertices if process_game_map_copy[a[0]][a[1]] in weight_copy]
        next_vertices = sorted(next_vertices, key = lambda x: weight_copy[process_game_map_copy[x[0]][x[1]]])

        if next_vertices:
            for next_vertex in next_vertices:
                if next_vertex in set(next_vertices) - set(path) - all_path_nodes:
                    next_char = process_game_map_copy[next_vertex[0]][next_vertex[1]]

                    if next_vertex in water_edge_list:
                        full_path = path + [next_vertex]

                        tree_in = 0
                        if mark > 0:
                            for p in range(len(full_path) - 1, 0, -1):
                                if process_game_map_copy[full_path[p - 1][0]][full_path[p - 1][1]] != '~' and process_game_map_copy[full_path[p][0]][full_path[p][1]] == '~':
                                    land_water = p - 1
                                    break
                            for m in full_path[water_land: land_water]:
                                if process_game_map_copy[m[0]][m[1]] == 'T':
                                    tree_in = 1
                                    break
                                                
                        if mark == 0 or (mark > 0 and tree_in == 1):
                            for i in range(len(full_path) - 1):
                                if process_game_map_copy[full_path[i][0]][full_path[i][1]] != '~' and process_game_map_copy[full_path[i + 1][0]][full_path[i + 1][1]] == '~':
                                    if cost + weight_copy[next_char] < (process_tools_copy['d'] + 1) * 10000 - 2000:
                                        return full_path[i:][::-1]
                    else:
                        queue.append((next_vertex, path + [next_vertex], cost + weight_copy[next_char]))
                        all_path_nodes.add(next_vertex)
                    
# weight calculation #

def weight_cal(n, item_weight_surrounding, d_para, process_game_map_copy):      # edge_node; item_weight_surrounding: list of (r, c, weight, surrounding)
    value = 0                                                                   # need optimisation when interval is tree or ' ' or water
    for i in item_weight_surrounding:
        distance = min([abs(n[0] - s[0]) + abs(n[1] - s[1]) for s in i[3]]) + 1
        if distance <= d_para:
            value += ((d_para + 1) - distance) * i[2]
    return value

def obstacle_surrounding(item, process_game_map_copy, process_tools_copy, nr, nc):             # item: (r, c, weight)
    item = (item[0], item[1])
    all_known_nodes = set()
    all_known_nodes.add(item)
    surrounding = []
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    priority = ['*', ' ', 'd', '$', 'a', 'k']
    if process_tools_copy['a'] > 0:
        priority.append('T')
    if process_tools_copy['k'] > 0:
        priority.append('-')
    queue = [(item, [item])]
    while queue:
        vertex, path = queue.pop(0)
        next_vertices = [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list if 0 <= vertex[0] + a[0] < nr and 0 <= vertex[1] + a[1] < nc]
        next_vertices = [a for a in next_vertices if process_game_map_copy[a[0]][a[1]] in priority]
        for next_vertex in set(next_vertices) - set(path) - all_known_nodes:
            char = process_game_map_copy[next_vertex[0]][next_vertex[1]]
            if char == '*':
                surrounding.append(next_vertex)
            else:
                queue.append((next_vertex, path + [next_vertex]))
                all_known_nodes.add(next_vertex)
    return surrounding


############### water cruise ###############

def water_cruise(current_node, current_direction):
    next_node = set_off_point(current_node)
    if not next_node:
        return current_node, current_direction

    path = []
    if next_node:
        path = path_node_to_node(current_node, next_node)
        end_node, end_direction = path_move(path, current_direction)        # to the water

    while path:
        path = cruise_get_path(end_node)
        if path:
            end_node, end_direction = path_move(path, end_direction)
    return end_node, end_direction



def cruise_get_path(node):         # bfs to get next node and the path
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    all_path = set()
    all_path.add(node)
    queue = [(node, [node])]
    while queue:
        vertex, path = queue.pop(0)
        for next_vertex in [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list]:
            if next_vertex not in set(path) | all_path and game_map[next_vertex[0]][next_vertex[1]] == '~':
                if cruise_unknow_check(next_vertex):
                    return path + [next_vertex]
                else:
                    queue.append((next_vertex, path + [next_vertex]))
                    all_path.add(next_vertex)


def cruise_unknow_check(vertex):                   
    for i in range(-2, 3, 1):
        for j in range(-2, 3, 1):
            if game_map[vertex[0] + i][vertex[1] + j] == '?':
                return True


def set_off_point(current_node):
    pending_water = item_not_get['~']
    confirm_water = set()
    aiming_water = []
    aiming_qty = 1
    for w in pending_water:
        if w not in confirm_water:
            w_qty, w_confirm_water = surrounding_question_qty(w)
            if w_qty is not None and w_confirm_water is not None:
                confirm_water = confirm_water | w_confirm_water
                if w_qty > aiming_qty:
                    aiming_water = list(w_confirm_water)
                    aiming_qty = w_qty
                elif w_qty == aiming_qty:
                    aiming_water.extend(list(w_confirm_water))
    if aiming_water:
        temp_list = sorted([(a, abs(current_node[0] - a[0]) + abs(current_node[1] - a[1])) for a in aiming_water], key = lambda x: x[1])
        return temp_list[0][0]


def surrounding_question_qty(node):             # return types: int, set of nodes
    if game_map[node[0]][node[1]] != '~':
        return 0, []
    available_mark = 0
    surrounding_question_list = []
    direction_list = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    all_path = set()
    all_path.add(node)
    queue = [(node, [node])]
    while queue:
        vertex, path = queue.pop(0)
        next_vertices = [(vertex[0] + a[0], vertex[1] + a[1]) for a in direction_list if 0 <= vertex[0] + a[0] < 160 and 0 <= vertex[1] + a[1] < 160]
        for next_vertex in set(next_vertices) - set(path) - all_path:
            char = game_map[next_vertex[0]][next_vertex[1]]
            if char == '?':
                surrounding_question_list.append(next_vertex)
            elif char == ' ':
                return len(surrounding_question_list), all_path
            elif char == '~':
                queue.append((next_vertex, path + [next_vertex]))
                all_path.add(next_vertex)
    return None, None






############### main function ###############

# initial #
s = init_socket()
game_map = []
for i in range(159):
    game_map_cell = []
    for j in range(159):
        game_map_cell.append('?')
    game_map.append(game_map_cell)

init_node = (80, 80)                            # row, column
init_map(init_node)
init_direction = 0                              # init direction '^',direction = {'^': 0, '>': 1, 'v': 2, '<': 3}
visited = set()
visited.add(tuple(init_node))                   # visited nodes
tools = {'a': 0, 'k': 0, 'd': 0, '$': 0, 'r': 0}        # tools got, self-define char for raft
item_not_get = {'a': [], 'k': [], 'd': [], '$': [], '-': [], 'T': [], '~': []}       # items not get but in sight

# first map discovery

end_node, end_direction = auto_agent(init_node, init_direction)
#input("start eliminate 'T' with '?'")
end_node, end_direction = auto_agent(end_node, end_direction, 2)       # eliminate 'T' with ? in sight

item_not_get_check()

#print('&' * 80)

cruise_end_node = None
mark_for_cruising = 0

while True:

    #print('phase 1: back to start node with $... ' * 2)


    if tools['$'] != 0 and game_map[end_node[0]][end_node[1]] != '~':                                         # already get '$' at first map discovery
        path = path_node_to_node(end_node, init_node)
        if path:
            end_node, end_direction = path_move(path, end_direction)
            

    #print('phase 2: find paths to $ and back to start node with ' * 2)


    item_not_get_check()
    if len(item_not_get['$']) >= 1 and tools['$'] == 0:         # '$' not get but in sight, find the route to '$'
        target_node = item_not_get['$'][0]
        wall_connect_nodes = wall_connect('T', '-', 'a', 'k', 'd', '$')
        target_scatter_path = target_plan(end_node, target_node, init_node, wall_connect_nodes)     # including back to init_node 

        if target_scatter_path:
            for i in range(len(target_scatter_path) - 1):
                path = path_node_to_node(end_node, target_scatter_path[i + 1])
                end_node, end_direction = path_move(path, end_direction)

    if tools['$'] > 0:
        target_node = init_node
        wall_connect_nodes = wall_connect('T', '-', 'a', 'k', 'd', '$')
        target_scatter_path = target_plan(end_node, target_node, init_node, wall_connect_nodes)     # including back to init_node 

        if target_scatter_path:
            for i in range(len(target_scatter_path) - 1):
                path = path_node_to_node(end_node, target_scatter_path[i + 1])
                end_node, end_direction = path_move(path, end_direction)


    #print('phase 3: cruising to discover map' * 2)


    mark_for_cruising = 0
    item_not_get_check()
    if  tools['$'] == 0 and mark_for_cruising == 0:                # need update for various situation
        mark_for_cruising = 1
        if tools['r'] > 0 and len(item_not_get['~']) > 0:
            end_node, end_direction = water_cruise(end_node, end_direction)
            end_node, end_direction = auto_agent(end_node, end_direction)


    #print('phase 2 again after 3: find paths to $ and back to start node with ' * 2)


    item_not_get_check()
    if len(item_not_get['$']) >= 1 and tools['$'] == 0:         # '$' not get but in sight, find the route to '$'
        target_node = item_not_get['$'][0]
        wall_connect_nodes = wall_connect('T', '-', 'a', 'k', 'd', '$')
        target_scatter_path = target_plan(end_node, target_node, init_node, wall_connect_nodes)     # including back to init_node
    
        if target_scatter_path:
            for i in range(len(target_scatter_path) - 1):
                path = path_node_to_node(end_node, target_scatter_path[i + 1])
                end_node, end_direction = path_move(path, end_direction)


    if tools['$'] > 0:
        target_node = init_node
        wall_connect_nodes = wall_connect('T', '-', 'a', 'k', 'd', '$')
        target_scatter_path = target_plan(end_node, target_node, init_node, wall_connect_nodes)     # including back to init_node
    
        if target_scatter_path:
            for i in range(len(target_scatter_path) - 1):
                path = path_node_to_node(end_node, target_scatter_path[i + 1])
                end_node, end_direction = path_move(path, end_direction)


    #print('phase 4: auto agent with raft... ' * 2)

    if mark_for_cruising == 1:
        end_node, end_direction = auto_agent(end_node, end_direction, 1)    # cruising with raft
        end_node, end_direction = auto_agent(end_node, end_direction, 2)    # eliminate 'T' with '?'s around


    #input('round ends')

    
    if tools['$'] != 0 and end_node == init_node:
        break
    
t2 = time.time()
print('\n')
print('time lapse:', t2 - t1)
print('\n')























