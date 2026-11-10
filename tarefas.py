#!/usr/bin/env python3
"""CLI de tarefas: adicionar, listar, concluir, editar e remover pelo terminal."""

import argparse
import sys

import servico
import storage

EXEMPLOS = {
    "add": 'python tarefas.py add "Estudar Python" --prioridade alta --data-limite 2026-12-31',
    "list": "python tarefas.py list --status pendente --prioridade alta",
    "done": "python tarefas.py done 1",
    "remove": "python tarefas.py remove 1",
    "edit": 'python tarefas.py edit 1 --descricao "Revisar Python" --prioridade baixa',
}


def construir_parser() -> argparse.ArgumentParser:
    fmt = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        prog="tarefas.py",
        description="Gerenciador de tarefas no terminal (dados em tasks.json).",
        epilog="Use 'tarefas.py <comando> --help' para ver detalhes e exemplos.",
        formatter_class=fmt,
    )
    sub = parser.add_subparsers(dest="comando", metavar="<comando>", required=True)

    def novo(nome, ajuda):
        return sub.add_parser(nome, help=ajuda, description=ajuda,
                              epilog=f"Exemplo:\n  {EXEMPLOS[nome]}", formatter_class=fmt)

    p = novo("add", "Adiciona uma tarefa.")
    p.add_argument("descricao", help="texto da tarefa")
    p.add_argument("-p", "--prioridade", choices=servico.PRIORIDADES, default="media",
                   help="prioridade (padrão: media)")
    p.add_argument("-d", "--data-limite", metavar="AAAA-MM-DD", help="data limite")

    p = novo("list", "Lista as tarefas.")
    p.add_argument("-s", "--status", choices=servico.STATUS, help="filtra por status")
    p.add_argument("-p", "--prioridade", choices=servico.PRIORIDADES,
                   help="filtra por prioridade")

    p = novo("done", "Marca uma tarefa como concluída.")
    p.add_argument("id", type=int, help="id da tarefa")

    p = novo("remove", "Remove uma tarefa.")
    p.add_argument("id", type=int, help="id da tarefa")

    p = novo("edit", "Edita descrição, prioridade ou data limite.")
    p.add_argument("id", type=int, help="id da tarefa")
    p.add_argument("--descricao", help="nova descrição")
    p.add_argument("-p", "--prioridade", choices=servico.PRIORIDADES, help="nova prioridade")
    p.add_argument("-d", "--data-limite", metavar="AAAA-MM-DD", help="nova data limite")
    p.add_argument("--sem-data", action="store_true", help="remove a data limite")
    return parser


def _seguro(texto: str) -> str:
    """Troca caracteres de controle (ex.: sequências ANSI) por '?' antes de imprimir."""
    return "".join(c if c.isprintable() else "?" for c in texto)


def formatar_tabela(tarefas: list[dict]) -> str:
    cabecalho = ["ID", "STATUS", "PRIORIDADE", "LIMITE", "DESCRIÇÃO"]
    linhas = [
        [str(t["id"]), _seguro(t["status"]), _seguro(t["prioridade"]),
         _seguro(t["data_limite"] or "-"), _seguro(t["descricao"])]
        for t in tarefas
    ]
    larguras = [max(len(c[i]) for c in [cabecalho] + linhas) for i in range(4)]

    def linha(cols):
        return "  ".join(c.ljust(w) for c, w in zip(cols[:4], larguras)) + "  " + cols[4]

    return "\n".join([linha(cabecalho), "  ".join("-" * w for w in larguras) + "  " + "-" * 9]
                     + [linha(l) for l in linhas])


def executar(args, estado: dict) -> bool:
    """Executa o comando; devolve True se o estado foi alterado e deve ser salvo."""
    if args.comando == "add":
        t = servico.adicionar(estado, args.descricao, args.prioridade, args.data_limite)
        print(f"Tarefa #{t['id']} adicionada: {t['descricao']}")
        return True
    if args.comando == "list":
        tarefas = servico.listar(estado, args.status, args.prioridade)
        print(formatar_tabela(tarefas) if tarefas else "Nenhuma tarefa encontrada.")
        return False
    if args.comando == "done":
        t = servico.concluir(estado, args.id)
        print(f"Tarefa #{t['id']} concluída: {t['descricao']}")
        return True
    if args.comando == "remove":
        t = servico.remover(estado, args.id)
        print(f"Tarefa #{t['id']} removida: {t['descricao']}")
        return True
    t = servico.editar(estado, args.id, args.descricao, args.prioridade,
                       args.data_limite, args.sem_data)
    print(f"Tarefa #{t['id']} atualizada.")
    return True


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    args = construir_parser().parse_args(argv)
    caminho = storage.caminho_arquivo()
    try:
        estado = storage.carregar(caminho)
        if executar(args, estado):
            storage.salvar(caminho, estado)
    except (servico.ErroTarefa, storage.ErroStorage) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
