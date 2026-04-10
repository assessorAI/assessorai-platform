from __future__ import annotations

from fastapi import Form, Depends, HTTPException
from pydantic import BaseModel, ValidationError, Field, EmailStr, field_validator, ConfigDict
from enum import Enum
from typing import Type, List, Optional, Dict, Literal, Any
import inspect
from datetime import datetime
import re
from .utils.config import load_mandato_cargos

class ContextItem(BaseModel):
    type: Literal['text', 'file', 'reference']
    content: str = Field(..., description="Texto, base64 (file) ou ref_id (reference)")

def form_factory(model: Type[BaseModel], **overrides):
    model_fields = model.model_fields

    def as_form(**data):
        try:
            return model(**data)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors(include_context=False, include_url=False))

    params = []

    for field_name, field_info in model_fields.items():
        annotation = field_info.annotation
        default = field_info.default
        description = field_info.description or None
        examples = field_info.examples or None
        
        # Apply overrides for this field if they exist
        field_overrides = overrides.get(field_name, {})
        if isinstance(field_overrides, dict):
            if 'description' in field_overrides:
                description = field_overrides['description']
            if 'examples' in field_overrides:
                examples = field_overrides['examples']
        
        form_param = Form(default, description=description, examples=examples)
        param = inspect.Parameter(
            field_name,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=form_param,
            annotation=annotation
        )
        params.append(param)

    sig = inspect.Signature(parameters=params)
    as_form.__signature__ = sig  # type: ignore[attr-defined]
    return Depends(as_form)

class BaseAPIModel(BaseModel):
    nome_parlamentar: Optional[str] = Field(
        None,
        description="Nome do parlamentar",
        examples=["Marina Bragante"],
        max_length=100
    )
    casa_legislativa: Optional[str] = Field(
        None,
        description="Casa Legislativa do parlamentar",
        examples=["Câmara Municipal de São Paulo"],
        max_length=100
    )
    municipio: Optional[str] = Field(
        None,
        description="Município do Parlamentar",
        examples=["São Paulo"],
        max_length=100
    )
    ue: Optional[str] = Field(
        None,
        description="Unidade da Federação",
        examples=["SP"],
        max_length=2
    )
    cargo_parlamentar: Optional[str] = Field(
        None,
        description="Cargo ocupado no mandato",
        examples=["Vereador"],
        max_length=100
    )
    partido: Optional[str] = Field(
        None,
        description="Partido político do parlamentar",
        examples=["PSOL"],
        max_length=100
    )
    temas_interesse: Optional[str] = Field(
        None,
        description="Temas de interesse do parlamentar",
        examples=["Educação,Saúde"]
    )
    perfil_parlamentar: Optional[str] = Field(
        None,
        description="Perfil do parlamentar",
        examples=["Progressista"]
    )
    espectro_politico: Optional[str] = Field(
        None,
        description="Espectro político do parlamentar",
        examples=["Centro Esquerda"]
    )
    data: Optional[str] = Field(
        datetime.now().strftime("%d/%m/%Y"),
        description="Data da requisição (dd/mm/aaaa)"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Data de criação do mandato"
    )
    slug: Optional[str] = Field(
        None,
        description="Identificador único amigável para URL, gerado automaticamente a partir do nome_parlamentar",
        max_length=120,
    )
    profile_image_url: Optional[str] = Field(
        None,
        description="Path relativo ao endpoint de imagem de perfil",
    )

    @field_validator("cargo_parlamentar")
    @classmethod
    def validate_cargo_parlamentar(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = load_mandato_cargos()
        if value not in allowed:
            raise ValueError(f"cargo_parlamentar inválido. Valores permitidos: {', '.join(allowed)}")
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome_parlamentar": "Marina Bragante",
                "casa_legislativa": "Câmara Municipal de São Paulo",
                "municipio": "São Paulo",
                "ue": "SP",
                "cargo_parlamentar": "Vereador",
                "partido": "PSOL",
                "temas_interesse": "Educação,Saúde",
                "perfil_parlamentar": "Progressista",
                "espectro_politico": "Centro Esquerda",
                "data": datetime.now().strftime("%d/%m/%Y")
            }
        }
    )



class BaseStructuredAnswer(BaseModel):
    """Base structured JSON Answer"""
    response: str = Field(description="The whole response text")

# User model and permissions
class PermissionLevel(str, Enum):
    user = "User"
    admin = "Admin"
    manager = "Manager"
    invited = "Invited"

class User(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="User first name", max_length=50)
    last_name: Optional[str] = Field(None, description="User last name", max_length=50)
    phone: Optional[str] = Field(None, description="User phone number", examples=["(11) 99999-9999"])
    permission_level: PermissionLevel = Field(..., description="User permission level")
    lgpd_check: bool = Field(..., description="LGPD acceptance consent")
    role: Optional[str] = Field(None, description="User role")
    is_active: bool = Field(True, description="Indicates if the user account is active")
    created_at: Optional[datetime] = Field(None, description="Data de criação do usuário")
    acquisition_data: Optional[Dict[str, Any]] = Field(None, description="Query parameters capturados durante o registro (UTM, etc)")


class UserOut(User):
    id: Optional[int] = Field(None, description="User ID")
    last_login: Optional[datetime] = Field(None, description="Data do último login")
    mandato: List["MandatoOut"] = Field(
        default_factory=list,
        description="Mandatos associados ao usuário",
    )


class UserMeOut(User):
    id: Optional[int] = Field(None, description="User ID")
    last_login: Optional[datetime] = Field(None, description="Data do último login")
    casa_legislativa: Optional[str] = Field(None, description="Casa legislativa do mandato associado")
    municipio: Optional[str] = Field(None, description="Município do mandato associado")
    ue: Optional[str] = Field(None, description="UF do mandato associado")
    cargo_parlamentar: Optional[str] = Field(None, description="Cargo do mandato associado")
    mandato: List["MandatoOut"] = Field(
        default_factory=list,
        description="Mandatos associados ao usuário autenticado",
    )


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expiration_date: datetime


# Mandato model: extends BaseAPIModel and links to multiple users
class Mandato(BaseAPIModel):
    id: Optional[int] = Field(None, description="Mandato ID")
    users: List[User] = Field(default_factory=list, description="Users associated with this Mandato")


class MandatoOut(BaseAPIModel):
    id: Optional[int] = Field(None, description="Mandato ID")
    users: List[int] = Field(default_factory=list, description="IDs dos usuários associados ao Mandato")


class MandatoGerenteOut(BaseModel):
    id: int = Field(..., description="ID do usuário")
    nome: Optional[str] = Field(None, description="Nome completo")
    email: EmailStr = Field(..., description="Email")


class MandatoLastLoginOut(BaseModel):
    email: EmailStr = Field(..., description="Email do último usuário que fez login")
    date: datetime = Field(..., description="Data do último login")


class MandatoListOut(MandatoOut):
    gerente: List[MandatoGerenteOut] = Field(
        default_factory=list,
        description="Usuários do mandato com permissão Manager/Admin",
    )
    last_login: Optional[MandatoLastLoginOut] = Field(
        None,
        description="Último login dentre usuários associados ao mandato",
    )
    numero_atividades: Optional[int] = Field(
        None,
        description="Número de atividades (audit logs) nos últimos 30 dias, excluindo login",
    )


# Emendas

class TipoEmenda(str, Enum):
    aditiva = "aditiva"
    modificativa = "modificativa"
    supressiva = "supressiva"

class Emenda(BaseModel):
    art: int = Field(..., description="Número do artigo modificado, acrescentado ou suprimido")
    tipo: TipoEmenda = Field(..., description="Tipo da emenda: aditiva, modificativa ou supressiva")
    texto: str = Field(..., description="Uma linha explicando o sentido geral da emenda")

class EmendaCompleta(Emenda):
    texto: str = Field(..., description="Texto completo da emenda")
    justificativa: str = Field(..., description="Justificativa da emenda")

class EmendasOneLiner(BaseModel):
    emendas: List[Emenda] = Field(..., description="Lista de emendas")


# Constitucionalidade - um modelo para análise de constitucionalidade: parecer: favoravel, contrário, contrário com ressalvas, favorável com ressalvas ; gravidade: grave, média, leve ; artigos destacados: lista de artigos do projeto que são problemáticos ; justificativa: texto explicando a análise

class TiposParecer(str, Enum):
    favoravel = "Favorável"
    contrario = "Contrário"
    favoravel_com_ressalvas = "Favorável com ressalvas"

class Gravidade(str, Enum):
    grave = "grave"
    media = "média"
    leve = "leve"

class ParecerConstitucional(BaseModel):
    parecer: TiposParecer = Field(..., description="Orientação do parecer sobre a constitucionalidade do projeto")
    gravidade: Optional[Gravidade] = Field(None, description="Gravidade do problema")
    artigos_destacados: List[int] = Field(..., description="Lista de artigos do projeto que são problemáticos")
    justificativa: str = Field(..., description="Explicação detalhada para análise")
    sugestao: Optional[str] = Field(None, description="Sugestão de correção")


# Projetos de lei

class SimpleText(BaseModel):
    text: str = Field(..., description="Texto de entrada")

class ProjetoLei(BaseModel):
    titulo: str = Field(..., description="Título do projeto de lei")
    ementa: str = Field(..., description="Ementa do projeto de lei")
    texto: str = Field(..., description="Texto integral do projeto de lei")
    justificativa: str = Field(..., description="Justificativa do projeto de lei")


# Password Reset

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail do usuário para recuperação de senha")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Token de recuperação recebido por e-mail", min_length=32)
    new_password: str = Field(..., description="Nova senha do usuário", min_length=8)


class MessageResponse(BaseModel):
    message: str = Field(..., description="Mensagem de resposta")


class ColetaDemandasCreateResponse(MessageResponse):
    contact_token: Optional[str] = Field(
        None,
        description="Token opaco para reaproveitar dados de identificacao em novas demandas",
    )


class ColetaDemandasUserOut(BaseModel):
    id: str = Field(..., description="Identificador opaco do contato")
    nome_completo: str
    telefone: str
    bairro: str
    data_nascimento: str = Field(..., description="Formato DD/MM/AAAA")


class ColetaDemandasValidateResponse(BaseModel):
    user: ColetaDemandasUserOut


class ColetaDemandaCreateIn(BaseModel):
    descricao: str = Field(..., min_length=10, max_length=1000)
    endereco: Optional[str] = Field(None, max_length=255)
    ponto_referencia: Optional[str] = Field(None, max_length=255)
    nome_completo: Optional[str] = Field(None, min_length=3, max_length=255)
    telefone: Optional[str] = Field(None, min_length=10, max_length=20)
    bairro: Optional[str] = Field(None, min_length=3, max_length=120)
    data_nascimento: Optional[str] = Field(None, description="Formato DD/MM/AAAA")
    contact_token: Optional[str] = Field(None)

    @field_validator("data_nascimento")
    @classmethod
    def validate_data_nascimento(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return value
        try:
            datetime.strptime(value.strip(), "%d/%m/%Y")
        except ValueError as exc:
            raise ValueError("data_nascimento deve estar no formato DD/MM/AAAA") from exc
        return value.strip()

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return value
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10 or len(digits) > 13:
            raise ValueError("telefone invalido")
        return value.strip()


class ColetaDemandaTipo(str, Enum):
    solicitacao = "solicitacao"
    denuncia = "denuncia"
    reclamacao = "reclamacao"
    sugestao = "sugestao"
    elogio = "elogio"
    outro = "outro"


class ColetaDemandaCategoria(str, Enum):
    saude = "saude"
    educacao = "educacao"
    seguranca = "seguranca"
    infraestrutura = "infraestrutura"
    transporte = "transporte"
    meio_ambiente = "meio_ambiente"
    assistencia_social = "assistencia_social"
    cultura = "cultura"
    esporte = "esporte"
    outro = "outro"


class ColetaDemandaTriagemExtractRequest(BaseModel):
    mandato_id: int = Field(..., ge=1)
    descricao_original: str = Field(..., min_length=1)
    local_texto: Optional[str] = None
    solicitante_nome: Optional[str] = None
    solicitante_email: Optional[EmailStr] = None
    solicitante_telefone: Optional[str] = None


class ColetaDemandaTriagemBase(BaseModel):
    mandato_id: int = Field(..., ge=1)
    coleta_demanda_id: Optional[int] = Field(None, ge=1)
    descricao_original: str = Field(..., min_length=1)
    descricao_processada: Optional[str] = None
    local_texto: Optional[str] = None
    origem: Optional[str] = None
    solicitante_nome: Optional[str] = None
    solicitante_email: Optional[EmailStr] = None
    solicitante_telefone: Optional[str] = None


class ColetaDemandaTriagemCreate(ColetaDemandaTriagemBase):
    tipo: Optional[ColetaDemandaTipo] = None
    categoria: Optional[ColetaDemandaCategoria] = None


class ColetaDemandaTriagemUpdate(BaseModel):
    tipo: Optional[ColetaDemandaTipo] = None
    categoria: Optional[ColetaDemandaCategoria] = None
    descricao_original: Optional[str] = None
    descricao_processada: Optional[str] = None
    local_texto: Optional[str] = None
    origem: Optional[str] = None
    solicitante_nome: Optional[str] = None
    solicitante_email: Optional[EmailStr] = None
    solicitante_telefone: Optional[str] = None


class ColetaDemandaTriagemOut(BaseModel):
    id: int
    mandato_id: int
    coleta_demanda_id: Optional[int] = None
    created_at: datetime
    tipo: Optional[ColetaDemandaTipo] = None
    categoria: Optional[ColetaDemandaCategoria] = None
    descricao_original: str
    descricao_processada: Optional[str] = None
    local_texto: Optional[str] = None
    origem: Optional[str] = None
    solicitante_nome: Optional[str] = None
    solicitante_email: Optional[EmailStr] = None
    solicitante_telefone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ColetaDemandaTriagemExtraction(BaseModel):
    tipo: ColetaDemandaTipo
    categoria: ColetaDemandaCategoria
    descricao_processada: str
    local_texto: Optional[str] = None
    solicitante_nome: Optional[str] = None
    solicitante_email: Optional[str] = None
    solicitante_telefone: Optional[str] = None


class ColetaDemandaTriagemExtractionDraft(BaseModel):
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    descricao_processada: Optional[str] = None
    local_texto: Optional[str] = None
    solicitante_nome: Optional[str] = None
    solicitante_email: Optional[str] = None
    solicitante_telefone: Optional[str] = None


# User Activation

class ActivateUserRequest(BaseModel):
    token: str = Field(..., description="Token de ativação recebido por e-mail", min_length=32)
    first_name: str = Field(..., description="Nome do usuário", max_length=50)
    last_name: str = Field(..., description="Sobrenome do usuário", max_length=50)
    phone: str = Field(..., description="Telefone do usuário", examples=["(11) 99999-9999"])
    password: str = Field(..., description="Senha do usuário", min_length=8)
    lgpd_check: bool = Field(..., description="Aceite dos termos LGPD")
    role: str = Field(..., description="Cargo/função do usuário", max_length=50)


class ActivateUserTokenResponse(BaseModel):
    email: EmailStr = Field(..., description="E-mail do usuário a ser ativado")
    mandato_nome: Optional[str] = Field(None, description="Nome do mandato ao qual o usuário foi convidado")


class AdminUserMetrics(BaseModel):
    total: int
    active: int
    inactive: int
    by_permission: Dict[str, int] = Field(default_factory=dict)


class AdminMandatoMetrics(BaseModel):
    total: int
    with_users: int
    without_users: int


class AdminTokenMetrics(BaseModel):
    active: int
    expiring_within_24h: int


class AdminDashboardSummary(BaseModel):
    users: AdminUserMetrics
    mandatos: AdminMandatoMetrics
    tokens: AdminTokenMetrics
    pending_invitations: int = Field(0, description="Number of pending user invitations")


class AdminHealthCheck(BaseModel):
    name: str
    status: Literal["ok", "warning", "error"]
    detail: Optional[str] = None
    data: Optional[Dict[str, List[str]]] = None


class AdminHealthResponse(BaseModel):
    overall_status: Literal["ok", "warning", "error"]
    checks: List[AdminHealthCheck]


class AuditEvent(BaseModel):
    event_type: str = Field(..., description="Categoria do evento, ex: oficio.generated")
    subject_id: Optional[str] = Field(None, description="Identificador do recurso afetado")
    actor_user_id: Optional[int] = Field(None, description="Usuário que originou o evento")
    actor_mandato_id: Optional[int] = Field(None, description="Mandato associado ao usuário no momento")
    actor_permission_level: Optional[str] = Field(None, description="Permissão do usuário ao disparar o evento")
    request_id: Optional[str] = Field(None, description="Identificador da requisição correlacionada")
    payload: Optional[Dict[str, object]] = Field(None, description="Metadados adicionais do evento")
    notes: Optional[str] = Field(None, description="Observações livres")


class AuditLogOut(AuditEvent):
    id: int
    created_at: datetime
    response: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


UserOut.model_rebuild()
UserMeOut.model_rebuild()


# Analytics Response Models

class AnalyticsMandatoBasic(BaseModel):
    """Basic mandato info for analytics"""
    id: int
    nome_parlamentar: Optional[str]
    cargo_parlamentar: Optional[str]
    ue: Optional[str]
    created_at: Optional[datetime]


class AnalyticsMandatoMetrics(BaseModel):
    """Individual mandato metrics"""
    mandato: AnalyticsMandatoBasic
    status: str  # 'ativo' or 'inativo'
    risk_level: str  # 'ok', 'baixo', 'medio', 'alto'
    ultimo_login: Optional[datetime]
    dias_sem_login: Optional[int]
    logs_7d: int
    logs_30d: int
    funcionalidades: Dict[str, int]


class AnalyticsUserMetricsOut(BaseModel):
    """Individual user metrics"""
    user_id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    status: str
    risk_level: str
    ultimo_login: Optional[datetime]
    dias_sem_login: Optional[int]
    logs_7d: int
    logs_30d: int
    funcionalidades: Dict[str, int]


class AnalyticsSummaryMandatos(BaseModel):
    """Aggregate summary of all mandatos"""
    total: int
    ativos: int
    inativos: int
    taxa_retencao: float
    
    # Breakdowns
    por_cargo: Dict[str, int]
    por_uf: Dict[str, int]
    por_perfil: Dict[str, int]
    por_espectro: Dict[str, int]
    
    # Risk distribution
    por_risco: Dict[str, int]  # {"ok": 10, "baixo": 5, ...}


class AnalyticsTimelineBucket(BaseModel):
    """Single time period data point"""
    period: str  # "2025-01" or "2025-W01"
    count: int
    ativos: Optional[int] = None


class AnalyticsTimeline(BaseModel):
    """Timeline of mandato registrations or activity"""
    timeline: List[AnalyticsTimelineBucket]


class AnalyticsFuncionalidadeUso(BaseModel):
    """Usage by funcionalidade"""
    funcionalidade: str
    count: int
    percentage: float


class AnalyticsFuncionalidadesResponse(BaseModel):
    """Breakdown of feature usage"""
    total_logs: int
    funcionalidades: List[AnalyticsFuncionalidadeUso]


class AnalyticsEngagementList(BaseModel):
    """List of mandatos with engagement metrics"""
    mandatos: List[AnalyticsMandatoMetrics]
    total: int


# ============================================================================
# Prompt Template Management Models
# ============================================================================

class PromptTemplateBase(BaseModel):
    """Base schema for prompt templates"""
    template_type: str = Field(..., description="Tipo do template (ex: generate_oficio, expert_pl_constitucionalidade)")
    content: str = Field(..., description="Conteúdo do template em Markdown/Mustache")
    description: Optional[str] = Field(None, description="Descrição da versão ou alterações realizadas")


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a new prompt template version"""
    pass


class PromptTemplateUpdate(BaseModel):
    """Schema for updating template metadata (not content - create new version for that)"""
    content: Optional[str] = Field(None, description="Conteúdo atualizado do template")
    description: Optional[str] = Field(None, description="Descrição atualizada")
    is_active: Optional[bool] = Field(None, description="Ativar/desativar template")


class PromptTemplate(PromptTemplateBase):
    """Full prompt template schema with metadata"""
    id: int
    version: int
    is_default: bool
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class PromptTemplateListItem(BaseModel):
    """Lightweight schema for listing templates"""
    id: int
    template_type: str
    version: int
    is_default: bool
    is_active: bool
    created_at: datetime
    description: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class PromptTemplateType(BaseModel):
    """Metadata about a template type"""
    type: str = Field(..., description="Identificador do tipo (ex: generate_oficio)")
    display_name: str = Field(..., description="Nome amigável para exibição")
    file_exists: bool = Field(..., description="Se existe arquivo .md para fallback")
    db_versions_count: int = Field(..., description="Número de versões no banco de dados")
    default_version: Optional[int] = Field(None, description="Versão marcada como default")
    has_active_default: bool = Field(False, description="Se existe uma versão default ativa")


class PromptTemplateFileContent(BaseModel):
    """Content from file-based template"""
    template_type: str
    content: str
    source: Literal["file"] = "file"


# ==================== Prompt Evaluation Models ====================

class PromptEvaluationCaseBase(BaseModel):
    """Base model for prompt evaluation test cases"""
    name: str = Field(..., max_length=200, description="Nome descritivo do caso de teste")
    test_type: str = Field(..., description="Tipo de teste (oficio, criar_projeto_pl, etc)")
    input_data: dict = Field(..., description="Dados de entrada no formato JSON")
    expected_output: Optional[str] = Field(None, description="Saída esperada para comparação")

class PromptEvaluationCaseCreate(PromptEvaluationCaseBase):
    """Model for creating a new evaluation case"""
    pass

class PromptEvaluationCaseUpdate(BaseModel):
    """Model for updating an evaluation case"""
    name: Optional[str] = Field(None, max_length=200)
    test_type: Optional[str] = None
    input_data: Optional[dict] = None
    expected_output: Optional[str] = None
    is_active: Optional[bool] = None

class PromptEvaluationCase(PromptEvaluationCaseBase):
    """Full evaluation case model"""
    id: int
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PromptEvaluationRunCreate(BaseModel):
    """Model for creating a new evaluation run"""
    run_name: Optional[str] = Field(None, max_length=200, description="Nome opcional para esta execução")
    template_id: Optional[int] = Field(None, description="ID do template a ser testado (None = usar default)")
    case_ids: List[int] = Field(..., min_length=1, description="IDs dos casos de teste a executar")
    mandato_ids: List[int] = Field(..., min_length=1, description="IDs dos mandatos para testar")
    template_ids: List[Optional[int]] = Field(..., min_length=1, description="IDs dos templates para testar (None = usar default)")
    templates_by_type: Optional[dict] = Field(None, description="Map de test_type -> template_ids para casos com múltiplos tipos")

class PromptEvaluationRunUpdate(BaseModel):
    """Model for updating run status"""
    status: Optional[str] = Field(None, description="Status: running, completed, failed, cancelled")
    completed_cases: Optional[int] = None

class PromptEvaluationRun(BaseModel):
    """Full evaluation run model"""
    id: int
    run_name: Optional[str]
    template_id: Optional[int]
    executed_by: Optional[int]
    executed_at: datetime
    total_cases: int
    completed_cases: int
    status: str
    mandato_ids: Optional[List[int]] = None
    template_ids: Optional[List[Optional[int]]] = None
    
    class Config:
        from_attributes = True


class PromptEvaluationResultCreate(BaseModel):
    """Model for creating an evaluation result"""
    run_id: int
    case_id: int
    mandato_id: Optional[int] = None
    template_id: Optional[int] = None
    actual_output: Optional[str] = None
    execution_time_ms: Optional[int] = None
    llm_evaluation_score: Optional[int] = Field(None, ge=0, le=100)
    llm_evaluation_analysis: Optional[str] = None
    error_message: Optional[str] = None

class PromptEvaluationResultUpdate(BaseModel):
    """Model for updating result (mainly for human evaluation)"""
    human_evaluation: Optional[str] = None
    llm_evaluation_score: Optional[int] = Field(None, ge=0, le=100)
    llm_evaluation_analysis: Optional[str] = None

class PromptEvaluationResult(BaseModel):
    """Full evaluation result model"""
    id: int
    run_id: int
    case_id: int
    mandato_id: Optional[int] = None
    template_id: Optional[int] = None
    actual_output: Optional[str]
    execution_time_ms: Optional[int]
    llm_evaluation_score: Optional[int]
    llm_evaluation_analysis: Optional[str]
    human_evaluation: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PromptEvaluationResultDetail(PromptEvaluationResult):
    """Extended result model with case and run details"""
    case_name: str
    case_test_type: str
    case_input_data: dict
    case_expected_output: Optional[str]
    run_name: Optional[str]
    template_version: Optional[int]
    template_type: Optional[str]
    mandato_nome: Optional[str] = None
    template_description: Optional[str] = None
