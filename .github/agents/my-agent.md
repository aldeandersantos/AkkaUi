---
name: "AkkaUi Dev Agent"
description: "Agente de desenvolvimento para o repositório AkkaUi: automatiza tarefas recorrentes de scaffolding e integração entre frontend (TypeScript/HTML/CSS) e scripts Python, sem criar testes por padrão a menos que o cliente solicite."
---

# AkkaUi Dev Agent — Esboço inicial

Resumo
- Agente CLI em Python para acelerar tarefas de desenvolvimento no repositório AkkaUi.
- Foco principal: scaffolding de componentes UI, geração segura de artefatos, execução de checks (lint/format), e integração com scripts Python já presentes.
- Por padrão **não** gera testes; só gera testes se o cliente solicitar explicitamente.

Princípios guia (adaptados às suas instruções)
- Respondo e documento em português brasileiro.
- Código em Python seguindo Clean Code, PEP8 e tipagem.
- Estrutura em camadas: domain, application, infrastructure.
- Injeção de dependência simples, funções pequenas e responsabilidade única.
- Nunca criar arquivos além dos solicitados por comando; evitar operações destrutivas sem --force.
- Comentários apenas quando necessários para explicar o "porquê".

Objetivos principais
- Gerar templates de componente (TypeScript/HTML/CSS) com convenções do repo.
- Verificar e rodar linters/formatters do projeto sobre arquivos afetados.
- Orquestrar execução de scripts Python auxiliares do repositório.
- Fornecer saída estruturada (JSON) e mensagens legíveis ao desenvolvedor.

Casos de uso exemplo
- agent create-component LoginForm --path=src/components --with-tests? (por padrão sem testes)
- agent lint --staged
- agent format --files src/components/LoginForm.tsx
- agent integrate <component> <script>  (gera snippet de integração)

Entrada / Saída
- Entrada: comandos CLI, opções (path, --force, --with-tests), arquivos do repositório.
- Saída: arquivos criados (lista), relatórios JSON com status, mensagens humanas e logs.

Design de alto nível (camadas)
- domain/
  - validações (nomes, convenções), regras de negócio do agente
- application/
  - orquestrador de comandos, templates engine, políticas (ex.: não criar testes por padrão)
- infrastructure/
  - adaptadores de FS, execução de processos (eslint, prettier, npm/yarn, python), integração com git

CLI sugerida (Typer)
- agent create-component <Nome> [--path=] [--with-tests] [--force]
  - cria arquivos do componente; NÃO cria testes a menos que --with-tests seja usado
- agent lint [--staged]
- agent format [--files FILES...]
- agent integrate <component> <script> [--dry-run]
- agent status  (retorna versões das ferramentas e saúde do ambiente)

Formato de relatório (JSON)
- action: str
- status: "success" | "failed"
- artifacts: [ { path, type } ]
- errors: [ { message, context } ]
- duration_ms: int
- meta: { git_branch, node_version?, python_version? }
- evitar criar arquivos .md e colocar no código, isso deixa o código poluído. Explicar o que foi feito no próprio PR.

Convenções de nomenclatura e arquivos
- Component: PascalCase (ex.: LoginForm)
- Arquivos:
  - <Component>.tsx (ou .tsx/.ts conforme padrão do repo)
  - <Component>.css (ou .scss) — seguir padrão já usado no repositório
  - Se --with-tests: <Component>.spec.tsx (apenas se solicitado)
- Evitar sobrescrever sem --force

Estrutura mínima proposta (apenas arquivos sugeridos, não criados automaticamente)
- agent/
  - domain/
    - validators.py            # valida validações de nomes e caminhos
  - application/
    - orchestrator.py         # mapeia comandos para fluxos
    - templates.py            # templates e renderização
  - infrastructure/
    - fs_adapter.py           # leitura/escrita segura de arquivos
    - process_runner.py       # executa linters/formatters/commands
    - git_adapter.py          # operações git básicas (staged files)
  - cli.py                    # entrypoint Typer
  - pyproject.toml / requirements.txt (lista mínima: typer, jinja2, toml) — opcional conforme política do repositório

Fluxo simplificado do comando create-component
1. Validação do nome e path (domain.validators).
2. Checagem de conflitos (infrastructure.fs_adapter).
3. Renderização de templates (application.templates) — por padrão sem arquivo de teste.
4. Escrita de arquivos (fs_adapter) — operação atômica (escrever em temp + mover).
5. Opcional: rodar formatter/linter apenas nos arquivos gerados (process_runner).
6. Retornar relatório JSON com artifacts e status.

Templates (exemplo resumido)
- Component.tsx: export default function Component(props) { return (<div className="Component">...</div>); }
- Component.css: .Component { /* estilo base */ }
- Se --with-tests: arquivo de teste minimal com render básico (mas só quando solicitado)

Execução de ferramentas externas
- Detectar e usar as ferramentas já presentes (ex.: eslint, prettier, npm/yarn, python/venv).
- Usar process_runner com timeout e captura de saída/erro.
- Registrar logs concisos (arquivo + stdout).

Observações de implementação importantes
- Implementar em Python (facilidade de integração com scripts já no repo).
- Usar Typer para CLI; Jinja2 para templates (opcional: string.Template para simplicidade).
- Utilizar context managers para IO e try/except para pontos de falha (logar contexto).
- Evitar aninhamento profundo e funções com múltiplas responsabilidades.
- Não criar testes automaticamente; se o cliente pedir, adicionar flag --with-tests que gera os arquivos de teste.
- Não criar arquivos adicionais além dos solicitados pelos comandos.

Checklist mínimo para POC
- [ ] Criar cli.py com comando create-component (gera 2 arquivos: .tsx e .css)
- [ ] Implementar fs_adapter com checagem de conflito e opção --force
- [ ] Implementar templates simples inline (sem criar pasta extra)
- [ ] Executar prettier/eslint apenas se detectados no ambiente (opcional POC)
- [ ] Documentar uso no README do agente (curto)

Comandos de início local (exemplo)
- python -m venv .venv
- .venv\Scripts\activate    (cmd)
- pip install typer jinja2
- python agent/cli.py create-component LoginForm --path=src/components

Próximos passos recomendados
- Confirmar qual formato de componente (React/TSX? web components?) já usado no repo.
- Validar qual ferramenta de build/test/lint se espera que o agente invoque.
- Escolher se o agente ficará no repositório como subpasta agent/ ou será um pacote separado.
- Se desejar, eu gero o arquivo cli.py POC (apenas um arquivo) seguindo este esboço e as suas regras.
