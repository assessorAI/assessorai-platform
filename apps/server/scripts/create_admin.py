#!/usr/bin/env python3
"""
Script para criar usuário administrador no sistema.

Uso:
    python -m scripts.create_admin --email admin@example.com --password mypassword
    python -m scripts.create_admin --email admin@example.com  # Senha será solicitada
"""

import argparse
import getpass
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db import session as db_session
from db.models import User, PermissionLevelEnum
from utils.security import get_password_hash


def validate_email(email: str) -> bool:
    """Valida formato básico de email."""
    return "@" in email and "." in email.split("@")[1]


def create_admin_user(email: str, password: str, first_name: str = None, last_name: str = None) -> None:
    """
    Cria um usuário administrador no banco de dados.
    
    Args:
        email: Email do usuário
        password: Senha em texto plano (será hasheada)
        first_name: Nome (opcional)
        last_name: Sobrenome (opcional)
    """
    # Inicializa o banco de dados
    db_session.init_db()
    
    # Acessa SessionLocal após init_db para garantir que foi inicializado
    session = db_session.SessionLocal()
    
    try:
        # Verifica se usuário já existe
        existing = session.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ Erro: Usuário com email '{email}' já existe!")
            print(f"   Permissão atual: {existing.permission_level}")
            print(f"   Nome: {existing.first_name} {existing.last_name}")
            
            # Pergunta se quer atualizar para admin
            response = input("\nDeseja promover este usuário para Admin? (s/N): ")
            if response.lower() in ['s', 'sim', 'y', 'yes']:
                existing.permission_level = PermissionLevelEnum.admin.value
                existing.hashed_password = get_password_hash(password)
                existing.is_active = True
                session.commit()
                print(f"✅ Usuário '{email}' promovido para Admin e senha atualizada!")
            else:
                print("Operação cancelada.")
            return
        
        # Cria novo usuário admin
        admin_user = User(
            email=email,
            first_name=first_name or email.split("@")[0],
            last_name=last_name or "Admin",
            hashed_password=get_password_hash(password),
            permission_level=PermissionLevelEnum.admin.value,
            is_active=True
        )
        
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        print(f"✅ Usuário administrador criado com sucesso!")
        print(f"   ID: {admin_user.id}")
        print(f"   Email: {admin_user.email}")
        print(f"   Nome: {admin_user.first_name} {admin_user.last_name}")
        print(f"   Permissão: {admin_user.permission_level}")
        print(f"   Ativo: {admin_user.is_active}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao criar usuário: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Cria usuário administrador no sistema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Com senha via argumento
  python -m scripts.create_admin --email admin@assessorai.org --password minhasenha123
  
  # Senha será solicitada (mais seguro)
  python -m scripts.create_admin --email admin@assessorai.org
  
  # Com nome completo
  python -m scripts.create_admin --email admin@assessorai.org --first-name João --last-name Silva
        """
    )
    
    parser.add_argument(
        "--email",
        required=True,
        help="Email do usuário administrador"
    )
    parser.add_argument(
        "--password",
        help="Senha do usuário (se não fornecida, será solicitada)"
    )
    parser.add_argument(
        "--first-name",
        help="Primeiro nome do usuário"
    )
    parser.add_argument(
        "--last-name",
        help="Sobrenome do usuário"
    )
    
    args = parser.parse_args()
    
    # Valida email
    if not validate_email(args.email):
        print(f"❌ Erro: Email '{args.email}' inválido!")
        sys.exit(1)
    
    # Obtém senha
    if args.password:
        password = args.password
        print("⚠️  Aviso: Senha fornecida via argumento (visível no histórico do shell)")
    else:
        password = getpass.getpass("Digite a senha para o admin: ")
        password_confirm = getpass.getpass("Confirme a senha: ")
        
        if password != password_confirm:
            print("❌ Erro: Senhas não conferem!")
            sys.exit(1)
        
        if len(password) < 6:
            print("❌ Erro: Senha deve ter pelo menos 6 caracteres!")
            sys.exit(1)
    
    # Cria usuário
    create_admin_user(
        email=args.email,
        password=password,
        first_name=args.first_name,
        last_name=args.last_name
    )


if __name__ == "__main__":
    main()
