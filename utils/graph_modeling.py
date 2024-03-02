import pygame

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def main(pos, edges):
    pygame.init()

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    WIDTH, HEIGHT = 800, 600

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Grafo interattivo')

    edges_new = []
    for edge in edges:
        edges_new.append(list(edge[0]))

    nodes = []
    for i in pos:
        nodes.append(Node(pos[i][0], pos[i][1]))

    running = True
    dragging = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Tasto sinistro del mouse
                    for node in nodes:
                        if pygame.Rect(node.x-10, node.y-10, 20, 20).collidepoint(event.pos):
                            dragging = True
                            node.x, node.y = event.pos
                elif event.button == 3:  # Tasto destro del mouse
                    for edge in edges_new:
                        pygame.draw.line(screen, BLACK, (nodes[edge[0]].x, nodes[edge[0]].y), (nodes[edge[1]].x, nodes[edge[1]].y))
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    for node in nodes:
                        if pygame.Rect(node.x-10, node.y-10, 20, 20).collidepoint(event.pos):
                            node.x, node.y = event.pos
        screen.fill(WHITE)
        for node in nodes:
            pygame.draw.circle(screen, BLACK, (node.x, node.y), 10)
        for edge in edges_new:
            pygame.draw.line(screen, BLACK, (nodes[edge[0]].x, nodes[edge[0]].y), (nodes[edge[1]].x, nodes[edge[1]].y))
        pygame.display.flip()

    pos_new = {}
    for i in pos:
        pos_new[i] = (nodes[i].x, nodes[i].y)

    pygame.quit()
    return pos_new
