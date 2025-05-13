from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[Coop {agent.unique_id}] {msg}")


class CooperativeAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None                              
        self.waiting_for_help = False                     
        self.known_structures: set[tuple[int,int]] = set()
        self.target = None                               
        self.delivered = {rt: 0 for rt in ResourceType}   

    def step(self):
        #Entrega se estiver carregando
        if self.carrying:
            self.move_towards(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"entregou STRUCTURE na base")
                self.carrying = None
            return

        # Se aguardando parceiro, tenta coletar
        if self.waiting_for_help:
            self.check_for_partner()
            return

        # Atualiza lista de estruturas no grid
        self.scan_for_structures()

        # Vai ajudar na estrutura mais útil
        if self.known_structures:
            best = self.choose_best_structure()
            if best:
                self.target = best
                log(self, f"ajudando em {best}")
                self.move_towards(best)
                if self.pos == best:
                    self.check_for_partner()
                return

        self.random_move()

    def scan_for_structures(self):
        # percorre todo o grid para localizar STRUCTURE
        self.known_structures.clear()
        for x in range(self.model.grid.width):
            for y in range(self.model.grid.height):
                cell = self.model.grid.get_cell_list_contents([(x, y)])
                if any(getattr(obj, "resource_type", None) == ResourceType.STRUCTURE for obj in cell):
                    self.known_structures.add((x, y))

    def choose_best_structure(self):
        # calcula utilidade = value/(dist+1)*(1+parceiros)
        best_pos, best_u = None, -1
        for pos in self.known_structures:
            d = abs(self.pos[0]-pos[0]) + abs(self.pos[1]-pos[1])
            waiting = sum(1 for a in self.model.grid.get_cell_list_contents([pos])
                          if getattr(a, "waiting_for_help", False))
            u = (1/(d+1))*(1+waiting)*ResourceType.STRUCTURE.value
            if u > best_u:
                best_pos, best_u = pos, u
        return best_pos

    def check_for_partner(self):
        cell = self.model.grid.get_cell_list_contents([self.pos])
        # remove STRUCTURE e marca parceria
        for obj in cell:
            if getattr(obj, "resource_type", None) == ResourceType.STRUCTURE:
                self.model.grid.remove_agent(obj)
                self.carrying = ResourceType.STRUCTURE
                for a in cell:
                    if getattr(a, "waiting_for_help", False):
                        a.carrying = ResourceType.STRUCTURE
                        a.waiting_for_help = False
                self.waiting_for_help = False
                log(self, "coleta concluída em parceria")
                return
        # sinaliza espera se achar STRUCTURE mas sem parceiro
        self.waiting_for_help = True
        log(self, "aguardando parceiro")

    def move_towards(self, dst):
        # passo único em Manhattan
        x,y = self.pos; dx,dy = dst
        if x<dx: x+=1
        elif x>dx: x-=1
        elif y<dy: y+=1
        elif y>dy: y-=1
        self.model.safe_move(self, (x,y))

    def random_move(self):
        # escolhe movimento ortogonal 
        nbrs = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        if nbrs:
            p = choice(nbrs)
            self.model.safe_move(self, p)
            log(self, f"andou para {p}")
