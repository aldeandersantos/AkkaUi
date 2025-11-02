# run_deploy.py

import os
import subprocess
import sys

def run_command(command):
    """Executa um comando no shell e verifica por erros."""
    print(f"Executando: {command}")
    try:
        # Usa subprocess.run para executar o comando
        subprocess.run(
            command,
            shell=True,
            check=True,  # Levanta erro se o comando falhar (status de saída diferente de 0)
            text=True,
            capture_output=True
        )
        print("Comando executado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o comando: {e.cmd}")
        print(f"Stdout:\n{e.stdout}")
        print(f"Stderr:\n{e.stderr}")
        sys.exit(1) # Sai com erro para interromper o deploy

def main():
    # 1. Configura as variáveis de ambiente necessárias para o Django
    # Importante: o Gunicorn já define DJANGO_SETTINGS_MODULE ao iniciar, 
    # mas é bom garantir para os comandos de gerenciamento.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

    # A. Instala dependências (Geralmente feito pelo Render antes, mas incluímos por segurança)
    # run_command("pip install -r requirements.txt")

    # B. Cria migrações para todos os apps
    # Por padrão executa: makemigrations --no-input
    run_command("python manage.py makemigrations --no-input")

    # B.1. Rodar makemigrations para apps específicos.
    # Temos uma lista padrão de apps que queremos garantir (inclui djstripe).
    default_apps = [
        "core",
        "usuario",
        "payment",
        "support",
        "guardian",
        "djstripe",
    ]

    # Se EXTRA_MAKEMIGRATE_APPS estiver definida, utiliza esses apps primeiro
    # e depois adiciona os defaults que não foram listados (evita duplicação).
    extras_env = os.environ.get("EXTRA_MAKEMIGRATE_APPS")
    if extras_env:
        apps = [a.strip() for a in extras_env.split(",") if a.strip()]
        combined = apps + [a for a in default_apps if a not in apps]
    else:
        combined = default_apps

    for app in combined:
        print(f"Executando makemigrations para app: {app}")
        run_command(f"python manage.py makemigrations {app} --no-input")

    # C. Coleta Arquivos Estáticos
    run_command("python manage.py collectstatic --no-input")

    # D. Aplica Migrações (Cria tabelas)
    run_command("python manage.py migrate --no-input")

    # E. Cria/Atualiza Superusuário (especificado pelo usuário)
    # Os valores abaixo seguem sua solicitação; também permitimos sobrescrever via
    # variáveis de ambiente DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD.
    print("Garantindo superusuário...")
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "Aldeander")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "aldeander-santos@hotmail.com")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "123456")

    # Código a executar dentro do contexto do Django (manage.py shell -c)
    create_code = (
        "from django.contrib.auth import get_user_model\n"
        "User = get_user_model()\n"
        f"username = '{username}'\n"
        f"email = '{email}'\n"
        f"password = '{password}'\n"
        "u = User.objects.filter(username=username).first()\n"
        "if not u:\n"
        "    User.objects.create_superuser(username=username, email=email, password=password)\n"
        "else:\n"
        "    u.email = email\n"
        "    u.set_password(password)\n"
        "    u.is_staff = True\n"
        "    u.is_superuser = True\n"
        "    u.save()\n"
        "print('Superusuário garantido')\n"
    )

    try:
        result = subprocess.run([
            sys.executable,
            "manage.py",
            "shell",
            "-c",
            create_code,
        ], check=False, capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)
        else:
            # Não falhamos o deploy por conta de problemas menores aqui;
            # apenas exibimos o erro para inspeção.
            print("Aviso: falha ao garantir superusuário (não fatal).")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
    except Exception as e:
        print(f"Erro ao tentar garantir superusuário: {e}")


if __name__ == "__main__":
    main()