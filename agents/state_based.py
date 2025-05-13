from random import choice
from mesa import Agent
from environment.resource import ResourceType


def log(a, m):
    print(f"[StateBased {a.unique_id:02}] {m}")


class StateBasedAgent(Agent):
    """
    • Explora evitando revisitas frequentes.
    • Coopera 2‑a‑2 (ou sozinho) para STRUCTURE.
    • Aceita tasks individuais do BDI.
    """

    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.memory: set[tuple[int, int]] = set()
        self.visit: dict[tuple[int, int], int] = {}
        self.carrying: ResourceType | None = None
        self.waiting_for_help: bool = False
        self.current_task: dict | None = None
        self.delivered = {rt: 0 for rt in ResourceType}

    # ------------------------------------------------------------ #
    # 1 passo                                                      #
    # ------------------------------------------------------------ #
    def step(self) -> None:
        # memoriza posição
        self.memory.add(self.pos)
        self.visit[self.pos] = self.visit.get(self.pos, 0) + 1

        self._receive()  # mensagens do BDI

        # ---------- carregando algo ------------------------------- #
        if self.carrying:
            self._move(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"🚚 entregou {self.carrying.name} | total={self.delivered}")
                self.carrying = None
                self.current_task = None
            return

        # ---------- aguardando parceiro --------------------------- #
        if self.waiting_for_help:
            self._check()
            return

        # ---------- task ativa ------------------------------------ #
        if self.current_task:
            tgt = self.current_task["position"]
            self.memory.add(tgt)
            self._move_towards(tgt)

            #  chegou ao destino → tenta coletar
            if self.pos == tgt:
                before = self.carrying
                self._look()  # varre e coleta
                if self.carrying is None and not self.waiting_for_help:
                    log(self, f"⚠️ tarefa inválida em {tgt}")
                    self.current_task = None
            return

        # ---------- comportamento padrão -------------------------- #
        self._look()
        self._explore()

    # ------------------------------------------------------------ #
    # comunicação                                                  #
    # ------------------------------------------------------------ #
    def _receive(self) -> None:
        """Recebe tasks quando não está ocupado."""
        if self.carrying or self.waiting_for_help:
            return
        if self.current_task and self.pos != tuple(self.current_task["position"]):
            return

        for msg in self.model.message_bus.receive(str(self.unique_id)):
            if msg.get("type") == "task" and msg.get("action") == "collect":
                self.current_task = {
                    "position": tuple(msg["position"]),
                    "resource_type": msg["resource_type"],
                }
                log(self, f"📥 task {msg['resource_type']} em {msg['position']}")

    # ------------------------------------------------------------ #
    # crenças                                                      #
    # ------------------------------------------------------------ #
    def _belief(self, p, r) -> None:
        self.model.report_resource(p, r)
        self.model.message_bus.send(
            "BDI",
            {"type": "belief", "data": {"position": p, "resource_type": r.name}},
        )

    # ------------------------------------------------------------ #
    # cooperação                                                   #
    # ------------------------------------------------------------ #
    def _check(self) -> None:
        """Verifica se há parceiro; coleta STRUCTURE sozinho ou em dupla."""
        cell = self.model.grid.get_cell_list_contents([self.pos])

        # estrutura desapareceu?
        if not any(
            getattr(o, "resource_type", None) == ResourceType.STRUCTURE for o in cell
        ):
            self.waiting_for_help = False
            log(self, "⚠️ STRUCTURE sumiu")
            return

        partners = [
            a
            for a in cell
            if isinstance(a, StateBasedAgent)
            and a.waiting_for_help
            and a.unique_id != self.unique_id
        ]

        # remove o recurso
        for obj in cell:
            if getattr(obj, "resource_type", None) == ResourceType.STRUCTURE:
                self.model.grid.remove_agent(obj)
                break

        self.carrying = ResourceType.STRUCTURE
        self.waiting_for_help = False
        for p in partners:
            p.carrying = ResourceType.STRUCTURE
            p.waiting_for_help = False

        if partners:
            log(self, f"🤝 coletou STRUCTURE com {[p.unique_id for p in partners]}")
        else:
            log(self, "🏗 coletou STRUCTURE sozinho")

    # ------------------------------------------------------------ #
    # exploração                                                   #
    # ------------------------------------------------------------ #
    def _explore(self) -> None:
        nbrs = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        unseen = [p for p in nbrs if p not in self.memory]
        if unseen:
            tgt = choice(unseen)
        else:
            m = min(self.visit.get(p, 0) for p in nbrs)
            tgt = choice([p for p in nbrs if self.visit.get(p, 0) == m])

        self.model.safe_move(self, tgt)
        log(self, f"🧭 explorou → {tgt} • visitas={self.visit.get(tgt,0)}")

    # ------------------------------------------------------------ #
    # navegação                                                    #
    # ------------------------------------------------------------ #
    def _move_towards(self, dest: tuple[int, int]) -> None:
        x, y = self.pos
        dx, dy = dest
        if x < dx:
            x += 1
        elif x > dx:
            x -= 1
        elif y < dy:
            y += 1
        elif y > dy:
            y -= 1
        self.model.safe_move(self, (x, y))
        log(self, f"➡️ passo → {(x, y)} (dest={dest})")

    # Alias para manter compatibilidade com a chamada existente
    _move = _move_towards

    # ------------------------------------------------------------ #
    # percepção / coleta                                           #
    # ------------------------------------------------------------ #
    def _look(self) -> None:
        """Analisa célula atual + vizinhos; coleta ou define novas metas."""
        nb = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=True
        )
        for p in nb:
            for obj in self.model.grid.get_cell_list_contents([p]):
                if not hasattr(obj, "resource_type"):
                    continue
                rt = obj.resource_type
                self._belief(p, rt)

                # --- célula onde estou -----------------------------
                if p == self.pos:
                    if rt in (ResourceType.CRYSTAL, ResourceType.METAL):
                        self.model.grid.remove_agent(obj)
                        self.carrying = rt
                        log(self, f"💎 pegou {rt.name}")
                        self.current_task = None
                        return
                    if rt == ResourceType.STRUCTURE:
                        self.waiting_for_help = True
                        log(self, "🏗 chegou na STRUCTURE • WAIT")
                        return

                # --- célula vizinha --------------------------------
                else:
                    if (
                        rt in (ResourceType.CRYSTAL, ResourceType.METAL)
                        and self.carrying is None
                        and self.current_task is None
                    ):
                        self.current_task = {"position": p, "resource_type": rt.name}
                        log(self, f"🎯 alvo em {p}")
                        return
