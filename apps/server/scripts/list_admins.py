#!/usr/bin/env python3
"""
Script to list all admin users from the database.
Usage: python scripts/list_admins.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import init_db, SessionLocal, get_session
from db.models import User, PermissionLevelEnum


def list_admin_users():
    """List all users with Admin permission level"""
    init_db()
    
    # SessionLocal is initialized after init_db()
    from db.session import SessionLocal as Session
    db = Session()
    
    try:
        # Query all admin users
        admin_users = db.query(User).filter(
            User.permission_level == PermissionLevelEnum.admin
        ).all()
        
        if not admin_users:
            print("Nenhum usuário administrador encontrado.")
            return
        
        print(f"\n{'='*80}")
        print(f"{'USUÁRIOS ADMINISTRADORES':^80}")
        print(f"{'='*80}\n")
        
        for user in admin_users:
            print(f"ID:              {user.id}")
            print(f"Email:           {user.email}")
            print(f"Nome:            {user.first_name or 'N/A'} {user.last_name or ''}")
            print(f"Telefone:        {user.phone or 'N/A'}")
            print(f"Cargo/Role:      {user.role or 'N/A'}")
            print(f"Permissão:       {user.permission_level}")
            print(f"Ativo:           {'Sim' if user.is_active else 'Não'}")
            print(f"LGPD Check:      {'Sim' if user.lgpd_check else 'Não'}")
            print(f"Mandatos:        {len(user.mandatos)}")
            if user.mandatos:
                for mandato in user.mandatos:
                    print(f"  - {mandato.nome_parlamentar} ({mandato.cargo_parlamentar})")
            print(f"{'-'*80}")
        
        print(f"\nTotal de administradores: {len(admin_users)}\n")
        
    except Exception as e:
        print(f"Erro ao listar administradores: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    list_admin_users()
