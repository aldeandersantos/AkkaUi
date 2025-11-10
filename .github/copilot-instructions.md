# Instruções para GitHub Copilot - Python
## Idioma
- Responda sempre em português brasileiro
- Use terminologia técnica em português quando possível

## Estilo de Código
- Siga os princípios de Clean Code
- Use nomes descritivos para variáveis, funções e classes
- Prefira funções pequenas e com responsabilidade única
- Evite aninhamento excessivo (máximo 2-3 níveis)
- Evite criar comentários longoes ou óbvios	
- Sempre veja se o código pode ser reutilizado antes de criar algo novo

## Comentários
- NÃO criar comentários longos ou óbvios, sempre que crialos, com # ao invés de '''comentario '''
- Comentários apenas quando necessário para explicar "por que", não "o que"
- Prefira código autoexplicativo
- Use docstrings concisas apenas para funções/classes públicas

## Resposta às Perguntas
- Responda de forma clara e objetiva
- Evite textos muito longos e de longa leitura

## Estrutura
- Organize código em camadas (domain, application, infrastructure)
- Separe responsabilidades claramente
- Use injeção de dependência quando apropriado
- Prefira composição sobre herança
- Use f-strings para formatação de strings
- Use classes para encapsular apenas quando realmente necessário, prefira funções simples
- Evite código duplicado, extraia funções
- NUNCA crie arquivos a mais além dos que forem solicitados
- Sempre escreva códigos simples e diretos, evitando complexidade

## Tratamento de Erros
- Use bloco try/except para operações assincronas ou sempre que for conveniente, mas não use sempre para tudo
- Sempre registre erros com informações contextuais
- Não precisa testar o código, apenas escreva o código e responda as perguntas do usuário

## Execução e Testes
- Sempre utilize o ambiente virtual (venv) ao executar ou testar código no console
- Powershell não aceita &&, tem que ser ;
- Não é necessário rodar o código automaticamente ao finalizar a entrega, apenas forneça o código solicitado
- Sempre use cmd no terminal ao invés de powershell

## Convenções Python
- Siga PEP 8
- Use type hints
- Prefira list/dict comprehensions quando apropriado
- Use context managers para recursos

## Debugging