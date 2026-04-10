from __future__ import annotations

from pathlib import Path
import sys
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import pandas as pd

try:
    from client.admin import api, ui
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from client.admin import api, ui  # type: ignore  # noqa: E402

ui.render_sidebar()
admin_session = ui.require_admin_session()

st.title("Admin • Avaliação de Prompts")

st.markdown("""
Sistema de avaliação controlada de prompts contra casos de teste conhecidos.
Permite validar mudanças em templates antes de colocá-los em produção.
""")

# Test types mapping
TEST_TYPES = {
    "oficio": "Geração de Ofícios",
    "criar_projeto_pl": "Sugestão de Projetos",
    "constitucionalidade": "Análise de Constitucionalidade",
    "criar_emenda": "Criação de Emendas",
    "sugestao_emendas": "Sugestão de Emendas",
    "sugestao_projetos": "Sugestão de Projetos",
}

# Create tabs
tab1, tab2, tab3 = st.tabs([
    "📋 Casos de Teste",
    "▶️ Executar Avaliações", 
    "📊 Resultados"
])

# ==================== Tab 1: Test Cases ====================
with tab1:
    st.header("Gerenciar Casos de Teste")
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("➕ Criar Novo Caso", use_container_width=True):
            st.session_state["show_create_case_form"] = True
            st.session_state["edit_case_id"] = None  # Reset edit mode
    
    with col2:
        uploaded_file = st.file_uploader(
            "Importar CSV",
            type=["csv"],
            help="CSV com colunas: name, test_type, input_text, orgao_destino, remetente, expected_output",
            key="csv_upload"
        )
        if uploaded_file is not None:
            with st.spinner("Importando casos..."):
                result = ui.call_api(lambda: api.import_cases_from_csv_file(uploaded_file))
                if result:
                    st.success(f"✓ {result['imported_count']} casos importados")
                    if result.get('error_count', 0) > 0:
                        st.warning(f"⚠️ {result['error_count']} erros encontrados")
                        with st.expander("Ver erros"):
                            for error in result.get('errors', []):
                                st.text(error)
                    st.rerun()
    
    with col3:
        test_type_filter = st.selectbox(
            "Filtrar",
            ["Todos"] + list(TEST_TYPES.keys()),
            format_func=lambda x: "Todos" if x == "Todos" else TEST_TYPES.get(x, x),
            key="filter_test_type"
        )
    
    # Create/Edit case form
    if st.session_state.get("show_create_case_form"):
        # Get mandatos for dropdown
        mandatos = ui.call_api(api.list_mandatos_for_dropdown)
        if not mandatos:
            st.warning("Nenhum mandato encontrado. Crie um mandato primeiro.")
            if st.button("Voltar"):
                st.session_state["show_create_case_form"] = False
                st.session_state["edit_case_id"] = None
                st.rerun()
        else:
            # Check if we're editing
            edit_case_id = st.session_state.get("edit_case_id")
            is_editing = edit_case_id is not None
            
            # Load existing case data if editing
            existing_case = None
            if is_editing:
                all_cases_for_edit = ui.call_api(lambda: api.list_evaluation_cases(is_active=True, limit=500))
                if all_cases_for_edit:
                    existing_case = next((c for c in all_cases_for_edit if c['id'] == edit_case_id), None)
            
            with st.form("create_case_form"):
                st.subheader("Editar Caso de Teste" if is_editing else "Criar Novo Caso de Teste")
                
                name = st.text_input(
                    "Nome do Caso*", 
                    value=existing_case['name'] if existing_case else "",
                    placeholder="Ex: Ofício simples para prefeito"
                )
                
                # Get default index for test_type if editing
                default_test_type_idx = 0
                if existing_case:
                    try:
                        default_test_type_idx = list(TEST_TYPES.keys()).index(existing_case['test_type'])
                    except ValueError:
                        pass
                
                test_type = st.selectbox(
                    "Tipo de Teste*",
                    list(TEST_TYPES.keys()),
                    index=default_test_type_idx,
                    format_func=lambda x: TEST_TYPES[x]
                )
                
                # Advanced mode toggle
                advanced_mode = st.checkbox("🔧 Modo Avançado (editar JSON manualmente)", value=False)
                
                # Store field values for building input_data
                input_data = {}
                
                if advanced_mode:
                    # JSON editor mode
                    st.markdown("**Dados de Entrada (JSON)**")
                    st.caption("Para 'oficio': {\"mandato_id\": 1, \"input_text\": \"...\", \"orgao_destino\": \"...\", \"remetente\": \"...\"}")
                    st.caption("Para outros: {\"mandato_id\": 1, \"input_text\": \"...\"}")
                    
                    # Pre-populate with existing data if editing
                    default_json_str = ""
                    if existing_case and 'input_data' in existing_case:
                        default_json_str = json.dumps(existing_case['input_data'], indent=2)
                    
                    input_data_str = st.text_area(
                        "Input Data*",
                        value=default_json_str,
                        height=200,
                        placeholder='{"mandato_id": 1, "input_text": "Solicitar informações sobre..."}',
                        label_visibility="collapsed"
                    )
                else:
                    # Intuitive form mode based on test_type
                    st.divider()
                    st.markdown("**📝 Campos do Caso de Teste**")
                    st.info("ℹ️ Mandatos agora são selecionados durante a execução do teste, não na criação do caso. Isso permite testar o mesmo caso com múltiplos mandatos.")
                    
                    # Type-specific fields
                    if test_type == "oficio":
                        st.caption("Campos para geração de ofícios")
                        existing_input_data = existing_case.get('input_data', {}) if existing_case else {}
                        
                        input_text = st.text_area(
                            "Texto da Demanda*",
                            value=existing_input_data.get('input_text', ''),
                            placeholder="Ex: Solicitar informações sobre falta de vagas em creches na região...",
                            height=100,
                            help="Descreva a demanda cidadã ou solicitação"
                        )
                        orgao_destino = st.text_input(
                            "Órgão Destino",
                            value=existing_input_data.get('orgao_destino', ''),
                            placeholder="Ex: Secretaria Municipal de Educação",
                            help="Opcional: órgão ou instituição destinatária"
                        )
                        remetente = st.text_input(
                            "Remetente",
                            value=existing_input_data.get('remetente', ''),
                            placeholder="Ex: Vereador(a) Marina Silva",
                            help="Opcional: nome do remetente (senão usa dados do mandato)"
                        )
                        
                        if input_text:
                            input_data["input_text"] = input_text
                        if orgao_destino:
                            input_data["orgao_destino"] = orgao_destino
                        if remetente:
                            input_data["remetente"] = remetente
                    
                    elif test_type in ["constitucionalidade", "criar_emenda", "sugestao_emendas"]:
                        st.caption("Campos para análise Expert PL")
                        existing_input_data = existing_case.get('input_data', {}) if existing_case else {}
                        
                        # File upload option
                        use_file_upload = st.checkbox(
                            "📎 Fazer upload de arquivo PDF",
                            help="Marque para fazer upload de um arquivo ao invés de usar uma referência"
                        )
                        
                        file_reference = ""
                        if use_file_upload:
                            uploaded_pdf = st.file_uploader(
                                "Upload PDF*",
                                type=["pdf"],
                                help="Faça upload do arquivo PDF do projeto de lei"
                            )
                            if uploaded_pdf:
                                # Store the file name as reference (actual upload would happen on submit)
                                file_reference = uploaded_pdf.name
                                st.info(f"Arquivo selecionado: {uploaded_pdf.name}")
                                # Store the actual file in session state for later upload
                                st.session_state[f"uploaded_file_{uploaded_pdf.name}"] = uploaded_pdf
                        else:
                            # File path (for testing, we'll store as string reference)
                            file_reference = st.text_input(
                                "Referência do Arquivo PDF*",
                                value=existing_input_data.get('file_reference', ''),
                                placeholder="Ex: projeto_lei_123.pdf ou caminho/para/arquivo.pdf",
                                help="Para testes automatizados, use uma referência ao arquivo"
                            )
                        
                        # Get default index for origem_legislativa
                        origem_options = ["", "Executivo", "Legislativo"]
                        default_origem_idx = 0
                        if 'origem_legislativa' in existing_input_data:
                            try:
                                default_origem_idx = origem_options.index(existing_input_data['origem_legislativa'])
                            except ValueError:
                                pass
                        
                        origem_legislativa = st.selectbox(
                            "Origem Legislativa",
                            options=origem_options,
                            index=default_origem_idx,
                            help="Opcional: origem da legislação"
                        )
                        
                        if file_reference:
                            input_data["file_reference"] = file_reference
                        if origem_legislativa:
                            input_data["origem_legislativa"] = origem_legislativa
                        
                        # Specific to criar_emenda
                        if test_type == "criar_emenda":
                            titulo_emenda = st.text_input(
                                "Título da Emenda*",
                                value=existing_input_data.get('titulo_emenda', ''),
                                placeholder="Ex: Emenda de redação ao artigo 5º"
                            )
                            
                            # Get default index for tipo_emenda
                            tipo_options = ["substitutivo", "aditiva", "modificativa", "supressiva", "redacao"]
                            default_tipo_idx = 0
                            if 'tipo_emenda' in existing_input_data:
                                try:
                                    default_tipo_idx = tipo_options.index(existing_input_data['tipo_emenda'])
                                except ValueError:
                                    pass
                            
                            tipo_emenda = st.selectbox(
                                "Tipo da Emenda*",
                                options=tipo_options,
                                index=default_tipo_idx
                            )
                            
                            if titulo_emenda:
                                input_data["titulo_emenda"] = titulo_emenda
                            if tipo_emenda:
                                input_data["tipo_emenda"] = tipo_emenda
                    
                    elif test_type == "sugestao_projetos" or test_type == "criar_projeto_pl":
                        st.caption("Campos para sugestão de projetos")
                        existing_input_data = existing_case.get('input_data', {}) if existing_case else {}
                        
                        input_text = st.text_area(
                            "Descrição do Tema*",
                            value=existing_input_data.get('input_text', ''),
                            placeholder="Ex: Criar projeto sobre mobilidade urbana e ciclovias...",
                            height=100,
                            help="Descreva o tema ou área para sugestão de projetos"
                        )
                        
                        if input_text:
                            input_data["input_text"] = input_text
                    
                    else:
                        # Generic fallback
                        st.caption("Campos genéricos")
                        existing_input_data = existing_case.get('input_data', {}) if existing_case else {}
                        
                        input_text = st.text_area(
                            "Input de Texto*",
                            value=existing_input_data.get('input_text', ''),
                            placeholder="Descreva o input para este tipo de teste...",
                            height=100
                        )
                        
                        if input_text:
                            input_data["input_text"] = input_text
                
                st.divider()
                expected_output = st.text_area(
                    "Saída Esperada (opcional)",
                    value=existing_case.get('expected_output', '') if existing_case else "",
                    height=150,
                    placeholder="Texto esperado como resultado da execução...",
                    help="Opcional: resultado esperado para comparação na avaliação"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button(
                        "✓ Atualizar Caso" if is_editing else "✓ Criar Caso", 
                        use_container_width=True
                    )
                with col2:
                    cancel = st.form_submit_button("✗ Cancelar", use_container_width=True)
                
                if submit:
                    # Validate and create/update
                    if not name or not test_type:
                        st.error("Preencha o nome e tipo de teste")
                    elif advanced_mode:
                        # Parse JSON manually
                        if not input_data_str:
                            st.error("Preencha os dados de entrada (JSON)")
                        else:
                            try:
                                input_data = json.loads(input_data_str)
                                if is_editing:
                                    result = ui.call_api(lambda: api.update_evaluation_case(
                                        case_id=edit_case_id,
                                        name=name,
                                        test_type=test_type,
                                        input_data=input_data,
                                        expected_output=expected_output if expected_output else None
                                    ))
                                    if result:
                                        st.success("✓ Caso atualizado com sucesso!")
                                        st.session_state["show_create_case_form"] = False
                                        st.session_state["edit_case_id"] = None
                                        st.rerun()
                                else:
                                    result = ui.call_api(lambda: api.create_evaluation_case(
                                        name=name,
                                        test_type=test_type,
                                        input_data=input_data,
                                        expected_output=expected_output if expected_output else None
                                    ))
                                    if result:
                                        st.success("✓ Caso criado com sucesso!")
                                        st.session_state["show_create_case_form"] = False
                                        st.rerun()
                            except json.JSONDecodeError:
                                st.error("Input Data deve ser um JSON válido")
                    else:
                        # Use built input_data from form fields
                        # Validate required fields based on test type
                        if test_type == "oficio" and "input_text" not in input_data:
                            st.error("Preencha o texto da demanda")
                        elif test_type in ["constitucionalidade", "criar_emenda", "sugestao_emendas"] and "file_reference" not in input_data:
                            st.error("Preencha a referência do arquivo PDF")
                        elif test_type == "criar_emenda" and ("titulo_emenda" not in input_data or "tipo_emenda" not in input_data):
                            st.error("Preencha título e tipo da emenda")
                        elif test_type in ["sugestao_projetos", "criar_projeto_pl"] and "input_text" not in input_data:
                            st.error("Preencha o campo de texto")
                        else:
                            if is_editing:
                                # Single case update
                                result = ui.call_api(lambda: api.update_evaluation_case(
                                    case_id=edit_case_id,
                                    name=name,
                                    test_type=test_type,
                                    input_data=input_data,
                                    expected_output=expected_output if expected_output else None
                                ))
                                if result:
                                    st.success("✓ Caso atualizado com sucesso!")
                                    st.session_state["show_create_case_form"] = False
                                    st.session_state["edit_case_id"] = None
                                    st.rerun()
                            else:
                                # Create single case (mandatos selected during run creation)
                                result = ui.call_api(lambda: api.create_evaluation_case(
                                    name=name,
                                    test_type=test_type,
                                    input_data=input_data,
                                    expected_output=expected_output if expected_output else None
                                ))
                                if result:
                                    st.success("✓ Caso criado com sucesso!")
                                    st.session_state["show_create_case_form"] = False
                                    st.rerun()
                
                if cancel:
                    st.session_state["show_create_case_form"] = False
                    st.session_state["edit_case_id"] = None
                    st.rerun()
    
    # List cases
    st.divider()
    st.subheader("Casos Existentes")
    
    cases = ui.call_api(lambda: api.list_evaluation_cases(
        test_type=test_type_filter if test_type_filter != "Todos" else None,
        is_active=True,
        limit=500
    ))
    
    if cases:
        st.caption(f"Total: {len(cases)} casos")
        
        for case in cases:
            with st.expander(f"**{case['name']}** ({TEST_TYPES.get(case['test_type'], case['test_type'])})"):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**ID:** {case['id']}")
                    st.markdown(f"**Tipo:** {TEST_TYPES.get(case['test_type'], case['test_type'])}")
                    
                    st.markdown("**Input Data:**")
                    st.json(case['input_data'])
                    
                    if case.get('expected_output'):
                        st.markdown("**Saída Esperada:**")
                        st.text(case['expected_output'][:500] + ('...' if len(case['expected_output']) > 500 else ''))
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_case_{case['id']}", use_container_width=True):
                        st.session_state["show_create_case_form"] = True
                        st.session_state["edit_case_id"] = case['id']
                        st.rerun()
                    
                    if st.button("🗑️ Deletar", key=f"del_case_{case['id']}", use_container_width=True):
                        if st.session_state.get(f"confirm_del_{case['id']}"):
                            ui.call_api(lambda: api.delete_evaluation_case(case['id'], permanent=False))
                            st.success("Caso deletado!")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_del_{case['id']}"] = True
                            st.warning("Clique novamente para confirmar")
    else:
        st.info("Nenhum caso de teste encontrado. Crie um novo ou importe via CSV.")
    
    # Export button
    if cases:
        st.divider()
        if st.button("📥 Exportar Casos para CSV"):
            csv_data = ui.call_api(lambda: api.export_cases_to_csv(
                test_type=test_type_filter if test_type_filter != "Todos" else None
            ))
            if csv_data:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=f"evaluation_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

# ==================== Tab 2: Run Evaluations ====================
with tab2:
    st.header("Executar Avaliação")
    
    st.markdown("""
    Selecione casos de teste e um template (opcional) para executar uma bateria de avaliações.
    O sistema irá:
    1. Executar cada caso de teste contra o endpoint correspondente
    2. Avaliar a saída com IA (comparando com saída esperada)
    3. Registrar resultados para revisão humana
    """)
    
    # Get available cases
    all_cases = ui.call_api(lambda: api.list_evaluation_cases(is_active=True, limit=500))
    
    if not all_cases:
        st.warning("Nenhum caso de teste disponível. Crie casos na aba 'Casos de Teste'.")
    else:
        with st.form("run_evaluation_form"):
            run_name = st.text_input(
                "Nome da Execução (opcional)",
                placeholder="Ex: Teste template v3 - oficios"
            )
            
            # Group cases by test_type
            cases_by_type = {}
            for case in all_cases:
                test_type = case['test_type']
                if test_type not in cases_by_type:
                    cases_by_type[test_type] = []
                cases_by_type[test_type].append(case)
            
            st.subheader("Selecionar Casos de Teste")
            
            selected_case_ids = []
            for test_type, cases in cases_by_type.items():
                with st.expander(f"**{TEST_TYPES.get(test_type, test_type)}** ({len(cases)} casos)"):
                    select_all = st.checkbox(f"Selecionar todos ({test_type})", key=f"select_all_{test_type}")
                    
                    for case in cases:
                        default_value = select_all
                        if st.checkbox(
                            f"{case['name']} (ID: {case['id']})",
                            value=default_value,
                            key=f"case_{case['id']}"
                        ):
                            if case['id'] not in selected_case_ids:
                                selected_case_ids.append(case['id'])
            
            st.divider()
            st.subheader("Selecionar Mandatos*")
            
            # Get mandatos for multi-select
            mandatos = ui.call_api(api.list_mandatos_for_dropdown)
            selected_mandato_ids = []
            
            if mandatos:
                st.info(f"Selecione um ou mais mandatos para testar ({len(mandatos)} disponíveis)")
                
                # Create options for multiselect with better display format
                mandato_options = {}
                for m in mandatos:
                    casa = m.get('casa_legislativa') or 'Outros'
                    nome = m.get('nome_parlamentar', 'N/A')
                    cargo = m.get('cargo_parlamentar', 'N/A')
                    display_name = f"{nome} - {cargo} ({casa})"
                    mandato_options[display_name] = m['id']
                
                # Multiselect with autocomplete
                selected_mandato_names = st.multiselect(
                    "Busque e selecione mandatos",
                    options=list(mandato_options.keys()),
                    help="Digite para buscar. Você pode selecionar múltiplos mandatos.",
                    key="mandato_multiselect"
                )
                
                # Convert selected names to IDs
                selected_mandato_ids = [mandato_options[name] for name in selected_mandato_names]
            else:
                st.warning("Nenhum mandato encontrado. Crie mandatos antes de executar avaliações.")
            
            st.divider()
            st.subheader("Selecionar Templates*")
            
            # Map test_type to prompt template type
            template_type_map = {
                "oficio": "generate_oficio",
                "criar_projeto_pl": "expert_pl_sugestao_projetos",
                "sugestao_projetos": "expert_pl_sugestao_projetos",
                "constitucionalidade": "expert_pl_constitucionalidade",
                "criar_emenda": "expert_pl_criar_emenda",
                "sugestao_emendas": "expert_pl_sugestao_emendas",
            }
            
            # Store templates per type: {test_type: [template_ids]}
            templates_by_type = {}
            selected_template_ids = []  # Flat list for backward compatibility
            
            # Detect test_type from selected cases
            if selected_case_ids:
                selected_cases_objects = [c for c in all_cases if c['id'] in selected_case_ids]
                test_types_in_selection = list(set(c['test_type'] for c in selected_cases_objects))
                
                if len(test_types_in_selection) == 1:
                    # Single test type - show simplified interface
                    detected_test_type = test_types_in_selection[0]
                    st.info(f"Tipo detectado: **{TEST_TYPES.get(detected_test_type, detected_test_type)}**")
                    
                    template_type = template_type_map.get(detected_test_type)
                    
                    if template_type:
                        versions = ui.call_api(lambda: api.list_prompt_template_versions(template_type, is_active=True))
                        if versions:
                            st.info(f"Selecione uma ou mais versões de template para comparar ({len(versions)} disponíveis)")
                            
                            # Option to include default template
                            include_default = st.checkbox(
                                "✓ Template Padrão (usar template padrão do sistema)",
                                value=True,
                                help="Testa usando o template padrão do sistema (não customizado)",
                                key=f"default_{detected_test_type}"
                            )
                            
                            if include_default:
                                selected_template_ids.append(None)
                                templates_by_type[detected_test_type] = [None]
                            else:
                                templates_by_type[detected_test_type] = []
                            
                            # Multi-select for custom versions
                            st.markdown("**Versões Customizadas:**")
                            for version in versions:
                                version_label = f"v{version['version']}"
                                if version.get('is_default'):
                                    version_label += " (padrão do mandato)"
                                if version.get('description'):
                                    version_label += f" - {version['description']}"
                                
                                if st.checkbox(
                                    version_label,
                                    key=f"template_{version['id']}"
                                ):
                                    selected_template_ids.append(version['id'])
                                    templates_by_type[detected_test_type].append(version['id'])
                        else:
                            st.info(f"Nenhuma versão customizada encontrada para {template_type}. Usando apenas template padrão.")
                            selected_template_ids.append(None)
                            templates_by_type[detected_test_type] = [None]
                    else:
                        st.info(f"Tipo de teste '{detected_test_type}' não possui template configurável. Usando template padrão.")
                        selected_template_ids.append(None)
                        templates_by_type[detected_test_type] = [None]
                else:
                    # Multiple test types - show section per type
                    st.info(f"**Múltiplos tipos detectados:** {', '.join([TEST_TYPES.get(t, t) for t in test_types_in_selection])}")
                    st.markdown("Configure os templates para cada tipo de teste:")
                    
                    for test_type in sorted(test_types_in_selection):
                        with st.expander(f"**{TEST_TYPES.get(test_type, test_type)}**", expanded=True):
                            template_type = template_type_map.get(test_type)
                            templates_by_type[test_type] = []
                            
                            if template_type:
                                versions = ui.call_api(lambda tt=template_type: api.list_prompt_template_versions(tt, is_active=True))
                                
                                # Option to include default template
                                include_default = st.checkbox(
                                    "✓ Template Padrão (sistema)",
                                    value=True,
                                    help="Testa usando o template padrão do sistema",
                                    key=f"default_{test_type}"
                                )
                                
                                if include_default:
                                    templates_by_type[test_type].append(None)
                                
                                # Multi-select for custom versions
                                if versions:
                                    st.markdown(f"**Versões Customizadas** ({len(versions)} disponíveis):")
                                    for version in versions:
                                        version_label = f"v{version['version']}"
                                        if version.get('is_default'):
                                            version_label += " (padrão do mandato)"
                                        if version.get('description'):
                                            version_label += f" - {version['description']}"
                                        
                                        if st.checkbox(
                                            version_label,
                                            key=f"template_{test_type}_{version['id']}"
                                        ):
                                            templates_by_type[test_type].append(version['id'])
                                else:
                                    st.caption("Nenhuma versão customizada disponível")
                            else:
                                st.info(f"Tipo '{test_type}' não possui template configurável. Usando apenas template padrão.")
                                templates_by_type[test_type] = [None]
                    
                    # Flatten templates_by_type into selected_template_ids for backward compatibility
                    all_selected_templates = []
                    for templates in templates_by_type.values():
                        all_selected_templates.extend(templates)
                    # Remove duplicates while preserving order
                    seen = set()
                    for tid in all_selected_templates:
                        if tid not in seen:
                            selected_template_ids.append(tid)
                            seen.add(tid)
            else:
                st.caption("Selecione casos de teste para configurar templates")
            
            st.divider()
            
            # Permutation calculation
            if selected_case_ids and selected_mandato_ids and selected_template_ids:
                # Calculate accurate permutations based on case types and their templates
                total_permutations = 0
                if templates_by_type:
                    # Group cases by type
                    cases_by_type_count = {}
                    for case in selected_cases_objects:
                        if case['id'] in selected_case_ids:
                            test_type = case['test_type']
                            cases_by_type_count[test_type] = cases_by_type_count.get(test_type, 0) + 1
                    
                    # Calculate permutations per type
                    breakdown = []
                    for test_type, case_count in cases_by_type_count.items():
                        template_count = len(templates_by_type.get(test_type, [None]))
                        type_perms = case_count * len(selected_mandato_ids) * template_count
                        total_permutations += type_perms
                        breakdown.append(f"{case_count} × {len(selected_mandato_ids)} × {template_count} = {type_perms} ({TEST_TYPES.get(test_type, test_type)})")
                    
                    st.info(f"**📊 Permutações por tipo:**")
                    for line in breakdown:
                        st.caption(f"  • {line}")
                    st.info(f"**Total: {total_permutations} resultados**")
                else:
                    # Simple calculation when all same type
                    num_cases = len(selected_case_ids)
                    num_mandatos = len(selected_mandato_ids)
                    num_templates = len(selected_template_ids)
                    total_permutations = num_cases * num_mandatos * num_templates
                    st.info(f"**📊 Permutações:** {num_cases} casos × {num_mandatos} mandatos × {num_templates} templates = **{total_permutations} resultados**")
            
            submitted = st.form_submit_button("▶️ Executar Avaliação", use_container_width=True)
            
            if submitted:
                if not selected_case_ids:
                    st.error("Selecione pelo menos um caso de teste")
                elif not selected_mandato_ids:
                    st.error("Selecione pelo menos um mandato")
                elif not selected_template_ids:
                    st.error("Selecione pelo menos um template")
                else:
                    # Calculate actual number of results based on templates_by_type
                    if templates_by_type:
                        cases_by_type_count = {}
                        for case in selected_cases_objects:
                            if case['id'] in selected_case_ids:
                                test_type = case['test_type']
                                cases_by_type_count[test_type] = cases_by_type_count.get(test_type, 0) + 1
                        
                        num_results = sum(
                            case_count * len(selected_mandato_ids) * len(templates_by_type.get(test_type, [None]))
                            for test_type, case_count in cases_by_type_count.items()
                        )
                    else:
                        num_results = len(selected_case_ids) * len(selected_mandato_ids) * len(selected_template_ids)
                    
                    with st.spinner(f"Criando run com {num_results} resultados..."):
                        # Prepare payload
                        payload = {
                            "case_ids": selected_case_ids,
                            "mandato_ids": selected_mandato_ids,
                            "template_ids": selected_template_ids,
                            "run_name": run_name if run_name else None,
                        }
                        
                        # Add templates_by_type if we have multiple types
                        if templates_by_type and len(templates_by_type) > 1:
                            payload["templates_by_type"] = templates_by_type
                        
                        # Create run with multi-mandato and multi-template
                        run = ui.call_api(lambda: api.create_evaluation_run(**payload))
                        
                        if run:
                            st.info(f"Run criado com ID: {run['id']} - {num_results} resultados criados")
                            
                            # Execute run
                            with st.spinner(f"Executando {num_results} testes..."):
                                result = ui.call_api(lambda: api.execute_evaluation_run(run['id']))
                            
                            if result:
                                st.success(f"""
                                ✓ Avaliação concluída!
                                - Total de resultados: {result['total']}
                                - Completados: {result['completed']}
                                - Falharam: {result['failed']}
                                - Status: {result['status']}
                                """)
                                
                                # Auto-navigate to results tab by setting session state
                                st.session_state["view_run_id"] = run['id']
                                st.info("✓ Navegue para a aba 'Resultados' para ver os resultados")

# ==================== Tab 3: Results ====================
with tab3:
    st.header("Resultados")
    
    # Get all runs for dropdown
    all_runs = ui.call_api(lambda: api.list_evaluation_runs(limit=100))
    
    if not all_runs:
        st.info("Nenhuma execução encontrada. Execute uma avaliação na aba 'Executar Avaliações'.")
    else:
        # Sort runs by executed_at descending (most recent first)
        all_runs = sorted(all_runs, key=lambda r: r.get('executed_at', ''), reverse=True)
        
        # Auto-select most recent run if not already set
        if "view_run_id" not in st.session_state and all_runs:
            st.session_state["view_run_id"] = all_runs[0]['id']
        
        # Create dropdown options with "Nome-do-teste (data)" format
        run_options = []
        for run in all_runs:
            run_name = run.get('run_name') or f"Run #{run['id']}"
            executed_at = datetime.fromisoformat(run['executed_at'].replace('Z', '+00:00'))
            date_str = executed_at.strftime("%d/%m/%Y %H:%M")
            status_emoji = {
                "completed": "✓",
                "running": "⏳",
                "failed": "✗",
                "cancelled": "⊘"
            }.get(run['status'], "?")
            run_options.append(f"{status_emoji} {run_name} ({date_str})")
        
        # Find current selection index
        current_run_id = st.session_state.get("view_run_id", all_runs[0]['id'])
        try:
            current_idx = next(i for i, run in enumerate(all_runs) if run['id'] == current_run_id)
        except StopIteration:
            current_idx = 0
        
        # Dropdown selector that auto-loads on change
        selected_option = st.selectbox(
            "Selecione uma execução:",
            options=run_options,
            index=current_idx,
            key="run_dropdown"
        )
        
        # Update session state based on selection
        selected_idx = run_options.index(selected_option)
        st.session_state["view_run_id"] = all_runs[selected_idx]['id']
        
    if st.session_state.get("view_run_id"):
        run_id = st.session_state["view_run_id"]
        
        # Get run info
        run = ui.call_api(lambda: api.get_evaluation_run(run_id))
        
        if not run:
            st.error(f"Run {run_id} não encontrado")
        else:
            # Show run summary
            col_title, col_delete = st.columns([5, 1])
            with col_title:
                st.subheader(f"Run #{run_id}: {run['run_name'] or '(sem nome)'}")
            with col_delete:
                if st.button("🗑️ Apagar Run", key=f"delete_run_{run_id}"):
                    if st.session_state.get(f"confirm_del_run_{run_id}"):
                        # Delete run via API
                        deleted = ui.call_api(lambda: api.update_evaluation_run(run_id, status="cancelled"))
                        if deleted:
                            st.success("Run cancelado com sucesso!")
                            # Clear from session state and reload
                            if "view_run_id" in st.session_state:
                                del st.session_state["view_run_id"]
                            st.rerun()
                    else:
                        st.session_state[f"confirm_del_run_{run_id}"] = True
                        st.warning("Clique novamente para confirmar")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", run['status'])
            with col2:
                st.metric("Total de Casos", run['total_cases'])
            with col3:
                st.metric("Completados", run['completed_cases'])
            
            # Show mandatos and templates used in this run
            if run.get('mandato_ids'):
                mandato_count = len(run['mandato_ids'])
                st.caption(f"**Mandatos testados:** {mandato_count}")
            
            if run.get('template_ids'):
                template_count = len(run['template_ids'])
                default_count = run['template_ids'].count(None)
                custom_count = template_count - default_count
                st.caption(f"**Templates testados:** {template_count} ({default_count} padrão, {custom_count} customizados)")
            
            st.divider()
            
            # Get results
            results = ui.call_api(lambda: api.list_evaluation_results(run_id=run_id, limit=500))
            
            if not results:
                st.warning("Nenhum resultado encontrado para esta execução")
            else:
                # Filters
                st.subheader("Filtros")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Extract unique mandatos from results
                    mandatos_in_results = list(set(r.get('mandato_nome', 'N/A') for r in results if r.get('mandato_nome')))
                    mandato_filter = st.selectbox(
                        "Filtrar por Mandato",
                        ["Todos"] + sorted(mandatos_in_results),
                        key="filter_mandato"
                    )
                
                with col2:
                    # Extract unique template descriptions from results
                    templates_in_results = []
                    for r in results:
                        template_desc = r.get('template_description') or 'Template Padrão'
                        if template_desc not in templates_in_results:
                            templates_in_results.append(template_desc)
                    
                    # Sort templates, handling None/null values
                    sorted_templates = sorted(templates_in_results, key=lambda x: (x is None, x or ''))
                    
                    template_filter = st.selectbox(
                        "Filtrar por Template",
                        ["Todos"] + sorted_templates,
                        key="filter_template"
                    )
                
                with col3:
                    # Score filter
                    score_filter = st.selectbox(
                        "Filtrar por Score",
                        ["Todos", "Alto (≥80)", "Médio (60-79)", "Baixo (<60)", "Sem avaliação"],
                        key="filter_score"
                    )
                
                # Apply filters
                filtered_results = results
                
                if mandato_filter != "Todos":
                    filtered_results = [r for r in filtered_results if r.get('mandato_nome') == mandato_filter]
                
                if template_filter != "Todos":
                    filtered_results = [r for r in filtered_results if (r.get('template_description') or 'Template Padrão') == template_filter]
                
                if score_filter != "Todos":
                    if score_filter == "Alto (≥80)":
                        filtered_results = [r for r in filtered_results if (r.get('llm_evaluation_score') or 0) >= 80]
                    elif score_filter == "Médio (60-79)":
                        filtered_results = [r for r in filtered_results if 60 <= (r.get('llm_evaluation_score') or 0) < 80]
                    elif score_filter == "Baixo (<60)":
                        filtered_results = [r for r in filtered_results if 0 < (r.get('llm_evaluation_score') or 0) < 60]
                    elif score_filter == "Sem avaliação":
                        filtered_results = [r for r in filtered_results if not r.get('llm_evaluation_score')]
                
                st.caption(f"Mostrando {len(filtered_results)} de {len(results)} resultados")
                
                st.divider()
                
                # Export button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("📥 Exportar CSV"):
                        csv_data = ui.call_api(lambda: api.export_results_to_csv(run_id=run_id))
                        if csv_data:
                            st.download_button(
                                label="⬇️ Download CSV",
                                data=csv_data,
                                file_name=f"evaluation_results_run{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                
                results = filtered_results
                
                # Show results
                for i, result in enumerate(results):
                    score_color = "🟢" if (result.get('llm_evaluation_score') or 0) >= 80 else "🟡" if (result.get('llm_evaluation_score') or 0) >= 60 else "🔴"
                    
                    # Build expander title with mandato and template info
                    mandato_info = result.get('mandato_nome', 'N/A')
                    template_info = result.get('template_description', 'Template Padrão')
                    
                    expander_title = f"{score_color} {result['case_name']} - Score: {result.get('llm_evaluation_score', 'N/A')}/100"
                    
                    with st.expander(expander_title, expanded=(i == 0)):
                        # Key info row
                        info_col1, info_col2, info_col3 = st.columns(3)
                        with info_col1:
                            st.markdown(f"**👤 Mandato:** {mandato_info}")
                        with info_col2:
                            st.markdown(f"**📝 Template:** {template_info}")
                        with info_col3:
                            st.markdown(f"**⏱️ Tempo:** {result.get('execution_time_ms', 'N/A')} ms")
                        
                        st.divider()
                        
                        # Case info
                        st.markdown(f"**Tipo de Teste:** {TEST_TYPES.get(result['case_test_type'], result['case_test_type'])}")
                        
                        # Input - Structured view
                        st.markdown("**📥 Input:**")
                        input_data = result['case_input_data']
                        
                        # Get mandato info if mandato_id is present
                        if 'mandato_id' in input_data:
                            mandato_info = ui.call_api(lambda: api.list_mandatos_for_dropdown())
                            if mandato_info:
                                mandato = next((m for m in mandato_info if m['id'] == input_data['mandato_id']), None)
                                if mandato:
                                    st.markdown(f"**Mandato:** {mandato.get('nome_parlamentar', 'N/A')} - {mandato.get('casa_legislativa', 'N/A')}")
                        
                        # Show main text field
                        if 'input_text' in input_data:
                            st.markdown("**Texto:**")
                            with st.container(border=True):
                                st.markdown(input_data['input_text'])
                        
                        # Show extra parameters if any
                        extra_params = {k: v for k, v in input_data.items() if k not in ['mandato_id', 'input_text']}
                        if extra_params:
                            st.markdown("**➕ Parâmetros extras:**")
                            for key, value in extra_params.items():
                                st.markdown(f"- **{key}:** {value}")
                        
                        # Raw JSON
                        st.markdown("**🔍 JSON completo do input:**")
                        with st.container(border=True):
                            st.json(input_data)
                        
                        # Expected vs Actual
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📋 Saída Esperada:**")
                            if result.get('case_expected_output'):
                                expected_text = result['case_expected_output']
                                
                                # Render as markdown
                                with st.container(border=True):
                                    st.markdown(expected_text)
                            else:
                                st.info("Não definida")
                        
                        with col2:
                            st.markdown("**📤 Output:**")
                            if result.get('actual_output'):
                                actual_text = result['actual_output']
                                actual_json = None
                                
                                # First, check if actual_output is already a dict (not a string)
                                if isinstance(actual_text, dict):
                                    actual_json = actual_text
                                else:
                                    # Try to parse as JSON first (standard format)
                                    try:
                                        actual_json = json.loads(actual_text)
                                    except (json.JSONDecodeError, TypeError):
                                        # LEGACY FALLBACK: For old data stored as Python repr strings
                                        # New data from backend is stored as proper JSON
                                        try:
                                            import ast
                                            actual_json = ast.literal_eval(actual_text)
                                        except (ValueError, SyntaxError):
                                            actual_json = None
                                
                                # If we have a dict, try to extract main content
                                if isinstance(actual_json, dict):
                                    # Common response keys to check
                                    content_key = None
                                    for key in ["response", "content", "text", "output", "result", "oficio", "analise", "emenda"]:
                                        if key in actual_json:
                                            content_key = key
                                            break
                                    
                                    if content_key:
                                        main_content = actual_json[content_key]
                                        # Render main content as markdown
                                        with st.container(border=True):
                                            st.markdown(main_content)
                                        
                                        # Full JSON below
                                        st.markdown("**JSON completo:**")
                                        with st.container(border=True):
                                            st.json(actual_json)
                                    else:
                                        # No recognized key, show whole JSON
                                        with st.container(border=True):
                                            st.json(actual_json)
                                else:
                                    # Not JSON or couldn't parse, render as markdown
                                    with st.container(border=True):
                                        st.markdown(actual_text)
                            elif result.get('error_message'):
                                st.error(f"Erro: {result['error_message']}")
                            else:
                                st.warning("Sem saída")
                        
                        # LLM Evaluation
                        if result.get('llm_evaluation_analysis'):
                            st.markdown("**🤖 Avaliação da IA:**")
                            st.info(result['llm_evaluation_analysis'])
                            st.metric("Score da IA", f"{result.get('llm_evaluation_score', 'N/A')}/100")
                        
                        # Human Evaluation
                        st.markdown("**👤 Avaliação Humana:**")
                        human_eval = st.text_area(
                            "Avaliação Humana",
                            value=result.get('human_evaluation', ''),
                            placeholder="Adicione suas observações sobre este resultado...",
                            key=f"human_eval_{result['id']}",
                            label_visibility="collapsed"
                        )
                        
                        if st.button("💾 Salvar Avaliação", key=f"save_eval_{result['id']}"):
                            updated = ui.call_api(lambda: api.update_evaluation_result(
                                result['id'],
                                human_evaluation=human_eval
                            ))
                            if updated:
                                st.success("✓ Avaliação salva!")
    else:
        st.info("👆 Selecione um ID de execução acima ou execute uma nova avaliação na aba 'Executar Avaliações'")
