from __future__ import annotations
from typing import Optional, List
from enum import Enum
from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Date,
    Table,
    Column,
    ForeignKey,
    Boolean,
    DateTime,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from .base import Base

import os
from dotenv import load_dotenv
load_dotenv()

EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

class PermissionLevelEnum(str, Enum):
    user = "User"
    admin = "Admin"
    manager = "Manager"
    invited = "Invited"


mandato_user_link = Table(
    "mandato_user_link",
    Base.metadata,
    Column("mandato_id", ForeignKey("mandatos.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    permission_level: Mapped[Optional[str]] = mapped_column(String(20))
    lgpd_check: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, server_default=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    acquisition_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    mandatos: Mapped[List[Mandato]] = relationship(
        "Mandato", secondary=mandato_user_link, back_populates="users"
    )
    tokens: Mapped[List[AuthToken]] = relationship("AuthToken", cascade="all, delete-orphan", back_populates="user")


class Mandato(Base):
    __tablename__ = "mandatos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_parlamentar: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    casa_legislativa: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cargo_parlamentar: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    partido: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    esfera: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    municipio: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ue: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    temas_interesse: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    perfil_parlamentar: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    espectro_politico: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    data: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # DEPRECATED: use created_at
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, server_default=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_login_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    slug: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True, index=True)
    profile_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    last_login_user: Mapped[Optional[User]] = relationship("User", foreign_keys=[last_login_user_id])

    users: Mapped[List[User]] = relationship(
        "User", secondary=mandato_user_link, back_populates="mandatos"
    )


class AuthToken(Base):
    __tablename__ = "auth_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="tokens")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship("User", backref="password_reset_tokens")


class UserActivationToken(Base):
    __tablename__ = "user_activation_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mandato_id: Mapped[int] = mapped_column(Integer, ForeignKey("mandatos.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship("User", backref="activation_tokens")
    mandato: Mapped[Mandato] = relationship("Mandato", backref="activation_tokens")


class ProjetoReferencia(Base):
    __tablename__ = "projetos_referencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    house: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    presentation_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    author: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    scraped_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    subject_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    actor_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    actor_mandato_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    actor_permission_level: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mandato_id: Mapped[int] = mapped_column(Integer, ForeignKey("mandatos.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    upload_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Embedding support
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=True)
    has_embeddings: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Relationships
    mandato: Mapped[Mandato] = relationship("Mandato", backref="files")
    user: Mapped[User] = relationship("User", backref="files")
    chunks: Mapped[List[FileChunk]] = relationship("FileChunk", back_populates="file", cascade="all, delete-orphan")


class FileChunk(Base):
    __tablename__ = "file_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    file: Mapped[File] = relationship("File", back_populates="chunks")


class VectorImportJobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VectorImportJob(Base):
    __tablename__ = "vector_import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=VectorImportJobStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    processed_chunks: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    user: Mapped[Optional[User]] = relationship("User", backref="import_jobs")


class PromptTemplate(Base):
    """Versioned storage for LLM prompt templates with admin customization"""
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    creator: Mapped[Optional[User]] = relationship("User", foreign_keys=[created_by], backref="created_templates")


class PromptEvaluationCase(Base):
    """Test cases for prompt evaluation with input/expected output"""
    __tablename__ = "prompt_evaluation_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    test_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    creator: Mapped[Optional[User]] = relationship("User", foreign_keys=[created_by], backref="evaluation_cases")
    results: Mapped[List[PromptEvaluationResult]] = relationship("PromptEvaluationResult", back_populates="case", cascade="all, delete-orphan")


class PromptEvaluationRun(Base):
    """Execution metadata for batch evaluation runs"""
    __tablename__ = "prompt_evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    executed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default='running', index=True)
    mandato_ids: Mapped[Optional[list]] = mapped_column(ARRAY(Integer), nullable=True)
    template_ids: Mapped[Optional[list]] = mapped_column(ARRAY(Integer), nullable=True)

    executor: Mapped[Optional[User]] = relationship("User", foreign_keys=[executed_by], backref="evaluation_runs")
    template: Mapped[Optional[PromptTemplate]] = relationship("PromptTemplate", foreign_keys=[template_id], backref="evaluation_runs")
    results: Mapped[List[PromptEvaluationResult]] = relationship("PromptEvaluationResult", back_populates="run", cascade="all, delete-orphan")


class PromptEvaluationResult(Base):
    """Individual test results with LLM and human evaluation"""
    __tablename__ = "prompt_evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("prompt_evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("prompt_evaluation_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    mandato_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mandatos.id"), nullable=True, index=True)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("prompt_templates.id"), nullable=True, index=True)
    actual_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    llm_evaluation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    llm_evaluation_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_evaluation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    run: Mapped[PromptEvaluationRun] = relationship("PromptEvaluationRun", back_populates="results")
    case: Mapped[PromptEvaluationCase] = relationship("PromptEvaluationCase", back_populates="results")
    mandato: Mapped[Optional[Mandato]] = relationship("Mandato", foreign_keys=[mandato_id])
    template: Mapped[Optional[PromptTemplate]] = relationship("PromptTemplate", foreign_keys=[template_id])


class AnalyticsMetric(Base):
    """Pre-calculated metrics for mandatos and users"""
    __tablename__ = "analytics_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Scope
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 'mandato' or 'user'
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Time window
    reference_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Status
    status: Mapped[Optional[str]] = mapped_column(String(20))  # 'ativo', 'inativo'
    risk_level: Mapped[Optional[str]] = mapped_column(String(20))  # 'ok', 'baixo', 'medio', 'alto'

    # Activity
    ultimo_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    dias_sem_login: Mapped[Optional[int]] = mapped_column(Integer)
    logs_7d: Mapped[int] = mapped_column(Integer, default=0)
    logs_30d: Mapped[int] = mapped_column(Integer, default=0)
    logs_total: Mapped[int] = mapped_column(Integer, default=0)

    # Funcionalidades breakdown
    funcionalidades_count: Mapped[Optional[dict]] = mapped_column(JSONB)


class ColetaDemandasContact(Base):
    __tablename__ = "coleta_demandas_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mandato_id = Column(Integer, ForeignKey("mandatos.id"), nullable=False, index=True)
    nome_completo = Column(String(255), nullable=False)
    telefone_normalizado = Column(String(20), nullable=False)
    telefone_exibicao = Column(String(30), nullable=False)
    bairro = Column(String(120), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    mandato = relationship("Mandato", backref="coleta_demandas_contacts")


class ColetaDemanda(Base):
    __tablename__ = "coleta_demandas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mandato_id = Column(Integer, ForeignKey("mandatos.id"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("coleta_demandas_contacts.id"), nullable=True, index=True)

    descricao = Column(Text, nullable=False)
    endereco = Column(String(255), nullable=True)
    nao_sei_endereco = Column(Boolean, nullable=False, default=False)
    ponto_referencia = Column(String(255), nullable=True)

    nome_completo = Column(String(255), nullable=False)
    telefone_normalizado = Column(String(20), nullable=False, index=True)
    telefone_exibicao = Column(String(30), nullable=False)
    bairro = Column(String(120), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    nome_responsavel = Column(String(255), nullable=True)
    telefone_responsavel = Column(String(30), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    mandato = relationship("Mandato", backref="coleta_demandas")
    contact = relationship("ColetaDemandasContact", backref="demandas")
    anexos = relationship("ColetaDemandaAttachment", back_populates="demanda", cascade="all, delete-orphan")


class ColetaDemandaAttachment(Base):
    __tablename__ = "coleta_demandas_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    demanda_id = Column(Integer, ForeignKey("coleta_demandas.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    size_bytes = Column(BigInteger, nullable=False)
    storage_path = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    demanda = relationship("ColetaDemanda", back_populates="anexos")


class ColetaDemandaTriagem(Base):
    __tablename__ = "coleta_demandas_triagem"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mandato_id = Column(Integer, ForeignKey("mandatos.id"), nullable=False, index=True)
    coleta_demanda_id = Column(Integer, ForeignKey("coleta_demandas.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    tipo = Column(String(50), nullable=True, index=True)
    categoria = Column(String(50), nullable=True, index=True)

    descricao_original = Column(Text, nullable=False)
    descricao_processada = Column(Text, nullable=True)
    descricao_embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=True)

    local_texto = Column(Text, nullable=True)

    origem = Column(Text, nullable=True)

    solicitante_nome = Column(Text, nullable=True)
    solicitante_email = Column(Text, nullable=True)
    solicitante_telefone = Column(Text, nullable=True)

    mandato = relationship("Mandato", backref="coleta_demandas_triagem")
    coleta_demanda = relationship("ColetaDemanda", backref="triagens")
