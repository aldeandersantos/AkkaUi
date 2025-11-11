# Testes do Backend - AkkaUi

Este diretório contém testes abrangentes para o backend do AkkaUi usando pytest.

## Estrutura dos Testes

Os testes estão organizados por aplicação Django:

### Core (`core/`)
- `test_models.py` - Testes para modelos do core (SvgFile)
- `test_views.py` - Testes para views do core
- `test_services.py` - Testes para serviços do core
- `test_serializers.py` - Testes para serializers

### Usuario (`usuario/`)
- `test_models.py` - Testes para modelos de usuário (CustomUser, Favorite)
- `test_views.py` - Testes para views de autenticação e usuário

### Payment (`payment/`)
- `test_models.py` - Testes para modelos de pagamento (Payment, PaymentItem, Purchase)
- `test_services.py` - Testes para PaymentService
- `test_views.py` - Testes para views de pagamento
- `test_cart.py` - Testes para carrinho de compras
- `test_purchases.py` - Testes para compras

### Guardian (`guardian/`)
- `test_models.py` - Testes para FileAsset e validadores

### Support (`support/`)
- `test_models.py` - Testes para Ticket e TicketMessage

## Executando os Testes

### Instalar Dependências

```bash
pip install -r requirements.txt
```

### Executar Todos os Testes

```bash
pytest
```

### Executar Testes Específicos

```bash
# Por aplicação
pytest core/test_*.py

# Por arquivo
pytest core/test_models.py

# Por classe de teste
pytest core/test_models.py::TestSvgFileModel

# Por teste específico
pytest core/test_models.py::TestSvgFileModel::test_create_svg_file
```

### Executar com Cobertura

```bash
pytest --cov=. --cov-report=html
```

Isso gerará um relatório de cobertura em `htmlcov/index.html`.

## Configuração

- `pytest.ini` - Configuração do pytest
- `conftest.py` - Fixtures compartilhadas entre todos os testes
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
