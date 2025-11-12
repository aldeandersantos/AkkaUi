# Testes do Backend - AkkaUi

Este diretório contém testes abrangentes para o backend do AkkaUi usando pytest.

## Estrutura dos Testes

Os testes estão organizados no diretório `tests/` com subdiretorios por aplicação Django:

```
tests/
├── __init__.py
├── conftest.py          # Fixtures compartilhadas
├── core/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_services.py
│   └── test_serializers.py
├── usuario/
│   ├── test_models.py
│   └── test_views.py
├── payment/
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_views.py
│   ├── test_cart.py
│   └── test_purchases.py
├── guardian/
│   └── test_models.py
└── support/
    └── test_models.py
```

### Core (`tests/core/`)
- `test_models.py` - Testes para modelos do core (SvgFile)
- `test_views.py` - Testes para views do core
- `test_services.py` - Testes para serviços do core
- `test_serializers.py` - Testes para serializers

### Usuario (`tests/usuario/`)
- `test_models.py` - Testes para modelos de usuário (CustomUser, Favorite)
- `test_views.py` - Testes para views de autenticação e usuário

### Payment (`tests/payment/`)
- `test_models.py` - Testes para modelos de pagamento (Payment, PaymentItem, Purchase)
- `test_services.py` - Testes para PaymentService
- `test_views.py` - Testes para views de pagamento
- `test_cart.py` - Testes para carrinho de compras
- `test_purchases.py` - Testes para compras

### Guardian (`tests/guardian/`)
- `test_models.py` - Testes para FileAsset e validadores

### Support (`tests/support/`)
- `test_models.py` - Testes para Ticket e TicketMessage

## Executando os Testes

### Instalar Dependências

```bash
pip install -r requirements.txt
```

### Executar Todos os Testes

```bash
pytest tests/
```

### Executar Testes Específicos

```bash
# Por aplicação
pytest tests/core/

# Por arquivo
pytest tests/core/test_models.py

# Por classe de teste
pytest tests/core/test_models.py::TestSvgFileModel

# Por teste específico
pytest tests/core/test_models.py::TestSvgFileModel::test_create_svg_file
```

### Executar com Cobertura

```bash
pytest tests/ --cov=. --cov-report=html
```

Isso gerará um relatório de cobertura em `htmlcov/index.html`.

## Configuração

- `pytest.ini` - Configuração do pytest (localizado na raiz do projeto)
- `tests/conftest.py` - Fixtures compartilhadas entre todos os testes
- `server/test_settings.py` - Configurações Django específicas para testes

## Marcadores (Markers)

Os testes usam marcadores para categorização:

- `@pytest.mark.models` - Testes de models
- `@pytest.mark.views` - Testes de views
- `@pytest.mark.services` - Testes de serviços
- `@pytest.mark.unit` - Testes unitários
- `@pytest.mark.integration` - Testes de integração

### Executar por Marcador

```bash
pytest -m models  # Apenas testes de models
pytest -m views   # Apenas testes de views
```

## Estatísticas

- **Total de Testes**: 152 passing, 1 skipped
- **Cobertura**: Modelos, Views, Services, Serializers

## Mocks e Fixtures

Os testes utilizam:

- `pytest-django` para integração com Django
- `pytest-mock` para mocking
- `pytest-cov` para cobertura de código
- Fixtures customizadas em `conftest.py`

## Migrations

As migrations foram criadas para todos os apps e estão incluídas no repositório.

## Observações

- Todos os testes usam banco de dados em memória SQLite
- Os testes são executados em transações que são revertidas após cada teste
- Mocks são utilizados para testar integrações com gateways de pagamento
