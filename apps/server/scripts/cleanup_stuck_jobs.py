#!/usr/bin/env python3
"""
Script para limpar jobs de importação vetorial travados.

Jobs são considerados travados se estiverem em PENDING ou PROCESSING
por mais de um tempo configurável (padrão: 30 minutos).

Uso:
    python scripts/cleanup_stuck_jobs.py [--timeout MINUTES] [--dry-run]

Exemplos:
    python scripts/cleanup_stuck_jobs.py --timeout 10
    python scripts/cleanup_stuck_jobs.py --dry-run
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from db.models import VectorImportJob, VectorImportJobStatus


def cleanup_stuck_jobs(timeout_minutes: int = 30, dry_run: bool = False) -> dict:
    """
    Marca jobs travados como FAILED.
    
    Args:
        timeout_minutes: Tempo em minutos para considerar job travado
        dry_run: Se True, apenas lista os jobs sem modificar
    
    Returns:
        Dict com estatísticas da limpeza
    """
    session = SessionLocal()
    stats = {
        "total_stuck": 0,
        "marked_failed": 0,
        "errors": []
    }
    
    try:
        threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        # Buscar jobs travados
        stuck_jobs = session.query(VectorImportJob).filter(
            VectorImportJob.status.in_([
                VectorImportJobStatus.PENDING,
                VectorImportJobStatus.PROCESSING
            ]),
            VectorImportJob.created_at < threshold
        ).all()
        
        stats["total_stuck"] = len(stuck_jobs)
        
        if not stuck_jobs:
            print(f"✅ Nenhum job travado encontrado (threshold: {timeout_minutes} minutos)")
            return stats
        
        print(f"\n⚠️  Encontrados {len(stuck_jobs)} jobs travados:\n")
        
        for job in stuck_jobs:
            elapsed = datetime.utcnow() - job.created_at
            hours = int(elapsed.total_seconds() / 3600)
            minutes = int((elapsed.total_seconds() % 3600) / 60)
            
            print(f"  ID {job.id}: {job.name}")
            print(f"    Status: {job.status}")
            print(f"    Criado há: {hours}h {minutes}m")
            print(f"    Items: {job.total_items}")
            print()
            
            if not dry_run:
                try:
                    job.status = VectorImportJobStatus.FAILED
                    job.error_message = (
                        f"Job marcado como falho automaticamente após {timeout_minutes} minutos sem resposta. "
                        f"Possível deadlock, timeout ou erro não capturado."
                    )
                    job.completed_at = datetime.utcnow()
                    stats["marked_failed"] += 1
                except Exception as e:
                    stats["errors"].append(f"Erro ao marcar job {job.id}: {e}")
        
        if not dry_run:
            session.commit()
            print(f"✅ {stats['marked_failed']} jobs marcados como FAILED")
        else:
            print("🔵 DRY RUN - Nenhuma alteração foi feita")
            print("   Execute sem --dry-run para aplicar as mudanças")
        
        if stats["errors"]:
            print(f"\n❌ Erros encontrados:")
            for error in stats["errors"]:
                print(f"   {error}")
    
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        stats["errors"].append(str(e))
        session.rollback()
    finally:
        session.close()
    
    return stats


def list_all_jobs():
    """Lista todos os jobs de importação."""
    session = SessionLocal()
    try:
        from sqlalchemy import func
        
        # Estatísticas por status
        status_counts = session.query(
            VectorImportJob.status,
            func.count(VectorImportJob.id)
        ).group_by(VectorImportJob.status).all()
        
        print("\n=== ESTATÍSTICAS DE JOBS ===\n")
        for status, count in status_counts:
            icon = {
                "PENDING": "🔵",
                "PROCESSING": "⚠️ ",
                "COMPLETED": "✅",
                "FAILED": "❌"
            }.get(status, "")
            print(f"  {icon}{status}: {count}")
        
        # Últimos 10 jobs
        jobs = session.query(VectorImportJob).order_by(
            VectorImportJob.created_at.desc()
        ).limit(10).all()
        
        print("\n=== ÚLTIMOS 10 JOBS ===\n")
        for job in jobs:
            print(f"  ID {job.id}: {job.name}")
            print(f"    Status: {job.status}")
            print(f"    Criado: {job.created_at}")
            if job.completed_at:
                print(f"    Completado: {job.completed_at}")
            print()
    
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Limpa jobs de importação vetorial travados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                    # Limpa jobs travados há mais de 30 minutos
  %(prog)s --timeout 10       # Limpa jobs travados há mais de 10 minutos
  %(prog)s --dry-run          # Apenas lista, não modifica
  %(prog)s --list             # Lista todos os jobs
        """
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="MINUTES",
        help="Tempo em minutos para considerar job travado (padrão: 30)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas lista jobs sem modificar o banco"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista todos os jobs e suas estatísticas"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_all_jobs()
        return
    
    print(f"🔍 Procurando jobs travados há mais de {args.timeout} minutos...")
    if args.dry_run:
        print("🔵 Modo DRY RUN - nenhuma alteração será feita\n")
    
    stats = cleanup_stuck_jobs(args.timeout, args.dry_run)
    
    print("\n=== RESUMO ===")
    print(f"  Jobs travados encontrados: {stats['total_stuck']}")
    print(f"  Jobs marcados como FAILED: {stats['marked_failed']}")
    if stats["errors"]:
        print(f"  Erros: {len(stats['errors'])}")


if __name__ == "__main__":
    main()
