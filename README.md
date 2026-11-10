# CLI de Tarefas

Gerenciador de tarefas que roda 100% no terminal, sem interface gráfica. Os dados ficam em um arquivo JSON local (`tasks.json`). Sem dependências externas, só a biblioteca padrão do Python.

## Requisitos

- Python 3.10 ou superior (Windows, Linux ou macOS)

## Instalação

Não há o que instalar. Baixe a pasta e execute:

```
python tarefas.py --help
```

> No Windows, se `python` não funcionar, use `py tarefas.py ...`.

## Estrutura

```
├── tarefas.py        # ponto de entrada: parsing dos argumentos e saída no terminal
├── servico.py        # regras de negócio (validação, ordenação, operações)
├── storage.py        # leitura/escrita do JSON (gravação atômica)
├── tasks.json        # gerado automaticamente na primeira gravação
└── tests/            # testes automatizados
```

## Comandos

| Comando | O que faz | Exemplo |
|---|---|---|
| `add` | Adiciona uma tarefa | `python tarefas.py add "Estudar Python" -p alta -d 2026-12-31` |
| `list` | Lista as tarefas (filtros `--status`, `--prioridade`) | `python tarefas.py list --status pendente` |
| `done <id>` | Marca como concluída | `python tarefas.py done 1` |
| `edit <id>` | Edita descrição, prioridade ou data | `python tarefas.py edit 1 --descricao "Novo texto"` |
| `remove <id>` | Remove a tarefa | `python tarefas.py remove 1` |

Todos aceitam `--help`.

**Opções**

- Prioridade: `baixa`, `media` (padrão) ou `alta` (`-p`/`--prioridade`).
- Data limite: `AAAA-MM-DD` (`-d`/`--data-limite`). No `edit`, `--sem-data` remove a data.
- Status (filtro do `list`): `pendente` ou `concluida`.

**Ordenação do `list`:** pendentes primeiro, depois prioridade (alta → baixa), data limite mais próxima e id.

## Exemplo de sessão

```
$ python tarefas.py add "Estudar Python" --prioridade alta --data-limite 2026-12-31
Tarefa #1 adicionada: Estudar Python
$ python tarefas.py add "Comprar pão"
Tarefa #2 adicionada: Comprar pão
$ python tarefas.py add "Ler um livro" -p baixa
Tarefa #3 adicionada: Ler um livro
$ python tarefas.py done 2
Tarefa #2 concluída: Comprar pão
$ python tarefas.py list
ID  STATUS     PRIORIDADE  LIMITE      DESCRIÇÃO
--  ---------  ----------  ----------  ---------
1   pendente   alta        2026-12-31  Estudar Python
3   pendente   baixa       -           Ler um livro
2   concluida  media       -           Comprar pão
$ python tarefas.py edit 3 --descricao "Ler 20 páginas"
Tarefa #3 atualizada.
$ python tarefas.py remove 2
Tarefa #2 removida: Comprar pão
$ python tarefas.py done 99
Erro: Tarefa #99 não encontrada.
```

Em caso de erro previsto, a mensagem vai para o stderr e o código de saída é `1` (argumentos inválidos retornam `2`).

## Formato do JSON

```json
{
  "proximo_id": 4,
  "tarefas": [
    {
      "id": 1,
      "descricao": "Estudar Python",
      "status": "pendente",
      "prioridade": "alta",
      "criada_em": "2026-11-09T21:30:00",
      "data_limite": "2026-12-31"
    }
  ]
}
```

`proximo_id` garante que ids de tarefas removidas não sejam reaproveitados.

## Onde fica o arquivo

Por padrão, `tasks.json` fica na mesma pasta do `tarefas.py`. Para usar outro local, defina a variável `TAREFAS_FILE`:

```
# Linux/macOS
TAREFAS_FILE=~/minhas-tarefas.json python tarefas.py list
# PowerShell
$env:TAREFAS_FILE = "$HOME\minhas-tarefas.json"; python tarefas.py list
```

## Testes

```
python -m unittest discover -s tests -v
```

## Solução de problemas

| Problema | Solução |
|---|---|
| `O arquivo '...' está corrompido` | O JSON foi editado de forma inválida. Corrija-o ou apague o arquivo para recomeçar. A CLI nunca sobrescreve um arquivo corrompido. |
| `Data inválida` | Use `AAAA-MM-DD`, por exemplo `2026-12-31`. |
| `Tarefa #N não encontrada` | Veja os ids válidos com `python tarefas.py list`. |
| `python` não é reconhecido (Windows) | Use `py tarefas.py ...` ou instale o Python em python.org. |
| Acentos aparecem errados | A CLI já usa UTF-8; configure o terminal para UTF-8 (`chcp 65001` no cmd). |

## Melhorias futuras

1. Tags/categorias e busca por texto (`search`).
2. Exportação para CSV/Markdown.
3. Destaque de tarefas atrasadas e comando `list --atrasadas`.
