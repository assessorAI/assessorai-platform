from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

import streamlit as st
import difflib

try:
    from client.admin import api, ui
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from client.admin import api, ui  # type: ignore  # noqa: E402

ui.render_sidebar()
admin_session = ui.require_admin_session()

st.title("Admin • Templates de Prompts")

st.markdown("""
Gerencie os templates de prompts utilizados pelo sistema. Você pode:
- Visualizar versões de cada template
- Criar novas versões com modificações
- Comparar versões do banco de dados com os arquivos `.md`
- Definir qual versão é a padrão (default)
""")

# Load template types
template_types = ui.call_api(api.list_prompt_template_types)
if template_types is None:
    st.error("Falha ao carregar tipos de templates")
    st.stop()

# Create tabs for each template type
tab_labels = [t["display_name"] for t in template_types]
tabs = st.tabs(tab_labels)

for tab, template_type_info in zip(tabs, template_types):
    with tab:
        template_type = template_type_info["type"]
        display_name = template_type_info["display_name"]
        
        st.subheader(f"{display_name}")
        
        # Show metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Versões no BD", template_type_info["db_versions_count"])
        with col2:
            st.metric("Versão Default", template_type_info.get("default_version", "—"))
        with col3:
            has_file = template_type_info["file_exists"]
            st.metric("Arquivo .md", "✓ Existe" if has_file else "✗ Ausente")
        
        # Load versions
        versions = ui.call_api(
            lambda: api.list_prompt_template_versions(template_type, is_active=True)
        )
        if versions is None:
            st.warning("Erro ao carregar versões")
            continue
        
        # Load file content if available
        file_content = None
        if has_file:
            file_result = ui.call_api(
                lambda: api.get_prompt_template_file_content(template_type)
            )
            if file_result:
                file_content = file_result.get("content")
        
        # Show current default version
        if template_type_info.get("has_active_default"):
            default_version = template_type_info.get("default_version")
            st.info(f"✓ Versão **{default_version}** é a padrão atual (será usada pelo sistema)")
        elif file_content:
            st.info(f"⚠️ Nenhuma versão no banco está marcada como padrão. Sistema usará o arquivo `prompts/{template_type}.md`")
        else:
            st.error("⚠️ Sem versão padrão no banco e sem arquivo .md - sistema não funcionará!")
        
        # Tabs within each template type
        if versions or file_content:
            inner_tabs = []
            inner_tab_labels = []
            
            if versions:
                inner_tab_labels.append("📋 Versões")
            if file_content:
                inner_tab_labels.append("📄 Arquivo Original")
            inner_tab_labels.append("➕ Criar Nova Versão")
            
            inner_tabs = st.tabs(inner_tab_labels)
            inner_tab_idx = 0
            
            # Versions tab
            if versions:
                with inner_tabs[inner_tab_idx]:
                    st.write(f"**{len(versions)} versões encontradas**")
                    
                    for version_info in versions:
                        version_num = version_info["version"]
                        is_default = version_info["is_default"]
                        is_active = version_info["is_active"]
                        created_at = version_info["created_at"]
                        description = version_info.get("description") or "Sem descrição"
                        
                        with st.expander(
                            f"Versão {version_num} {'🌟 (Padrão)' if is_default else ''} {'✓ Ativa' if is_active else '✗ Inativa'}",
                            expanded=is_default
                        ):
                            st.markdown(f"**Criada em:** {created_at}")
                            st.markdown(f"**Descrição:** {description}")
                            
                            # Load full content
                            full_version = ui.call_api(
                                lambda v=version_num: api.get_prompt_template_version(template_type, v)
                            )
                            
                            if full_version:
                                content = full_version.get("content", "")
                                
                                # Show content preview
                                st.markdown("**Conteúdo:**")
                                st.code(content, language="markdown", line_numbers=True)
                                
                                # Actions
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    if not is_default and is_active:
                                        if st.button(f"Definir como Padrão", key=f"set_default_{template_type}_{version_num}"):
                                            result = ui.call_api(
                                                lambda: api.set_prompt_template_as_default(full_version["id"])
                                            )
                                            if result:
                                                st.success(f"Versão {version_num} definida como padrão!")
                                                st.rerun()
                                
                                with col2:
                                    if is_active and not is_default:
                                        if st.button(f"Desativar", key=f"deactivate_{template_type}_{version_num}"):
                                            result = ui.call_api(
                                                lambda: api.delete_prompt_template(full_version["id"])
                                            )
                                            if result:
                                                st.success(f"Versão {version_num} desativada!")
                                                st.rerun()
                                
                                with col3:
                                    if not is_default:
                                        if st.button(f"🗑️ Deletar", key=f"delete_permanent_{template_type}_{version_num}", type="secondary"):
                                            # Show confirmation in session state
                                            st.session_state[f"confirm_delete_{template_type}_{version_num}"] = True
                                            st.rerun()
                                
                                with col4:
                                    if st.button(f"Usar como Base", key=f"use_base_{template_type}_{version_num}"):
                                        st.session_state[f"new_version_content_{template_type}"] = content
                                        st.info("Conteúdo copiado para 'Criar Nova Versão'")
                                
                                # Confirmation dialog for permanent deletion
                                if st.session_state.get(f"confirm_delete_{template_type}_{version_num}", False):
                                    st.warning(f"⚠️ **ATENÇÃO:** Você está prestes a deletar permanentemente a versão {version_num}. Esta ação é **irreversível**!")
                                    col_confirm, col_cancel = st.columns(2)
                                    with col_confirm:
                                        if st.button(f"✓ Sim, deletar permanentemente", key=f"confirm_yes_{template_type}_{version_num}", type="primary"):
                                            result = ui.call_api(
                                                lambda: api.permanently_delete_prompt_template(full_version["id"])
                                            )
                                            if result:
                                                st.success(f"Versão {version_num} deletada permanentemente!")
                                                st.session_state.pop(f"confirm_delete_{template_type}_{version_num}", None)
                                                st.rerun()
                                    with col_cancel:
                                        if st.button(f"✗ Cancelar", key=f"confirm_no_{template_type}_{version_num}"):
                                            st.session_state.pop(f"confirm_delete_{template_type}_{version_num}", None)
                                            st.rerun()
                inner_tab_idx += 1
            
            # File content tab
            if file_content:
                with inner_tabs[inner_tab_idx]:
                    st.markdown(f"**Arquivo:** `prompts/{template_type}.md`")
                    st.markdown("Este é o conteúdo do arquivo original que serve como fallback.")
                    
                    st.code(file_content, language="markdown", line_numbers=True)
                    
                    # Compare with default version
                    if versions:
                        default_version_info = next(
                            (v for v in versions if v.get("is_default")),
                            None
                        )
                        
                        if default_version_info:
                            with st.expander("📊 Comparar com Versão Padrão do BD"):
                                default_full = ui.call_api(
                                    lambda: api.get_prompt_template_version(
                                        template_type,
                                        default_version_info["version"]
                                    )
                                )
                                
                                if default_full:
                                    db_content = default_full.get("content", "")
                                    
                                    # Generate diff
                                    diff = difflib.unified_diff(
                                        file_content.splitlines(keepends=True),
                                        db_content.splitlines(keepends=True),
                                        fromfile=f"Arquivo {template_type}.md",
                                        tofile=f"BD Versão {default_version_info['version']}",
                                        lineterm=""
                                    )
                                    diff_text = "".join(diff)
                                    
                                    if diff_text:
                                        st.code(diff_text, language="diff")
                                    else:
                                        st.success("✓ Conteúdo idêntico!")
                    
                    # Action to restore from file
                    if st.button(f"Usar Arquivo como Base", key=f"use_file_{template_type}"):
                        st.session_state[f"new_version_content_{template_type}"] = file_content
                        st.info("Conteúdo do arquivo copiado para 'Criar Nova Versão'")
                inner_tab_idx += 1
            
            # Create new version tab
            with inner_tabs[inner_tab_idx]:
                st.markdown("### Criar Nova Versão")
                
                with st.form(f"create_version_{template_type}"):
                    description = st.text_area(
                        "Descrição da versão",
                        placeholder="Ex: Adicionado suporte para X, melhorada clareza em Y",
                        height=80
                    )
                    
                    # Pre-fill with session state if available
                    default_content = st.session_state.get(
                        f"new_version_content_{template_type}",
                        file_content or ""
                    )
                    
                    content = st.text_area(
                        "Conteúdo do template (Markdown/Mustache)",
                        value=default_content,
                        height=400,
                        help="Use sintaxe Mustache para variáveis: {{variavel}}"
                    )
                    
                    submitted = st.form_submit_button("Criar Nova Versão")
                    
                    if submitted:
                        if not content.strip():
                            st.error("Conteúdo não pode estar vazio")
                        else:
                            payload = {
                                "template_type": template_type,
                                "content": content,
                                "description": description or None
                            }
                            
                            result = ui.call_api(
                                lambda: api.create_prompt_template_version(payload)
                            )
                            
                            if result:
                                new_version = result.get("version")
                                st.success(f"✓ Nova versão {new_version} criada com sucesso!")
                                
                                # Clear session state
                                if f"new_version_content_{template_type}" in st.session_state:
                                    del st.session_state[f"new_version_content_{template_type}"]
                                
                                st.rerun()
        else:
            st.warning("Nenhuma versão no banco de dados e nenhum arquivo .md encontrado.")
            
            # Allow creating first version from scratch
            with st.form(f"create_first_version_{template_type}"):
                st.markdown("### Criar Primeira Versão")
                
                description = st.text_area(
                    "Descrição da versão",
                    placeholder="Ex: Versão inicial do template",
                    height=80
                )
                
                content = st.text_area(
                    "Conteúdo do template (Markdown/Mustache)",
                    height=400,
                    help="Use sintaxe Mustache para variáveis: {{variavel}}"
                )
                
                submitted = st.form_submit_button("Criar Primeira Versão")
                
                if submitted:
                    if not content.strip():
                        st.error("Conteúdo não pode estar vazio")
                    else:
                        payload = {
                            "template_type": template_type,
                            "content": content,
                            "description": description or None
                        }
                        
                        result = ui.call_api(
                            lambda: api.create_prompt_template_version(payload)
                        )
                        
                        if result:
                            new_version = result.get("version")
                            st.success(f"✓ Primeira versão {new_version} criada com sucesso!")
                            st.rerun()

st.divider()
st.markdown("""
### Sobre Templates de Prompts

Os templates são usados pelo sistema para gerar conteúdo via LLM. Cada template:
- Pode ter múltiplas versões (versionamento automático)
- Apenas uma versão pode ser marcada como padrão (default) por tipo
- O sistema usa a versão default do BD; se não houver, usa o arquivo `.md` como fallback
- Use sintaxe Mustache para variáveis: `{{nome_da_variavel}}`
""")
