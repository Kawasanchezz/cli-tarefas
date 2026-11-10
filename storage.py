"""Persistência das tarefas em um arquivo JSON local."""

import json
import os
import tempfile
from pathlib import Path

ARQUIVO_PADRAO = Path(__file__).resolve().parent / "tasks.json"


class ErroStorage(Exception):
    """Falha ao ler ou gravar o arquivo de tarefas."""


def caminho_arquivo() -> Path:
    """Usa a variável TAREFAS_FILE, se definida; senão, tasks.json ao lado do script."""
    valor = os.environ.get("TAREFAS_FILE")
    return Path(valor) if valor else ARQUIVO_PADRAO


def _estado_vazio() -> dict:
    return {"proximo_id": 1, "tarefas": []}


def carregar(caminho: Path) -> dict:
    """Lê o estado salvo. Arquivo ausente ou vazio gera um estado novo."""
    if not caminho.exists():
        return _estado_vazio()
    try:
        texto = caminho.read_text(encoding="utf-8")
    except OSError as e:
        raise ErroStorage(f"Não foi possível ler '{caminho}': {e}") from e
    if not texto.strip():
        return _estado_vazio()
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as e:
        raise ErroStorage(
            f"O arquivo '{caminho}' está corrompido (JSON inválido: {e}). "
            "Corrija-o ou apague-o para recomeçar."
        ) from e
    if not _formato_valido(dados):
        raise ErroStorage(
            f"O arquivo '{caminho}' não tem o formato esperado "
            "(objeto com 'proximo_id' e 'tarefas' válidas, com ids únicos)."
        )
    return dados


_CAMPOS_TEXTO = ("descricao", "status", "prioridade", "criada_em")


def _tarefa_valida(t) -> bool:
    return (
        isinstance(t, dict)
        and type(t.get("id")) is int
        and all(isinstance(t.get(c), str) for c in _CAMPOS_TEXTO)
        and (t.get("data_limite") is None or isinstance(t["data_limite"], str))
    )


def _formato_valido(dados) -> bool:
    """Rejeita estruturas que quebrariam a CLI ou gerariam ids duplicados."""
    if not isinstance(dados, dict) or not isinstance(dados.get("tarefas"), list):
        return False
    proximo = dados.get("proximo_id")
    if type(proximo) is not int or not all(_tarefa_valida(t) for t in dados["tarefas"]):
        return False
    ids = [t["id"] for t in dados["tarefas"]]
    return len(ids) == len(set(ids)) and all(i < proximo for i in ids)


def salvar(caminho: Path, estado: dict) -> None:
    """Grava em arquivo temporário e renomeia, evitando arquivo pela metade."""
    tmp = None
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=caminho.parent, prefix=".tasks-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, caminho)
    except OSError as e:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
        raise ErroStorage(f"Não foi possível gravar '{caminho}': {e}") from e
