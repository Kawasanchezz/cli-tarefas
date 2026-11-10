# Política de segurança

## Versões suportadas

Projeto acadêmico em versão única. Apenas o código da branch principal recebe correções.

## Como reportar uma vulnerabilidade

Não abra uma issue pública. Use o **relato privado de vulnerabilidades do GitHub**
(aba *Security* → *Report a vulnerability* do repositório). Inclua os passos para reproduzir,
a versão do Python e o sistema operacional.

Por ser um projeto acadêmico mantido sem equipe dedicada, a resposta é feita por melhor esforço;
a meta é confirmar o recebimento em alguns dias e corrigir problemas confirmados antes de divulgá-los.

## Modelo de ameaça

A CLI roda localmente, sem rede, sem contas e sem serviços externos. O arquivo `tasks.json`
e a variável de ambiente `TAREFAS_FILE` são considerados entradas do próprio usuário.
O principal risco tratado é um `tasks.json` adulterado ou corrompido.

## Proteções implementadas

- Validação do formato do JSON (tipos, ids únicos, `proximo_id` consistente); arquivos inválidos
  geram erro claro e nunca são sobrescritos.
- Caracteres de controle (ex.: sequências ANSI) são neutralizados na saída do `list`.
- Gravação atômica (arquivo temporário + renomeação).
- Sem `eval`, `exec`, `subprocess`, deserialização insegura ou dependências externas.
- `tasks.json` e artefatos de ferramentas de IA estão no `.gitignore`.

## Limitações conhecidas

- **Sem controle de concorrência:** duas execuções simultâneas podem sobrescrever as alterações uma da outra.
- **Dados em texto puro:** `tasks.json` não é criptografado e herda as permissões da pasta.
- Não há proteção contra um usuário com acesso de escrita à pasta do projeto.

Este projeto não é garantido como "completamente seguro"; revisões e relatos são bem-vindos.
