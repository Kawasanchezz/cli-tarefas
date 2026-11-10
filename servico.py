"""Regras de negócio: operações sobre o estado de tarefas (sem I/O)."""

from datetime import datetime

PRIORIDADES = ("baixa", "media", "alta")
STATUS = ("pendente", "concluida")
_ORDEM_PRIORIDADE = {"alta": 0, "media": 1, "baixa": 2}


class ErroTarefa(Exception):
    """Erro de validação ou de regra de negócio."""


def validar_descricao(descricao: str) -> str:
    descricao = (descricao or "").strip()
    if not descricao:
        raise ErroTarefa("A descrição não pode ser vazia.")
    return descricao


def validar_data(texto: str) -> str:
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date().isoformat()
    except (ValueError, TypeError):
        raise ErroTarefa(
            f"Data inválida: '{texto}'. Use o formato AAAA-MM-DD (ex.: 2026-12-31)."
        ) from None


def _buscar(estado: dict, id_: int) -> dict:
    for tarefa in estado["tarefas"]:
        if tarefa["id"] == id_:
            return tarefa
    raise ErroTarefa(f"Tarefa #{id_} não encontrada.")


def adicionar(estado: dict, descricao: str, prioridade: str = "media",
              data_limite: str | None = None) -> dict:
    tarefa = {
        "id": estado["proximo_id"],
        "descricao": validar_descricao(descricao),
        "status": "pendente",
        "prioridade": prioridade,
        "criada_em": datetime.now().isoformat(timespec="seconds"),
        "data_limite": validar_data(data_limite) if data_limite else None,
    }
    estado["proximo_id"] += 1
    estado["tarefas"].append(tarefa)
    return tarefa


def listar(estado: dict, status: str | None = None,
           prioridade: str | None = None) -> list[dict]:
    """Pendentes primeiro; depois prioridade, data limite (sem data por último) e id."""
    tarefas = [
        t for t in estado["tarefas"]
        if (status is None or t["status"] == status)
        and (prioridade is None or t["prioridade"] == prioridade)
    ]
    return sorted(
        tarefas,
        key=lambda t: (
            t["status"] != "pendente",
            _ORDEM_PRIORIDADE.get(t["prioridade"], 9),
            t["data_limite"] is None,
            t["data_limite"] or "",
            t["id"],
        ),
    )


def concluir(estado: dict, id_: int) -> dict:
    tarefa = _buscar(estado, id_)
    if tarefa["status"] == "concluida":
        raise ErroTarefa(f"A tarefa #{id_} já está concluída.")
    tarefa["status"] = "concluida"
    return tarefa


def remover(estado: dict, id_: int) -> dict:
    tarefa = _buscar(estado, id_)
    estado["tarefas"].remove(tarefa)
    return tarefa


def editar(estado: dict, id_: int, descricao: str | None = None,
           prioridade: str | None = None, data_limite: str | None = None,
           remover_data: bool = False) -> dict:
    if descricao is None and prioridade is None and data_limite is None and not remover_data:
        raise ErroTarefa(
            "Nada para editar. Use --descricao, --prioridade, --data-limite ou --sem-data."
        )
    tarefa = _buscar(estado, id_)
    # Valida tudo antes de alterar, para não deixar edição pela metade.
    nova_desc = validar_descricao(descricao) if descricao is not None else None
    nova_data = validar_data(data_limite) if data_limite is not None else None
    if nova_desc is not None:
        tarefa["descricao"] = nova_desc
    if prioridade is not None:
        tarefa["prioridade"] = prioridade
    if nova_data is not None:
        tarefa["data_limite"] = nova_data
    elif remover_data:
        tarefa["data_limite"] = None
    return tarefa
