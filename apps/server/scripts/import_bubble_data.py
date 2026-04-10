#!/usr/bin/env python3
"""
Script para importar dados de usuários e mandatos do Bubble.io para o banco de dados.

Uso:
    python scripts/import_bubble_data.py [options]
    
Opções:
    --dry-run              Simula a importação sem escrever no banco
    --force                Remove dados existentes antes de importar
    --send-password-reset  Envia emails de troca de senha para todos os usuários importados
    --users-only           Importa apenas usuários
    --mandatos-only        Importa apenas mandatos
    --skip-orphans         Pula mandatos sem usuários (padrão: True)
    --user-file PATH       Caminho para arquivo JSON de usuários (padrão: data/bubble-users.json)
    --mandato-file PATH    Caminho para arquivo JSON de mandatos (padrão: data/bubble-mandatos.json)

Exemplos:
    # Importação normal (apenas cria usuários e mandatos)
    python scripts/import_bubble_data.py
    
    # Importação com envio automático de emails de troca de senha
    python scripts/import_bubble_data.py --send-password-reset
    
    # Importar apenas usuários @legislabrasil.org
    python scripts/import_bubble_data.py --user-file data/bubble-assessorai.json --mandato-file data/bubble-assessorai-mandatos.json
    
    # Simular importação com emails (não grava no banco)
    python scripts/import_bubble_data.py --dry-run --send-password-reset
    
    # Limpar dados existentes e reimportar com emails
    python scripts/import_bubble_data.py --force --send-password-reset
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import secrets

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Adiciona o diretório raiz ao path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import db.session as db_session
from db.models import User, Mandato, PermissionLevelEnum, PasswordResetToken
from utils.security import get_password_hash

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DATA_DIR = ROOT_DIR / "data"
USERS_FILE = DATA_DIR / "bubble-users.json"
MANDATOS_FILE = DATA_DIR / "bubble-mandatos.json"
DEFAULT_PASSWORD = "TrocarSenha@2025"  # Usuários devem redefinir na primeira ativação


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Bubble.io data to database")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate import without writing to database"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear existing data before importing"
    )
    parser.add_argument(
        "--users-only",
        action="store_true",
        help="Import only users"
    )
    parser.add_argument(
        "--mandatos-only",
        action="store_true",
        help="Import only mandatos"
    )
    parser.add_argument(
        "--skip-orphans",
        action="store_true",
        default=True,
        help="Skip mandatos without users (default: True)"
    )
    parser.add_argument(
        "--user-file",
        type=str,
        default=None,
        help="Path to users JSON file (default: data/bubble-users.json)"
    )
    parser.add_argument(
        "--mandato-file",
        type=str,
        default=None,
        help="Path to mandatos JSON file (default: data/bubble-mandatos.json)"
    )
    parser.add_argument(
        "--send-password-reset",
        action="store_true",
        help="Send password reset emails to all imported users"
    )
    return parser.parse_args()


def load_json_file(file_path: Path) -> List[Dict]:
    """Carrega e valida arquivo JSON."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} records from {file_path.name}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path.name}: {e}")
        return []


def normalize_string(value: Optional[str]) -> Optional[str]:
    """Normaliza strings removendo espaços extras."""
    if not value or value.strip() == "":
        return None
    return value.strip()


def parse_boolean(value: Optional[str]) -> bool:
    """Converte valores string para boolean."""
    if not value:
        return False
    return value.strip().lower() in ("sim", "yes", "true", "1")


def normalize_cargo_parlamentar(cargo: Optional[str]) -> Optional[str]:
    """
    Normaliza o cargo parlamentar para os valores aceitos pelo sistema.
    
    Mapeia valores do Bubble (com gênero) para valores sem gênero:
    - Vereador(a) -> Vereador
    - Deputado(a) estadual -> Deputado Estadual
    - Deputado(a) federal -> Deputado Federal
    - Senador(a) -> Senador
    """
    if not cargo:
        return None
    
    cargo_normalized = cargo.strip()
    
    # Mapeamento de valores do Bubble para valores aceitos
    cargo_mapping = {
        "vereador(a)": "Vereador",
        "vereador": "Vereador",
        "deputado(a) estadual": "Deputado Estadual",
        "deputado estadual": "Deputado Estadual",
        "deputado(a) federal": "Deputado Federal",
        "deputado federal": "Deputado Federal",
        "senador(a)": "Senador",
        "senador": "Senador",
    }
    
    return cargo_mapping.get(cargo_normalized.lower(), cargo_normalized)


def map_permission_level(acesso: Optional[str], is_admin: bool) -> str:
    """Mapeia nível de acesso do Bubble para PermissionLevel do sistema."""
    if is_admin:
        return PermissionLevelEnum.admin.value
    
    acesso_normalized = normalize_string(acesso)
    if not acesso_normalized:
        return PermissionLevelEnum.user.value
    
    mapping = {
        "gestor": PermissionLevelEnum.manager.value,
        "manager": PermissionLevelEnum.manager.value,
        "admin": PermissionLevelEnum.admin.value,
        "administrator": PermissionLevelEnum.admin.value,
    }
    
    return mapping.get(acesso_normalized.lower(), PermissionLevelEnum.user.value)


def parse_user_record(record: Dict) -> Optional[Dict]:
    """Parseia e valida um registro de usuário do Bubble."""
    email = normalize_string(record.get("email"))
    if not email:
        logger.warning(f"Skipping user record without email: {record.get('unique id')}")
        return None
    
    # Verifica se o email foi confirmado
    email_confirmed = parse_boolean(record.get("Email Confirmed"))
    if not email_confirmed:
        logger.debug(f"User {email} has unconfirmed email, importing as inactive")
    
    is_admin = parse_boolean(record.get("admin"))
    acesso = record.get("acesso")
    
    user_data = {
        "email": email.lower(),
        "first_name": normalize_string(record.get("first name")),
        "last_name": normalize_string(record.get("last name")),
        "phone": normalize_string(record.get("phone") or record.get("telefone")),
        "permission_level": map_permission_level(acesso, is_admin),
        "lgpd_check": parse_boolean(record.get("aceite_lgpd")),
        "role": normalize_string(record.get("funcao")),
        "is_active": email_confirmed,
        "mandato_name": normalize_string(record.get("Mandato")),
        "bubble_id": record.get("unique id"),
    }
    
    return user_data


def parse_mandato_record(record: Dict, skip_orphans: bool = True) -> Optional[Dict]:
    """Parseia e valida um registro de mandato do Bubble."""
    nome = normalize_string(record.get("nome_parlamentar"))
    if not nome:
        logger.warning(f"Skipping mandato without nome_parlamentar: {record.get('unique id')}")
        return None
    
    # Parseia lista de usuários (emails separados por vírgula)
    usuarios_str = normalize_string(record.get("usuarios"))
    user_emails = []
    if usuarios_str:
        user_emails = [
            email.strip().lower() 
            for email in usuarios_str.split(",") 
            if email.strip()
        ]
    
    # Pula mandatos sem usuários se skip_orphans=True
    if skip_orphans and not user_emails:
        logger.debug(f"Skipping orphan mandato (no users): {nome}")
        return None
    
    # Parseia temas de interesse
    temas_str = normalize_string(record.get("temas"))
    temas_list = []
    if temas_str:
        temas_list = [t.strip() for t in temas_str.split(",") if t.strip()]
    
    mandato_data = {
        "nome_parlamentar": nome,
        "casa_legislativa": normalize_string(record.get("casa_legislativa")),
        "cargo_parlamentar": normalize_cargo_parlamentar(record.get("cargo")),
        "partido": normalize_string(record.get("partido")),
        "esfera": None,  # Não presente no JSON, pode ser inferido da casa
        "municipio": normalize_string(record.get("municipio")),
        "ue": normalize_string(record.get("uf")),
        "temas_interesse": ", ".join(temas_list) if temas_list else None,
        "perfil_parlamentar": normalize_string(record.get("perfil")),
        "espectro_politico": normalize_string(record.get("posicionamento")),
        "data": datetime.now().strftime("%d/%m/%Y"),
        "user_emails": user_emails,
        "bubble_id": record.get("unique id"),
    }
    
    return mandato_data


def clear_existing_data(session, force: bool = False, users_only: bool = False, mandatos_only: bool = False) -> None:
    """Remove dados existentes se force=True, respeitando as flags de seleção."""
    if not force:
        return
    
    try:
        if users_only:
            # Remove apenas usuários e seus relacionamentos
            logger.warning("FORCE mode: Clearing existing users only...")
            session.execute(text("DELETE FROM mandato_user_link"))
            session.execute(text("DELETE FROM users"))
        elif mandatos_only:
            # Remove apenas mandatos e seus relacionamentos
            logger.warning("FORCE mode: Clearing existing mandatos only...")
            session.execute(text("DELETE FROM mandato_user_link"))
            session.execute(text("DELETE FROM mandatos"))
        else:
            # Remove tudo
            logger.warning("FORCE mode: Clearing existing mandatos and users...")
            session.execute(text("DELETE FROM mandato_user_link"))
            session.execute(text("DELETE FROM mandatos"))
            session.execute(text("DELETE FROM users"))
        
        session.commit()
        logger.info("Existing data cleared successfully")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to clear existing data: {e}")
        raise


def send_password_reset_emails(
    session,
    user_map: Dict[str, int],
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Envia emails de reset de senha para todos os usuários importados.
    Retorna estatísticas {sent: int, failed: int, skipped: int}.
    """
    # Import direto para evitar problemas com __init__.py
    import sys
    import importlib.util
    
    # Carrega sendgrid_service diretamente sem passar pelo __init__.py
    spec = importlib.util.spec_from_file_location(
        "sendgrid_service_module",
        ROOT_DIR / "services" / "sendgrid_service.py"
    )
    sendgrid_module = importlib.util.module_from_spec(spec)
    sys.modules["sendgrid_service_module"] = sendgrid_module
    spec.loader.exec_module(sendgrid_module)
    get_email_service = sendgrid_module.get_email_service
    
    # Carrega config diretamente
    spec = importlib.util.spec_from_file_location(
        "config_module",
        ROOT_DIR / "utils" / "config.py"
    )
    config_module = importlib.util.module_from_spec(spec)
    sys.modules["config_module"] = config_module
    spec.loader.exec_module(config_module)
    get_frontend_url = config_module.get_frontend_url
    
    email_service = get_email_service()
    
    if not email_service.is_configured:
        logger.warning("SendGrid not configured - skipping password reset emails")
        return {"sent": 0, "failed": 0, "skipped": len(user_map)}
    
    stats = {"sent": 0, "failed": 0, "skipped": 0}
    frontend_url = get_frontend_url()
    
    logger.info(f"Sending password reset emails to {len(user_map)} users...")
    
    for email, user_id in user_map.items():
        try:
            user = session.get(User, user_id)
            if not user:
                logger.warning(f"User {email} not found, skipping email")
                stats["skipped"] += 1
                continue
            
            if dry_run:
                logger.info(f"[DRY-RUN] Would send password reset email to: {email}")
                stats["sent"] += 1
                continue
            
            # Gera token de reset de senha com validade de 24h
            token_str = secrets.token_urlsafe(32)
            expires = timedelta(hours=24)
            
            reset_token = PasswordResetToken(
                token=token_str,
                user_id=user.id,
                expires_at=datetime.now() + expires,
                used=False
            )
            session.add(reset_token)
            session.flush()
            
            # Prepara link de reset
            reset_link = f"{frontend_url}/reset-password?token={token_str}"
            
            # Envia email
            status_code = email_service.send_email(
                recipients=email,
                subject="Bem-vindo ao AssessorAI - Troque sua Senha",
                template_name="bubble_import_password_reset.md",
                template_context={
                    "first_name": user.first_name or "Usuário",
                    "email": email,
                    "reset_link": reset_link
                }
            )
            
            if status_code and 200 <= status_code < 300:
                stats["sent"] += 1
                logger.debug(f"Password reset email sent to: {email}")
            else:
                stats["failed"] += 1
                logger.warning(f"Failed to send password reset email to: {email}")
            
        except Exception as e:
            logger.error(f"Error sending password reset email to {email}: {e}")
            stats["failed"] += 1
    
    if not dry_run:
        session.commit()
    
    logger.info(
        f"Password reset emails: {stats['sent']} sent, "
        f"{stats['failed']} failed, {stats['skipped']} skipped"
    )
    return stats


def load_existing_users(session) -> Dict[str, int]:
    """
    Carrega usuários existentes no banco de dados.
    Retorna mapeamento {email: user_id}.
    """
    logger.info("Loading existing users from database...")
    user_map = {}
    
    try:
        users = session.query(User).all()
        for user in users:
            user_map[user.email] = user.id
        
        logger.info(f"Loaded {len(user_map)} existing users")
        return user_map
    except Exception as e:
        logger.error(f"Error loading existing users: {e}")
        return {}


def import_users(
    session, 
    users_data: List[Dict], 
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Importa usuários para o banco de dados.
    Retorna mapeamento {email: user_id}.
    """
    logger.info(f"Importing {len(users_data)} users...")
    user_map = {}
    hashed_pw = get_password_hash(DEFAULT_PASSWORD)
    
    created = 0
    skipped = 0
    errors = 0
    
    for user_data in users_data:
        email = user_data["email"]
        
        try:
            # Verifica se usuário já existe - se existir, pula
            existing = session.query(User).filter(User.email == email).first()
            if existing:
                logger.warning(f"User already exists, skipping: {email}")
                user_map[email] = existing.id
                skipped += 1
                continue
            
            if dry_run:
                logger.info(f"[DRY-RUN] Would create user: {email}")
                created += 1
                continue
            
            # Cria novo usuário
            user = User(
                email=email,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                phone=user_data["phone"],
                permission_level=user_data["permission_level"],
                lgpd_check=user_data["lgpd_check"],
                role=user_data["role"],
                is_active=user_data["is_active"],
                hashed_password=hashed_pw,
            )
            
            session.add(user)
            session.flush()  # Para obter o ID
            user_map[email] = user.id
            created += 1
            
            logger.debug(
                f"Created user: {email} (id={user.id}, "
                f"permission={user_data['permission_level']})"
            )
            
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Duplicate user {email}: {e}")
            skipped += 1
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user {email}: {e}")
            errors += 1
    
    if not dry_run:
        session.commit()
    
    logger.info(
        f"Users import complete: {created} created, {skipped} skipped, {errors} errors"
    )
    return user_map


def import_mandatos(
    session,
    mandatos_data: List[Dict],
    user_map: Dict[str, int],
    dry_run: bool = False
) -> tuple[Dict[str, int], List[Dict]]:
    """
    Importa mandatos e estabelece relacionamentos com usuários.
    Retorna tupla: (mapeamento {nome_parlamentar: mandato_id}, lista de mandatos pulados).
    """
    logger.info(f"Importing {len(mandatos_data)} mandatos...")
    mandato_map = {}
    skipped_mandatos = []
    
    created = 0
    skipped = 0
    errors = 0
    links_created = 0
    links_skipped = 0
    
    for mandato_data in mandatos_data:
        nome = mandato_data["nome_parlamentar"]
        
        try:
            # Verifica se mandato já existe - se existir, pula
            existing = session.query(Mandato).filter(
                Mandato.nome_parlamentar == nome
            ).first()
            
            if existing:
                logger.warning(f"Mandato already exists, will sync users: {nome}")
                mandato_map[nome] = existing.id
                mandato = existing
                skipped += 1
                # Registra mandato duplicado
                skipped_mandatos.append({
                    "nome": nome,
                    "casa": mandato_data["casa_legislativa"],
                    "cargo": mandato_data["cargo_parlamentar"],
                    "partido": mandato_data["partido"],
                    "municipio": mandato_data["municipio"],
                    "reason": "Duplicado - nome já existe no banco"
                })
                # Continue to link users below instead of skipping
            
            else:
                if dry_run:
                    logger.info(f"[DRY-RUN] Would create mandato: {nome}")
                    created += 1
                    # Simula ID para dry-run
                    mandato_map[nome] = -1
                    continue
                
                # Cria novo mandato
                mandato = Mandato(
                    nome_parlamentar=nome,
                    casa_legislativa=mandato_data["casa_legislativa"],
                    cargo_parlamentar=mandato_data["cargo_parlamentar"],
                    partido=mandato_data["partido"],
                    esfera=mandato_data["esfera"],
                    municipio=mandato_data["municipio"],
                    ue=mandato_data["ue"],
                    temas_interesse=mandato_data["temas_interesse"],
                    perfil_parlamentar=mandato_data["perfil_parlamentar"],
                    espectro_politico=mandato_data["espectro_politico"],
                    data=mandato_data["data"],
                )
                
                session.add(mandato)
                session.flush()
                mandato_map[nome] = mandato.id
                created += 1
                
                logger.debug(f"Created mandato: {nome} (id={mandato.id})")
            
            # Vincula usuários ao mandato (funciona tanto para mandatos novos quanto existentes)
            for user_email in mandato_data["user_emails"]:
                if user_email not in user_map:
                    logger.warning(
                        f"User {user_email} not found for mandato {nome}, skipping link"
                    )
                    links_skipped += 1
                    continue
                
                user_id = user_map[user_email]
                
                if dry_run:
                    logger.debug(
                        f"[DRY-RUN] Would link user {user_email} to mandato {nome}"
                    )
                    links_created += 1
                    continue
                
                # Verifica se link já existe
                user = session.get(User, user_id)
                if mandato not in user.mandatos:
                    user.mandatos.append(mandato)
                    links_created += 1
                    logger.debug(f"Linked user {user_email} to mandato {nome}")
                else:
                    links_skipped += 1
            
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Duplicate mandato {nome}: {e}")
            skipped += 1
            skipped_mandatos.append({
                "nome": nome,
                "casa": mandato_data.get("casa_legislativa"),
                "cargo": mandato_data.get("cargo_parlamentar"),
                "partido": mandato_data.get("partido"),
                "municipio": mandato_data.get("municipio"),
                "reason": f"Erro de integridade: {str(e)[:100]}"
            })
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating mandato {nome}: {e}")
            errors += 1
            skipped_mandatos.append({
                "nome": nome,
                "casa": mandato_data.get("casa_legislativa"),
                "cargo": mandato_data.get("cargo_parlamentar"),
                "partido": mandato_data.get("partido"),
                "municipio": mandato_data.get("municipio"),
                "reason": f"Erro: {str(e)[:100]}"
            })
    
    if not dry_run:
        session.commit()
    
    logger.info(
        f"Mandatos import complete: {created} created, {skipped} skipped, "
        f"{errors} errors, {links_created} links created, {links_skipped} links skipped"
    )
    return mandato_map, skipped_mandatos


def generate_import_report(
    users_data: List[Dict],
    mandatos_data: List[Dict],
    user_map: Dict[str, int],
    mandato_map: Dict[str, int],
    skipped_mandatos: List[Dict]
) -> None:
    """Gera relatório de importação."""
    logger.info("=" * 80)
    logger.info("IMPORT REPORT")
    logger.info("=" * 80)
    logger.info(f"Users loaded from JSON: {len(users_data)}")
    logger.info(f"Users imported to DB: {len(user_map)}")
    logger.info(f"Mandatos loaded from JSON: {len(mandatos_data)}")
    logger.info(f"Mandatos imported to DB: {len(mandato_map)}")
    
    # Estatísticas de permissões
    permission_stats = {}
    for user_data in users_data:
        perm = user_data["permission_level"]
        permission_stats[perm] = permission_stats.get(perm, 0) + 1
    
    logger.info("\nUsers by permission level:")
    for perm, count in sorted(permission_stats.items()):
        logger.info(f"  {perm}: {count}")
    
    # Mandatos não importados
    if skipped_mandatos:
        logger.warning(f"\n{len(skipped_mandatos)} mandatos NOT imported:")
        for m in skipped_mandatos:
            logger.warning(
                f"  - {m['nome']} | Casa: {m['casa']} | "
                f"Cargo: {m['cargo']} | Município: {m['municipio']}"
            )
            logger.warning(f"    Motivo: {m['reason']}")
    
    # Usuários órfãos (sem mandato)
    orphan_users = [
        u for u in users_data 
        if not u.get("mandato_name") or u["mandato_name"] not in mandato_map
    ]
    if orphan_users:
        logger.warning(f"\n{len(orphan_users)} users without valid mandato:")
        for u in orphan_users[:10]:
            logger.warning(f"  - {u['email']} (mandato: {u.get('mandato_name')})")
        if len(orphan_users) > 10:
            logger.warning(f"  ... and {len(orphan_users) - 10} more")
    
    logger.info("=" * 80)


def main():
    args = parse_args()
    
    if args.dry_run:
        logger.info("DRY-RUN MODE: No data will be written to database")
    
    # Inicializa banco de dados
    db_session.init_db()
    session = db_session.SessionLocal()
    
    try:
        # Limpa dados existentes se --force
        if args.force and not args.dry_run:
            clear_existing_data(
                session,
                force=True,
                users_only=args.users_only,
                mandatos_only=args.mandatos_only
            )
        
        # Determina os arquivos a serem usados
        users_file = Path(args.user_file) if args.user_file else USERS_FILE
        mandatos_file = Path(args.mandato_file) if args.mandato_file else MANDATOS_FILE
        
        # Carrega dados dos arquivos JSON
        users_raw = load_json_file(users_file) if not args.mandatos_only else []
        mandatos_raw = load_json_file(mandatos_file) if not args.users_only else []
        
        # Parseia e valida dados
        users_data = [
            parsed for record in users_raw 
            if (parsed := parse_user_record(record)) is not None
        ]
        
        mandatos_data = [
            parsed for record in mandatos_raw
            if (parsed := parse_mandato_record(record, skip_orphans=args.skip_orphans)) is not None
        ]
        
        logger.info(f"Parsed {len(users_data)} valid users from {len(users_raw)} records")
        logger.info(f"Parsed {len(mandatos_data)} valid mandatos from {len(mandatos_raw)} records")
        
        if args.skip_orphans:
            orphan_count = len(mandatos_raw) - len(mandatos_data) - sum(
                1 for r in mandatos_raw if not normalize_string(r.get("nome_parlamentar"))
            )
            logger.info(f"Skipped {orphan_count} orphan mandatos (no users)")
        
        # Importa dados
        user_map = {}
        mandato_map = {}
        skipped_mandatos = []
        
        if not args.mandatos_only:
            user_map = import_users(session, users_data, dry_run=args.dry_run)
        else:
            # Quando importando apenas mandatos, carrega usuários existentes do banco
            user_map = load_existing_users(session)
        
        if not args.users_only:
            mandato_map, skipped_mandatos = import_mandatos(
                session, mandatos_data, user_map, dry_run=args.dry_run
            )
        
        # Envia emails de reset de senha se solicitado
        email_stats = {}
        if args.send_password_reset and user_map:
            logger.info("\n" + "="*80)
            logger.info("SENDING PASSWORD RESET EMAILS")
            logger.info("="*80)
            email_stats = send_password_reset_emails(session, user_map, dry_run=args.dry_run)
        
        # Gera relatório
        generate_import_report(users_data, mandatos_data, user_map, mandato_map, skipped_mandatos)
        
        # Relatório de emails
        if args.send_password_reset and email_stats:
            logger.info("\n" + "="*80)
            logger.info("EMAIL REPORT")
            logger.info("="*80)
            logger.info(f"Emails sent: {email_stats.get('sent', 0)}")
            logger.info(f"Emails failed: {email_stats.get('failed', 0)}")
            logger.info(f"Emails skipped: {email_stats.get('skipped', 0)}")
            logger.info("="*80)
        
        if args.dry_run:
            logger.info("\nDRY-RUN completed. No changes were made to the database.")
        else:
            logger.info("\nImport completed successfully!")
            if not args.send_password_reset:
                logger.info(f"Default password for all users: {DEFAULT_PASSWORD}")
                logger.info("Users should reset their passwords on first login.")
                logger.info("Tip: Use --send-password-reset to automatically send password reset emails.")
            else:
                logger.info("Password reset emails have been sent to all imported users.")
        
    except Exception as e:
        logger.exception(f"Import failed: {e}")
        session.rollback()
        return 1
    finally:
        session.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
