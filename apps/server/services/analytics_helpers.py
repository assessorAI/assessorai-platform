from enum import Enum
from typing import Optional


class FuncionalidadeEnum(str, Enum):
    """Business-level feature categories"""
    AUTENTICACAO = "auth"
    EXPERT_PL = "expert_pl"
    OFICIOS = "oficios"
    BUSCA_VETORIAL = "vector_search"
    GESTAO_PROMPTS = "prompts"
    AVALIACAO_PROMPTS = "prompt_evaluation"
    ADMIN = "admin"
    OUTROS = "outros"


def get_funcionalidade_from_event(event_type: str) -> str:
    """
    Maps technical event_type to business funcionalidade.
    
    Examples:
        'auth:login' -> 'auth'
        'expert_pl.analysis.success' -> 'expert_pl'
        'oficio.generate.success' -> 'oficios'
    """
    # Split by '.' or ':' and take first part
    if ':' in event_type:
        prefix = event_type.split(':')[0]
    elif '.' in event_type:
        prefix = event_type.split('.')[0]
    else:
        prefix = event_type
    
    mapping = {
        'auth': FuncionalidadeEnum.AUTENTICACAO.value,
        'expert_pl': FuncionalidadeEnum.EXPERT_PL.value,
        'oficio': FuncionalidadeEnum.OFICIOS.value,
        'vector_search': FuncionalidadeEnum.BUSCA_VETORIAL.value,
        'vector_import': FuncionalidadeEnum.ADMIN.value,
        'prompt_template': FuncionalidadeEnum.GESTAO_PROMPTS.value,
        'prompt_evaluation': FuncionalidadeEnum.AVALIACAO_PROMPTS.value,
    }
    
    return mapping.get(prefix, FuncionalidadeEnum.OUTROS.value)


class MandatoStatusEnum(str, Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"


class RiskLevelEnum(str, Enum):
    OK = "ok"
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"


def calculate_risk_level(dias_sem_login: Optional[int]) -> str:
    """
    Calculate engagement risk based on days since last login.
    
    Rules:
        - None or 0-7 days: ok
        - 8-14 days: baixo
        - 15-21 days: medio
        - 22+ days: alto
    """
    if dias_sem_login is None:
        return RiskLevelEnum.ALTO.value  # Never logged in = high risk
    
    if dias_sem_login <= 7:
        return RiskLevelEnum.OK.value
    elif dias_sem_login <= 14:
        return RiskLevelEnum.BAIXO.value
    elif dias_sem_login <= 21:
        return RiskLevelEnum.MEDIO.value
    else:
        return RiskLevelEnum.ALTO.value
