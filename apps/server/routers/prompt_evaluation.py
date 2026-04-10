from __future__ import annotations

import csv
import io
import json
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload

from ..db.models import (
    PromptEvaluationCase as PromptEvaluationCaseORM,
    PromptEvaluationRun as PromptEvaluationRunORM,
    PromptEvaluationResult as PromptEvaluationResultORM,
    PromptTemplate as PromptTemplateORM,
    User as UserORM,
)
from ..db.session import get_session
from ..models import (
    PromptEvaluationCase,
    PromptEvaluationCaseCreate,
    PromptEvaluationCaseUpdate,
    PromptEvaluationRun,
    PromptEvaluationRunCreate,
    PromptEvaluationRunUpdate,
    PromptEvaluationResult,
    PromptEvaluationResultCreate,
    PromptEvaluationResultUpdate,
    PromptEvaluationResultDetail,
)
from ..routers.deps import require_admin_user, get_current_user
from ..services.audit import AuditLogger, get_audit_logger
from ..llm import call_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/prompt-evaluation", tags=["admin/prompt-evaluation"])

# Valid test types mapping to endpoints
VALID_TEST_TYPES = {
    "oficio": "generate_oficio",
    "criar_projeto_pl": "expert_pl_sugestao_projetos",
    "constitucionalidade": "expert_pl_constitucionalidade",
    "criar_emenda": "expert_pl_criar_emenda",
    "sugestao_emendas": "expert_pl_sugestao_emendas",
    "sugestao_projetos": "expert_pl_sugestao_projetos",
}


# ==================== Evaluation Cases CRUD ====================

@router.post("/cases", response_model=PromptEvaluationCase, status_code=201)
async def create_evaluation_case(
    *,
    session: Session = Depends(get_session),
    case_in: PromptEvaluationCaseCreate,
    current_user: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> PromptEvaluationCase:
    """Create a new evaluation test case"""
    
    # Validate test_type
    if case_in.test_type not in VALID_TEST_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid test_type. Must be one of: {', '.join(VALID_TEST_TYPES.keys())}"
        )
    
    case_orm = PromptEvaluationCaseORM(
        name=case_in.name,
        test_type=case_in.test_type,
        input_data=case_in.input_data,
        expected_output=case_in.expected_output,
        created_by=current_user.id,
    )
    
    session.add(case_orm)
    session.commit()
    session.refresh(case_orm)
    
    audit.log(
        event_type="prompt_evaluation_case_created",
        payload={"case_id": case_orm.id, "name": case_orm.name, "test_type": case_orm.test_type},
        actor_user_id=current_user.id,
    )
    
    return PromptEvaluationCase.model_validate(case_orm)


@router.get("/cases", response_model=List[PromptEvaluationCase])
async def list_evaluation_cases(
    *,
    session: Session = Depends(get_session),
    current_user: UserORM = require_admin_user,
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    is_active: bool = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> List[PromptEvaluationCase]:
    """List evaluation test cases with optional filtering"""
    
    query = select(PromptEvaluationCaseORM)
    
    if test_type:
        query = query.where(PromptEvaluationCaseORM.test_type == test_type)
    
    query = query.where(PromptEvaluationCaseORM.is_active == is_active)
    query = query.order_by(PromptEvaluationCaseORM.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = session.execute(query)
    cases = result.scalars().all()
    
    return [PromptEvaluationCase.model_validate(case) for case in cases]


# ==================== CSV Import/Export ====================

@router.post("/cases/import-csv", response_model=dict)
async def import_cases_from_csv(
    *,
    session: Session = Depends(get_session),
    file: UploadFile = File(...),
    current_user: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict:
    """Import evaluation cases from CSV file
    
    CSV format: name,test_type,input_text,orgao_destino,remetente,expected_output
    """
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    csv_text = content.decode('utf-8-sig')  # Handle BOM
    csv_reader = csv.DictReader(io.StringIO(csv_text))
    
    imported_count = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
        try:
            # Build input_data based on test_type
            test_type = row.get('test_type', '').strip()
            
            if test_type not in VALID_TEST_TYPES:
                errors.append(f"Row {row_num}: Invalid test_type '{test_type}'")
                continue
            
            input_data = {}
            if test_type == 'oficio':
                input_data = {
                    "input_text": row.get('input_text', ''),
                    "orgao_destino": row.get('orgao_destino', ''),
                    "remetente": row.get('remetente', ''),
                }
            else:
                # For other types, store input_text as the main content
                input_data = {"input_text": row.get('input_text', '')}
            
            case_orm = PromptEvaluationCaseORM(
                name=row.get('name', '').strip(),
                test_type=test_type,
                input_data=input_data,
                expected_output=row.get('expected_output', '').strip() or None,
                created_by=current_user.id,
            )
            
            session.add(case_orm)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    if imported_count > 0:
        session.commit()
    
    audit.log(
        event_type="prompt_evaluation_cases_imported",
        payload={"imported_count": imported_count, "error_count": len(errors)},
        actor_user_id=current_user.id,
    )
    
    return {
        "imported_count": imported_count,
        "error_count": len(errors),
        "errors": errors[:10],  # Return first 10 errors
    }


@router.get("/cases/export-csv")
async def export_cases_to_csv(
    *,
    session: Session = Depends(get_session),
    current_user: UserORM = require_admin_user,
    test_type: Optional[str] = Query(None, description="Filter by test type"),
) -> StreamingResponse:
    """Export evaluation cases to CSV"""
    
    query = select(PromptEvaluationCaseORM).where(PromptEvaluationCaseORM.is_active == True)
    
    if test_type:
        query = query.where(PromptEvaluationCaseORM.test_type == test_type)
    
    result = session.execute(query)
    cases = result.scalars().all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['name', 'test_type', 'input_text', 'orgao_destino', 'remetente', 'expected_output'])
    writer.writeheader()
    
    for case in cases:
        row = {
            'name': case.name,
            'test_type': case.test_type,
            'input_text': case.input_data.get('input_text', ''),
            'orgao_destino': case.input_data.get('orgao_destino', ''),
            'remetente': case.input_data.get('remetente', ''),
            'expected_output': case.expected_output or '',
        }
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=evaluation_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/cases/{case_id}", response_model=PromptEvaluationCase)
async def get_evaluation_case(
    *,
    session: Session = Depends(get_session),
    case_id: int,
    current_user: UserORM = require_admin_user,
) -> PromptEvaluationCase:
    """Get a specific evaluation case by ID"""
    
    case = session.get(PromptEvaluationCaseORM, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Evaluation case not found")
    
    return PromptEvaluationCase.model_validate(case)


@router.patch("/cases/{case_id}", response_model=PromptEvaluationCase)
async def update_evaluation_case(
    *,
    session: Session = Depends(get_session),
    case_id: int,
    case_update: PromptEvaluationCaseUpdate,
    current_user: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> PromptEvaluationCase:
    """Update an evaluation case"""
    
    case = session.get(PromptEvaluationCaseORM, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Evaluation case not found")
    
    update_data = case_update.model_dump(exclude_unset=True)
    
    # Validate test_type if being updated
    if "test_type" in update_data and update_data["test_type"] not in VALID_TEST_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid test_type. Must be one of: {', '.join(VALID_TEST_TYPES.keys())}"
        )
    
    for field, value in update_data.items():
        setattr(case, field, value)
    
    case.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(case)
    
    audit.log(
        event_type="prompt_evaluation_case_updated",
        payload={"case_id": case_id, "updated_fields": list(update_data.keys())},
        actor_user_id=current_user.id,
    )
    
    return PromptEvaluationCase.model_validate(case)


@router.delete("/cases/{case_id}", status_code=204)
async def delete_evaluation_case(
    *,
    session: Session = Depends(get_session),
    case_id: int,
    current_user: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
    permanent: bool = Query(False, description="Permanently delete (true) or soft delete (false)"),
):
    """Delete an evaluation case (soft delete by default)"""
    
    case = session.get(PromptEvaluationCaseORM, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Evaluation case not found")
    
    if permanent:
        session.delete(case)
        event = "prompt_evaluation_case_deleted_permanent"
    else:
        case.is_active = False
        case.updated_at = datetime.now(timezone.utc)
        event = "prompt_evaluation_case_deleted_soft"
    
    session.commit()
    
    audit.log(
        event_type=event,
        payload={"case_id": case_id, "name": case.name},
        actor_user_id=current_user.id,
    )


# ==================== Evaluation Runs ====================

@router.post("/runs", response_model=PromptEvaluationRun, status_code=201)
async def create_evaluation_run(
    *,
    session: Session = Depends(get_session),
    run_in: PromptEvaluationRunCreate,
    current_user: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> PromptEvaluationRun:
    """Create a new evaluation run (will execute the tests)"""
    
    # Validate that all cases exist and are active
    cases_query = select(PromptEvaluationCaseORM).where(
        and_(
            PromptEvaluationCaseORM.id.in_(run_in.case_ids),
            PromptEvaluationCaseORM.is_active == True
        )
    )
    result = session.execute(cases_query)
    cases = result.scalars().all()
    
    if len(cases) != len(run_in.case_ids):
        raise HTTPException(status_code=400, detail="Some case IDs are invalid or inactive")
    
    # Validate mandatos
    from ..db.models import Mandato as MandatoORM
    mandatos_query = select(MandatoORM).where(MandatoORM.id.in_(run_in.mandato_ids))
    mandatos = session.execute(mandatos_query).scalars().all()
    if len(mandatos) != len(run_in.mandato_ids):
        raise HTTPException(status_code=400, detail="Some mandato IDs are invalid")
    
    # Validate templates (filter out None values for default template)
    non_null_template_ids = [tid for tid in run_in.template_ids if tid is not None]
    if non_null_template_ids:
        templates_query = select(PromptTemplateORM).where(PromptTemplateORM.id.in_(non_null_template_ids))
        templates = session.execute(templates_query).scalars().all()
        if len(templates) != len(non_null_template_ids):
            raise HTTPException(status_code=400, detail="Some template IDs are invalid")
    
    # Calculate total permutations
    if run_in.templates_by_type:
        # Calculate based on type-specific templates
        total_results = 0
        for case in cases:
            template_count = len(run_in.templates_by_type.get(case.test_type, run_in.template_ids))
            total_results += len(run_in.mandato_ids) * template_count
    else:
        # Simple calculation: cases × mandatos × templates
        total_results = len(cases) * len(run_in.mandato_ids) * len(run_in.template_ids)
    
    # Create run
    run_orm = PromptEvaluationRunORM(
        run_name=run_in.run_name,
        template_id=run_in.template_id,  # Legacy field - store first template
        executed_by=current_user.id,
        total_cases=total_results,
        status='pending',
        mandato_ids=run_in.mandato_ids,
        template_ids=run_in.template_ids,
    )
    
    session.add(run_orm)
    session.flush()  # Get the run_id without committing
    
    # Create placeholder results for each case × mandato × template permutation
    # If templates_by_type is provided, use type-specific templates for each case
    for case in cases:
        for mandato_id in run_in.mandato_ids:
            # Determine which templates to use for this case
            if run_in.templates_by_type and case.test_type in run_in.templates_by_type:
                # Use type-specific templates
                template_list = run_in.templates_by_type[case.test_type]
            else:
                # Fall back to flat template_ids list
                template_list = run_in.template_ids
            
            for template_id in template_list:
                result_orm = PromptEvaluationResultORM(
                    run_id=run_orm.id,
                    case_id=case.id,
                    mandato_id=mandato_id,
                    template_id=template_id,
                )
                session.add(result_orm)
    
    session.commit()
    session.refresh(run_orm)
    
    audit.log(
        event_type="prompt_evaluation_run_created",
        payload={
            "run_id": run_orm.id,
            "case_count": len(cases),
            "mandato_count": len(run_in.mandato_ids),
            "template_count": len(run_in.template_ids),
            "total_results": total_results,
        },
        actor_user_id=current_user.id,
    )
    
    return PromptEvaluationRun.model_validate(run_orm)


@router.get("/runs", response_model=List[PromptEvaluationRun])
async def list_evaluation_runs(
    *,
    session: Session = Depends(get_session),
    current_user: UserORM = require_admin_user,
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> List[PromptEvaluationRun]:
    """List evaluation runs"""
    
    query = select(PromptEvaluationRunORM)
    
    if status:
        query = query.where(PromptEvaluationRunORM.status == status)
    
    query = query.order_by(PromptEvaluationRunORM.executed_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = session.execute(query)
    runs = result.scalars().all()
    
    return [PromptEvaluationRun.model_validate(run) for run in runs]


@router.get("/runs/{run_id}", response_model=PromptEvaluationRun)
async def get_evaluation_run(
    *,
    session: Session = Depends(get_session),
    run_id: int,
    current_user: UserORM = require_admin_user,
) -> PromptEvaluationRun:
    """Get a specific evaluation run"""
    
    run = session.get(PromptEvaluationRunORM, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    
    return PromptEvaluationRun.model_validate(run)


@router.patch("/runs/{run_id}", response_model=PromptEvaluationRun)
async def update_evaluation_run(
    *,
    session: Session = Depends(get_session),
    run_id: int,
    run_update: PromptEvaluationRunUpdate,
    current_user: UserORM = require_admin_user,
) -> PromptEvaluationRun:
    """Update evaluation run status"""
    
    run = session.get(PromptEvaluationRunORM, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    
    update_data = run_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(run, field, value)
    
    session.commit()
    session.refresh(run)
    
    return PromptEvaluationRun.model_validate(run)


# ==================== Execute Tests ====================

def prepare_test_input(case: PromptEvaluationCaseORM, session: Session, mandato_id: int = None) -> dict:
    """Transform case.input_data into format expected by LLM prompts"""
    
    input_data = case.input_data.copy()
    test_type = case.test_type
    
    # Fetch mandato from parameter (new way) or from input_data (legacy)
    mandato_data = None
    if mandato_id:
        from ..db.models import Mandato as MandatoORM
        from ..models import Mandato as MandatoSchema
        
        mandato_obj = session.get(MandatoORM, mandato_id)
        if not mandato_obj:
            raise ValueError(f"Mandato ID {mandato_id} not found")
        
        mandato_schema = MandatoSchema.model_validate(mandato_obj, from_attributes=True)
        mandato_data = mandato_schema.model_dump()
    elif "mandato_id" in input_data:
        # Legacy: mandato_id stored in input_data
        from ..db.models import Mandato as MandatoORM
        from ..models import Mandato as MandatoSchema
        
        legacy_mandato_id = input_data.pop("mandato_id")
        mandato_obj = session.get(MandatoORM, legacy_mandato_id)
        if not mandato_obj:
            raise ValueError(f"Mandato ID {legacy_mandato_id} not found")
        
        mandato_schema = MandatoSchema.model_validate(mandato_obj, from_attributes=True)
        mandato_data = mandato_schema.model_dump()
    
    # Transform based on test type
    if test_type == "oficio":
        # Format: {'mandato': {...}, 'input': "...", 'orgao_destino': "...", 'remetente': "...", 'data': "..."}
        prepared = {
            'mandato': mandato_data,
            'input': input_data.get('input_text', ''),
            'data': datetime.now().isoformat(),
        }
        if 'orgao_destino' in input_data:
            prepared['orgao_destino'] = input_data['orgao_destino']
        if 'remetente' in input_data:
            prepared['remetente'] = input_data['remetente']
        elif mandato_data:
            prepared['remetente'] = mandato_data.get('nome_parlamentar', '')
        
        return prepared
    
    elif test_type in ["constitucionalidade", "sugestao_emendas", "criar_emenda"]:
        # Expert PL endpoints with file uploads
        prepared = {
            'mandato': mandato_data,
        }
        if 'origem_legislativa' in input_data:
            prepared['origem_legislativa'] = input_data['origem_legislativa']
        if 'input_text' in input_data:
            prepared['input'] = input_data['input_text']
        
        # Note: File handling would need special treatment in tests
        # For now, we'll include the file reference if present
        if 'file_uri' in input_data:
            prepared['file_uri'] = input_data['file_uri']
        
        return prepared
    
    elif test_type in ["criar_projeto_pl", "sugestao_projetos"]:
        # Expert PL criar_projeto endpoint
        prepared = {
            'mandato': mandato_data,
            'input': input_data.get('input_text', ''),
        }
        
        # Handle references if present
        if 'references_text' in input_data:
            prepared['references_text'] = input_data['references_text']
        
        return prepared
    
    else:
        # Fallback: return as-is with mandato if available
        prepared = input_data.copy()
        if mandato_data:
            prepared['mandato'] = mandato_data
        return prepared


@router.post("/runs/{run_id}/execute", response_model=dict)
async def execute_evaluation_run(
    *,
    session: Session = Depends(get_session),
    run_id: int,
    current_user: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict:
    """Execute all test cases for a run"""
    
    run = session.get(PromptEvaluationRunORM, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    
    if run.status not in ['pending', 'running']:
        raise HTTPException(status_code=400, detail=f"Run status is '{run.status}', cannot execute")
    
    # Mark as running
    run.status = 'running'
    session.commit()
    
    # Get all cases for this run
    results_query = select(PromptEvaluationResultORM).where(PromptEvaluationResultORM.run_id == run_id)
    existing_results = session.execute(results_query).scalars().all()
    case_ids = [result.case_id for result in existing_results]
    
    if not case_ids:
        # Need to determine which cases to run - this should come from the initial creation
        raise HTTPException(status_code=400, detail="No test cases associated with this run")
    
    cases_query = select(PromptEvaluationCaseORM).where(PromptEvaluationCaseORM.id.in_(case_ids))
    cases = session.execute(cases_query).scalars().all()
    
    # Get template type if specified
    template_type_override = None
    if run.template_id:
        template = session.get(PromptTemplateORM, run.template_id)
        if template:
            template_type_override = template.template_type
    
    completed = 0
    failed = 0
    
    # Create a mapping of case_id to result for updates
    results_by_case = {result.case_id: result for result in existing_results}
    
    for result_orm in existing_results:
        try:
            # Get case for this result
            case = session.get(PromptEvaluationCaseORM, result_orm.case_id)
            if not case:
                logger.error(f"Case {result_orm.case_id} not found")
                failed += 1
                continue
            
            # Execute the test case
            start_time = time.time()
            
            # Map test_type to prompt_template
            prompt_template = VALID_TEST_TYPES.get(case.test_type)
            if not prompt_template:
                raise ValueError(f"Invalid test_type: {case.test_type}")
            
            # Prepare input data with proper transformations (using result's mandato_id)
            prepared_input = prepare_test_input(case, session, mandato_id=result_orm.mandato_id)
            
            # Load specific template if result has template_id
            if result_orm.template_id:
                template_obj = session.get(PromptTemplateORM, result_orm.template_id)
                if template_obj and template_obj.template_type == prompt_template:
                    # Use specific template content directly
                    from ..llm import call_llm_with_template_content
                    response_content = call_llm_with_template_content(
                        content=prepared_input,
                        template_content=template_obj.content,
                        session=session,
                    )
                else:
                    # Fallback to default
                    response_content = call_llm(
                        content=prepared_input,
                        prompt_template=prompt_template,
                        session=session,
                    )
            else:
                # Use default template
                response_content = call_llm(
                    content=prepared_input,
                    prompt_template=prompt_template,
                    session=session,
                )
            
            # Extract the text output from LLM response
            if isinstance(response_content, dict):
                # Try common output keys in order of preference
                # 'response' = BaseStructuredAnswer (most common)
                # 'output' = legacy/custom outputs
                for key in ['response', 'output', 'content', 'text']:
                    if key in response_content:
                        actual_output = response_content[key]
                        break
                else:
                    # No standard key found - store entire dict as JSON
                    # This handles custom structured outputs (e.g., ListaObjetivosMetas)
                    actual_output = json.dumps(response_content, ensure_ascii=False, indent=2)
            else:
                actual_output = str(response_content)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Evaluate with LLM
            llm_score, llm_analysis = evaluate_output_with_llm(
                expected=case.expected_output,
                actual=actual_output,
                session=session,
            )
            
            # Update existing result
            result_orm.actual_output = actual_output
            result_orm.execution_time_ms = execution_time
            result_orm.llm_evaluation_score = llm_score
            result_orm.llm_evaluation_analysis = llm_analysis
            result_orm.error_message = None
            
            completed += 1
            
        except Exception as e:
            logger.error(f"Error executing result {result_orm.id}: {str(e)}")
            
            # Update result with error
            result_orm.error_message = str(e)
            failed += 1
    
    # Update run status
    run.completed_cases = completed
    run.status = 'completed' if failed == 0 else 'failed'
    session.commit()
    
    audit.log(
        event_type="prompt_evaluation_run_executed",
        payload={"run_id": run_id, "completed": completed, "failed": failed},
        actor_user_id=current_user.id,
    )
    
    return {
        "run_id": run_id,
        "status": run.status,
        "completed": completed,
        "failed": failed,
        "total": len(cases),
    }


def evaluate_output_with_llm(
    expected: Optional[str],
    actual: str,
    session: Session,
) -> tuple[Optional[int], Optional[str]]:
    """Use LLM to evaluate output quality"""
    
    if not expected:
        return None, None
    
    evaluation_prompt = f"""Você é um avaliador de qualidade de texto. Compare a saída esperada com a saída real e avalie:

SAÍDA ESPERADA:
{expected}

SAÍDA REAL:
{actual}

Critérios de avaliação:
1. Completude - A saída cobre todos os pontos necessários?
2. Precisão - A informação está correta?
3. Formatação - O texto está bem estruturado?
4. Alinhamento - A saída está alinhada com o esperado?

Forneça:
1. Uma pontuação de 0-100
2. Uma análise detalhada explicando a pontuação

Formato de resposta:
PONTUAÇÃO: [número de 0-100]
ANÁLISE: [sua análise detalhada]"""
    
    try:
        # For now, we'll use a simple evaluation system
        # TODO: Implement proper LLM-based evaluation
        # This would require creating a custom evaluation prompt template
        
        # Simple heuristic evaluation
        if not actual:
            return 0, "Saída vazia"
        
        # Check if expected text appears in actual
        expected_lower = expected.lower()
        actual_lower = actual.lower()
        
        # Calculate a simple similarity score
        expected_words = set(expected_lower.split())
        actual_words = set(actual_lower.split())
        
        if not expected_words:
            return None, "Saída esperada vazia"
        
        overlap = len(expected_words & actual_words)
        score = int((overlap / len(expected_words)) * 100)
        score = min(100, score)  # Cap at 100
        
        analysis = f"Pontuação baseada em sobreposição de palavras. {overlap} de {len(expected_words)} palavras esperadas encontradas."
        
        return score, analysis
        
    except Exception as e:
        logger.error(f"Error evaluating with LLM: {str(e)}")
        return None, f"Error during evaluation: {str(e)}"


# ==================== Results ====================

@router.get("/results", response_model=List[PromptEvaluationResultDetail])
async def list_evaluation_results(
    *,
    session: Session = Depends(get_session),
    current_user: UserORM = require_admin_user,
    run_id: Optional[int] = Query(None, description="Filter by run ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> List[PromptEvaluationResultDetail]:
    """List evaluation results with details"""
    
    query = (
        select(PromptEvaluationResultORM)
        .options(
            joinedload(PromptEvaluationResultORM.case),
            joinedload(PromptEvaluationResultORM.run).joinedload(PromptEvaluationRunORM.template),
            joinedload(PromptEvaluationResultORM.mandato),
            joinedload(PromptEvaluationResultORM.template),
        )
    )
    
    if run_id:
        query = query.where(PromptEvaluationResultORM.run_id == run_id)
    
    query = query.order_by(PromptEvaluationResultORM.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = session.execute(query)
    results = result.unique().scalars().all()
    
    detailed_results = []
    for res in results:
        detail_dict = {
            "id": res.id,
            "run_id": res.run_id,
            "case_id": res.case_id,
            "mandato_id": res.mandato_id,
            "template_id": res.template_id,
            "actual_output": res.actual_output,
            "execution_time_ms": res.execution_time_ms,
            "llm_evaluation_score": res.llm_evaluation_score,
            "llm_evaluation_analysis": res.llm_evaluation_analysis,
            "human_evaluation": res.human_evaluation,
            "error_message": res.error_message,
            "created_at": res.created_at,
            "case_name": res.case.name if res.case else "",
            "case_test_type": res.case.test_type if res.case else "",
            "case_input_data": res.case.input_data if res.case else {},
            "case_expected_output": res.case.expected_output if res.case else None,
            "run_name": res.run.run_name if res.run else None,
            "template_version": res.template.version if res.template else None,
            "template_type": res.template.template_type if res.template else None,
            "mandato_nome": res.mandato.nome_parlamentar if res.mandato else None,
            "template_description": res.template.description if res.template else None,
        }
        detailed_results.append(PromptEvaluationResultDetail(**detail_dict))
    
    return detailed_results


@router.get("/results/export-csv")
async def export_results_to_csv(
    *,
    session: Session = Depends(get_session),
    current_user: UserORM = require_admin_user,
    run_id: Optional[int] = Query(None, description="Filter by run ID"),
) -> StreamingResponse:
    """Export evaluation results to CSV"""
    
    query = (
        select(PromptEvaluationResultORM)
        .options(
            joinedload(PromptEvaluationResultORM.case),
            joinedload(PromptEvaluationResultORM.run).joinedload(PromptEvaluationRunORM.template)
        )
    )
    
    if run_id:
        query = query.where(PromptEvaluationResultORM.run_id == run_id)
    
    result = session.execute(query)
    results = result.unique().scalars().all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'result_id', 'run_id', 'run_name', 'case_name', 'test_type', 
        'template_version', 'execution_time_ms', 'llm_score', 
        'human_evaluation', 'error_message'
    ])
    writer.writeheader()
    
    for res in results:
        row = {
            'result_id': res.id,
            'run_id': res.run_id,
            'run_name': res.run.run_name if res.run else '',
            'case_name': res.case.name if res.case else '',
            'test_type': res.case.test_type if res.case else '',
            'template_version': res.run.template.version if res.run and res.run.template else '',
            'execution_time_ms': res.execution_time_ms or '',
            'llm_score': res.llm_evaluation_score or '',
            'human_evaluation': res.human_evaluation or '',
            'error_message': res.error_message or '',
        }
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/results/{result_id}", response_model=PromptEvaluationResult)
async def get_evaluation_result(
    *,
    session: Session = Depends(get_session),
    result_id: int,
    current_user: UserORM = require_admin_user,
) -> PromptEvaluationResult:
    """Get a specific evaluation result"""
    
    result = session.get(PromptEvaluationResultORM, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation result not found")
    
    return PromptEvaluationResult.model_validate(result)


@router.patch("/results/{result_id}", response_model=PromptEvaluationResult)
async def update_evaluation_result(
    *,
    session: Session = Depends(get_session),
    result_id: int,
    result_update: PromptEvaluationResultUpdate,
    current_user: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> PromptEvaluationResult:
    """Update evaluation result (mainly for human evaluation)"""
    
    result = session.get(PromptEvaluationResultORM, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation result not found")
    
    update_data = result_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(result, field, value)
    
    session.commit()
    session.refresh(result)
    
    audit.log(
        event_type="prompt_evaluation_result_updated",
        payload={"result_id": result_id, "updated_fields": list(update_data.keys())},
        actor_user_id=current_user.id,
    )
    
    return PromptEvaluationResult.model_validate(result)
