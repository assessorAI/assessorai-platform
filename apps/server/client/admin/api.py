from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import ConnectionError, Timeout
import streamlit as st

from . import state

DEFAULT_BASE_URL = "http://localhost:8000"


def _resolve_base_url() -> str:
    try:
        config_url = st.config.get_option("api.base_url")  # type: ignore[attr-defined]
    except RuntimeError:
        config_url = None
    if config_url:
        return str(config_url).strip().rstrip("/")
    env_url = os.getenv("ASSESSORAI_API_URL")
    if env_url:
        return env_url.strip().rstrip("/")
    return DEFAULT_BASE_URL


class APIError(RuntimeError):
    def __init__(self, response: requests.Response, message: Optional[str] = None):
        self.response = response
        self.status_code = response.status_code if response is not None else None
        detail = message or _extract_error_message(response)
        super().__init__(detail)


def _extract_error_message(response: Optional[requests.Response]) -> str:
    if response is None:
        return "API request failed (no response)."
    try:
        data = response.json()
        if isinstance(data, dict):
            if "detail" in data:
                return str(data["detail"])
            return json.dumps(data)
    except Exception:
        pass
    return f"API request failed with status {response.status_code}"


def _base_url() -> str:
    return _resolve_base_url()


def get_base_url() -> str:
    return _base_url()


def _session() -> requests.Session:
    key = "_admin_http_session"
    if key not in st.session_state:
        st.session_state[key] = requests.Session()
    return st.session_state[key]


def _authorised_headers(include_token: bool = True) -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if include_token:
        token = st.session_state.get(state.ADMIN_TOKEN_KEY)
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


def _request(
    method: str,
    path: str,
    *,
    json_body: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    include_token: bool = True,
    timeout: int = 30,
    retries: int = 3,
) -> Any:
    base = _base_url()
    url = f"{base}{path if path.startswith('/') else '/' + path}"
    sess = _session()
    
    last_error = None
    for attempt in range(retries):
        try:
            response = sess.request(
                method,
                url,
                json=json_body,
                data=data,
                params=params,
                headers=_authorised_headers(include_token),
                timeout=timeout,
            )
            
            if response.status_code == 401:
                # Try to refresh by calling /user/me
                try:
                    _request("GET", "/user/me", include_token=True, retries=1)
                    # If successful, retry the original request
                    response = sess.request(
                        method,
                        url,
                        json=json_body,
                        data=data,
                        params=params,
                        headers=_authorised_headers(include_token),
                        timeout=timeout,
                    )
                    if response.status_code == 401:
                        raise APIError(response, "Sessão expirada. Faça login novamente.")
                except APIError:
                    raise APIError(response, "Sessão expirada. Faça login novamente.")
            
            if response.status_code >= 400:
                raise APIError(response)
            if response.status_code == 204:
                return None
            if "application/json" in response.headers.get("content-type", ""):
                return response.json()
            return response.text
            
        except (ConnectionError, Timeout) as e:
            last_error = e
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                time.sleep(wait_time)
                continue
            raise APIError(None, f"Conexão falhou após {retries} tentativas: {str(e)}")
    
    # Should not reach here, but just in case
    if last_error:
        raise APIError(None, f"Conexão falhou: {str(last_error)}")


def login(email: str, password: str) -> None:
    data = {"username": email, "password": password}
    response = _session().post(
        f"{_base_url()}/auth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        timeout=30,
    )
    if response.status_code >= 400:
        raise APIError(response)
    token_data = response.json()
    token = token_data["access_token"]
    expiration_date = token_data.get("expiration_date")
    st.session_state[state.ADMIN_TOKEN_KEY] = token
    if expiration_date:
        st.session_state["token_expiration_date"] = expiration_date
    user_info = _request("GET", "/user/me")
    state.set_session(token, user_info)


def logout() -> None:
    state.clear_session()
    st.session_state.pop("token_expiration_date", None)


def is_token_expired() -> bool:
    expiration_date = st.session_state.get("token_expiration_date")
    if not expiration_date:
        return True
    from datetime import datetime
    try:
        exp_dt = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
        return datetime.now(exp_dt.tzinfo) > exp_dt
    except ValueError:
        return True


def fetch_dashboard_summary() -> Dict[str, Any]:
    return _request("GET", "/admin/summary")


def fetch_health_snapshot() -> Dict[str, Any]:
    return _request("GET", "/admin/health")


def list_users(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Returns paginated response: {"users": [...], "total": X, "limit": Y, "offset": Z}"""
    return _request("GET", "/user/", params={"limit": limit, "offset": offset})


def create_user(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request("POST", "/user/", json_body=payload)


def update_user(user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request("PUT", f"/user/{user_id}", json_body=payload)


def list_mandatos(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Returns paginated response: {"mandatos": [...], "total": X, "limit": Y, "offset": Z}"""
    return _request("GET", "/mandatos/", params={"limit": limit, "offset": offset})


def list_mandatos_for_dropdown() -> List[Dict[str, Any]]:
    """Get simplified mandato list for dropdown selection"""
    response = _request("GET", "/mandatos/", params={"limit": 500})
    if isinstance(response, dict) and "mandatos" in response:
        return response["mandatos"]
    return []


def create_mandato(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request("POST", "/mandatos/", json_body=payload)


def update_mandato(mandato_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request("PUT", f"/mandatos/{mandato_id}", json_body=payload)


def permission_levels() -> List[str]:
    # Keep aligned with backend PermissionLevel enum
    return ["User", "Manager", "Admin", "Invited"]


def delete_user(user_id: int) -> Dict[str, Any]:
    return _request("DELETE", f"/user/{user_id}")


def send_password_reset_emails(user_ids: Optional[List[int]] = None, emails: Optional[List[str]] = None, template: str = "password_reset") -> Dict[str, Any]:
    """
    Send password reset emails to specified users or all users.
    
    - If user_ids is provided, send to those specific user IDs
    - If emails is provided, send to those specific emails  
    - If both are None, send to ALL active users
    - template: "password_reset" (default) or "bubble_import_password_reset"
    """
    payload: Dict[str, Any] = {"template": template}
    if user_ids is not None:
        payload["user_ids"] = user_ids
    if emails is not None:
        payload["emails"] = emails
    return _request("POST", "/admin/send-password-reset", json_body=payload)


def delete_mandato(mandato_id: int) -> Dict[str, Any]:
    return _request("DELETE", f"/mandatos/{mandato_id}")


def list_embedding_providers() -> Dict[str, Any]:
    return _request("GET", "/admin/vector/providers", timeout=180)


def vector_stats() -> Dict[str, Any]:
    return _request("GET", "/admin/vector/stats", timeout=180)


def vector_summary() -> Dict[str, Any]:
    """Get summary statistics grouped by house and year"""
    return _request("GET", "/admin/vector/summary", timeout=180)


def reindex_vectors(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request("POST", "/admin/vector/reindex", json_body=payload, timeout=300)


def generate_oficio(
    mandato_id: Optional[int],
    input_text: str,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {"input": input_text}
    params: Dict[str, Any] = {}
    if mandato_id:
        params["mandato_id"] = mandato_id
    return _request("POST", "/oficio/generate", data=data, params=params)


def _post_with_file(
    path: str,
    *,
    mandato_id: Optional[int],
    data: Dict[str, Any],
    uploaded_file,
) -> Dict[str, Any]:
    if uploaded_file is None:
        raise ValueError("Selecione um arquivo para prosseguir.")
    params: Dict[str, Any] = {}
    if mandato_id:
        params["mandato_id"] = mandato_id
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/pdf",
        )
    }
    response = _session().post(
        f"{_base_url()}{path if path.startswith('/') else '/' + path}",
        data=data,
        params=params,
        files=files,
        headers=_authorised_headers(),
        timeout=90,
    )
    if response.status_code >= 400:
        raise APIError(response)
    if "application/json" in response.headers.get("content-type", ""):
        return response.json()
    return {"raw": response.text}


def expert_pl_analysis(
    mandato_id: Optional[int], origem_legislativa: Optional[str], uploaded_file
) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if origem_legislativa:
        data["origem_legislativa"] = origem_legislativa
    return _post_with_file(
        "/expert/pl/analise_constitucionalidade",
        mandato_id=mandato_id,
        data=data,
        uploaded_file=uploaded_file,
    )


def expert_pl_suggest_amendments(
    mandato_id: Optional[int], origem_legislativa: Optional[str], uploaded_file
) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if origem_legislativa:
        data["origem_legislativa"] = origem_legislativa
    return _post_with_file(
        "/expert/pl/sugestao_emendas",
        mandato_id=mandato_id,
        data=data,
        uploaded_file=uploaded_file,
    )


def expert_pl_create_amend(
    mandato_id: Optional[int],
    origem_legislativa: Optional[str],
    emenda_payload: Dict[str, Any],
    uploaded_file,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if origem_legislativa:
        data["origem_legislativa"] = origem_legislativa
    data.update(emenda_payload)
    return _post_with_file(
        "/expert/pl/criar_emenda",
        mandato_id=mandato_id,
        data=data,
        uploaded_file=uploaded_file,
    )


def expert_pl_create_project(
    mandato_id: Optional[int],
    origem_legislativa: Optional[str],
    tema: str,
    referencias: Optional[str],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if mandato_id:
        params["mandato_id"] = mandato_id
    data: Dict[str, Any] = {"text": tema}
    if origem_legislativa:
        data["origem_legislativa"] = origem_legislativa
    if referencias:
        data["referencias"] = referencias
    response = _session().post(
        f"{_base_url()}/expert/pl/criar_projeto",
        data=data,
        params=params,
        headers=_authorised_headers(),
        timeout=90,
    )
    if response.status_code >= 400:
        raise APIError(response)
    return response.json()


def vector_query(query: str, limit: int = 5, offset: int = 0, detail: bool = False) -> Dict[str, Any]:
    return _request(
        "GET",
        "/search/query",
        params={"query": query, "limit": limit, "offset": offset, "detail": detail},
    )


def vector_top_projects(query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    return _request(
        "GET",
        "/search/top_projects",
        params={"query": query, "limit": limit, "offset": offset},
    )


def fetch_audit_logs(
    *,
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    mandato_id: Optional[int] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if event_type:
        params["event_type"] = event_type
    if user_id:
        params["user_id"] = user_id
    if mandato_id:
        params["mandato_id"] = mandato_id
    if from_dt:
        params["from"] = from_dt
    if to_dt:
        params["to"] = to_dt
    return _request("GET", "/admin/audit/", params=params)


def fetch_audit_log(log_id: int) -> Dict[str, Any]:
    return _request("GET", f"/admin/audit/{log_id}")


def add_user_to_mandato(mandato_id: int, email: str) -> List[Dict[str, Any]]:
    return _request("POST", f"/mandatos/{mandato_id}/users", json_body={"email": email})


def remove_user_from_mandato(mandato_id: int, user_id: int) -> List[Dict[str, Any]]:
    return _request("DELETE", f"/mandatos/{mandato_id}/users/{user_id}")



def import_vector_documents(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request("POST", "/admin/vector/import", json_body=payload, timeout=180)


def check_vector_duplicates(items: List[Dict[str, Any]], sample_size: int = 5) -> Dict[str, Any]:
    """Check if documents already exist in the vector store"""
    return _request("POST", "/admin/vector/check-duplicates", json_body={"items": items, "sample_size": sample_size}, timeout=30)


def list_import_jobs(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    return _request("GET", "/admin/vector/jobs", params={"limit": limit, "offset": offset})


def delete_import_job(job_id: int) -> Dict[str, Any]:
    return _request("DELETE", f"/admin/vector/jobs/{job_id}")


# ============================================================================
# Prompt Template Management
# ============================================================================

def list_prompt_template_types() -> List[Dict[str, Any]]:
    """List all prompt template types with metadata"""
    return _request("GET", "/admin/prompts/types", timeout=30, retries=3)


def list_all_prompt_templates(
    template_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List all prompt templates with optional filtering"""
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if template_type:
        params["template_type"] = template_type
    if is_active is not None:
        params["is_active"] = is_active
    return _request("GET", "/admin/prompts/", params=params, timeout=30, retries=3)


def list_prompt_template_versions(
    template_type: str,
    is_active: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """List all versions of a specific template type"""
    params: Dict[str, Any] = {}
    if is_active is not None:
        params["is_active"] = is_active
    return _request(
        "GET",
        f"/admin/prompts/{template_type}/versions",
        params=params,
        timeout=30,
        retries=3
    )


def get_prompt_template_version(template_type: str, version: int) -> Dict[str, Any]:
    """Get a specific version of a template"""
    return _request(
        "GET",
        f"/admin/prompts/{template_type}/{version}",
        timeout=30,
        retries=3
    )


def get_prompt_template_file_content(template_type: str) -> Dict[str, Any]:
    """Get the file-based template content for comparison"""
    return _request(
        "GET",
        f"/admin/prompts/{template_type}/file-content",
        timeout=30,
        retries=3
    )


def create_prompt_template_version(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new version of a prompt template"""
    return _request("POST", "/admin/prompts/", json_body=payload, timeout=30, retries=3)


def update_prompt_template(template_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update template metadata (description, content, or active status)"""
    return _request(
        "PUT",
        f"/admin/prompts/{template_id}",
        json_body=payload,
        timeout=30,
        retries=3
    )


def delete_prompt_template(template_id: int) -> Dict[str, Any]:
    """Soft delete a template (set is_active=False)"""
    return _request("DELETE", f"/admin/prompts/{template_id}", timeout=30, retries=3)


def set_prompt_template_as_default(template_id: int) -> Dict[str, Any]:
    """Set a template version as the default for its type"""
    return _request(
        "POST",
        f"/admin/prompts/{template_id}/set-default",
        timeout=30,
        retries=3
    )


def permanently_delete_prompt_template(template_id: int) -> Dict[str, Any]:
    """Permanently delete a template from database (irreversible)"""
    return _request(
        "DELETE",
        f"/admin/prompts/{template_id}/permanent",
        timeout=30,
        retries=3
    )


# ==================== Prompt Evaluation API Functions ====================

def create_evaluation_case(
    name: str,
    test_type: str,
    input_data: dict,
    expected_output: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new evaluation test case"""
    return _request(
        "POST",
        "/admin/prompt-evaluation/cases",
        json_body={
            "name": name,
            "test_type": test_type,
            "input_data": input_data,
            "expected_output": expected_output,
        },
    )


def list_evaluation_cases(
    test_type: Optional[str] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """List evaluation test cases"""
    params = {"is_active": is_active, "skip": skip, "limit": limit}
    if test_type:
        params["test_type"] = test_type
    return _request("GET", "/admin/prompt-evaluation/cases", params=params)


def get_evaluation_case(case_id: int) -> Dict[str, Any]:
    """Get a specific evaluation case"""
    return _request("GET", f"/admin/prompt-evaluation/cases/{case_id}")


def update_evaluation_case(
    case_id: int,
    name: Optional[str] = None,
    test_type: Optional[str] = None,
    input_data: Optional[dict] = None,
    expected_output: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update an evaluation case"""
    updates = {}
    if name is not None:
        updates["name"] = name
    if test_type is not None:
        updates["test_type"] = test_type
    if input_data is not None:
        updates["input_data"] = input_data
    if expected_output is not None:
        updates["expected_output"] = expected_output
    if is_active is not None:
        updates["is_active"] = is_active
    
    return _request("PATCH", f"/admin/prompt-evaluation/cases/{case_id}", json_body=updates)


def delete_evaluation_case(case_id: int, permanent: bool = False):
    """Delete an evaluation case"""
    params = {"permanent": permanent}
    _request("DELETE", f"/admin/prompt-evaluation/cases/{case_id}", params=params)


def import_cases_from_csv_file(uploaded_file) -> Dict[str, Any]:
    """Import evaluation cases from CSV file (Streamlit UploadedFile)"""
    # Read file content
    content = uploaded_file.getvalue()
    filename = uploaded_file.name
    
    # Make multipart/form-data request
    base = _base_url()
    url = f"{base}/admin/prompt-evaluation/cases/import-csv"
    sess = _session()
    
    files = {"file": (filename, content, "text/csv")}
    headers = _authorised_headers(include_token=True)
    # Remove Content-Type from headers to let requests set it correctly for multipart
    headers.pop("Content-Type", None)
    
    response = sess.post(url, files=files, headers=headers, timeout=60)
    
    if response.status_code >= 400:
        raise APIError(response)
    
    return response.json()


def export_cases_to_csv(test_type: Optional[str] = None) -> bytes:
    """Export evaluation cases to CSV - returns raw bytes"""
    params = {}
    if test_type:
        params["test_type"] = test_type
    
    # Make raw request to get bytes
    base = _base_url()
    url = f"{base}/admin/prompt-evaluation/cases/export-csv"
    sess = _session()
    
    response = sess.get(url, params=params, headers=_authorised_headers(), timeout=60)
    
    if response.status_code >= 400:
        raise APIError(response)
    
    return response.content


def create_evaluation_run(
    case_ids: List[int],
    mandato_ids: List[int],
    template_ids: List[Optional[int]],
    run_name: Optional[str] = None,
    templates_by_type: Optional[dict] = None,
) -> Dict[str, Any]:
    """Create a new evaluation run with multi-mandato and multi-template support"""
    json_body = {
        "case_ids": case_ids,
        "mandato_ids": mandato_ids,
        "template_ids": template_ids,
        "run_name": run_name,
    }
    if templates_by_type:
        json_body["templates_by_type"] = templates_by_type
    
    return _request(
        "POST",
        "/admin/prompt-evaluation/runs",
        json_body=json_body,
    )


def list_evaluation_runs(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """List evaluation runs"""
    params = {"skip": skip, "limit": limit}
    if status:
        params["status"] = status
    return _request("GET", "/admin/prompt-evaluation/runs", params=params)


def get_evaluation_run(run_id: int) -> Dict[str, Any]:
    """Get a specific evaluation run"""
    return _request("GET", f"/admin/prompt-evaluation/runs/{run_id}")


def update_evaluation_run(
    run_id: int,
    status: Optional[str] = None,
    completed_cases: Optional[int] = None,
) -> Dict[str, Any]:
    """Update evaluation run status"""
    updates = {}
    if status is not None:
        updates["status"] = status
    if completed_cases is not None:
        updates["completed_cases"] = completed_cases
    
    return _request("PATCH", f"/admin/prompt-evaluation/runs/{run_id}", json_body=updates)


def execute_evaluation_run(run_id: int) -> Dict[str, Any]:
    """Execute all test cases for a run"""
    return _request("POST", f"/admin/prompt-evaluation/runs/{run_id}/execute", timeout=300)


def list_evaluation_results(
    run_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """List evaluation results"""
    params = {"skip": skip, "limit": limit}
    if run_id:
        params["run_id"] = run_id
    return _request("GET", "/admin/prompt-evaluation/results", params=params)


def get_evaluation_result(result_id: int) -> Dict[str, Any]:
    """Get a specific evaluation result"""
    return _request("GET", f"/admin/prompt-evaluation/results/{result_id}")


def update_evaluation_result(
    result_id: int,
    human_evaluation: Optional[str] = None,
    llm_evaluation_score: Optional[int] = None,
    llm_evaluation_analysis: Optional[str] = None,
) -> Dict[str, Any]:
    """Update evaluation result (mainly for human evaluation)"""
    updates = {}
    if human_evaluation is not None:
        updates["human_evaluation"] = human_evaluation
    if llm_evaluation_score is not None:
        updates["llm_evaluation_score"] = llm_evaluation_score
    if llm_evaluation_analysis is not None:
        updates["llm_evaluation_analysis"] = llm_evaluation_analysis
    
    return _request("PATCH", f"/admin/prompt-evaluation/results/{result_id}", json_body=updates)


def export_results_to_csv(run_id: Optional[int] = None) -> bytes:
    """Export evaluation results to CSV - returns raw bytes"""
    params = {}
    if run_id:
        params["run_id"] = run_id
    
    # Make raw request to get bytes
    base = _base_url()
    url = f"{base}/admin/prompt-evaluation/results/export-csv"
    sess = _session()
    
    response = sess.get(url, params=params, headers=_authorised_headers(), timeout=60)
    
    if response.status_code >= 400:
        raise APIError(response)
    
    return response.content

