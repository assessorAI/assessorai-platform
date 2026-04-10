#!/usr/bin/env python3
"""
Script manual para testar funcionalidade de gerenciamento de templates de prompt.
Testa todos os endpoints REST sem precisar do Docker postgres.
"""

import requests
import json
import time
from pprint import pprint

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def get_admin_token():
    """Obter token de autenticação do admin"""
    print_info("Autenticando como admin...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_success(f"Autenticado com sucesso!")
        return token
    else:
        print_error(f"Falha na autenticação: {response.status_code}")
        print(response.text)
        return None

def test_list_template_types(headers):
    """Teste 1: Listar tipos de templates"""
    print_info("\n=== Teste 1: Listar tipos de templates ===")
    response = requests.get(f"{BASE_URL}/admin/prompts/types", headers=headers)
    
    if response.status_code == 200:
        types = response.json()
        print_success(f"Encontrados {len(types)} tipos de templates")
        for t in types:
            print(f"  - {t['type']}: {t['display_name']} (versions: {t['db_versions_count']}, default: v{t['default_version'] or 'none'})")
        return types
    else:
        print_error(f"Falha ao listar tipos: {response.status_code}")
        print(response.text)
        return None

def test_create_template(headers, template_type="generate_oficio"):
    """Teste 2: Criar nova versão de template"""
    print_info(f"\n=== Teste 2: Criar template '{template_type}' ===")
    
    payload = {
        "template_type": template_type,
        "content": f"# Template de Teste\n\nEste é um template de teste para {template_type}.\n\nVariáveis: {{{{mandato}}}}, {{{{user}}}}\n\nConteúdo aqui...",
        "description": f"Versão de teste criada automaticamente em {time.strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/prompts/",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        template = response.json()
        print_success(f"Template criado: ID={template['id']}, version={template['version']}")
        print(f"  - created_at: {template['created_at']}")
        print(f"  - is_default: {template['is_default']}")
        print(f"  - is_active: {template['is_active']}")
        return template
    else:
        print_error(f"Falha ao criar template: {response.status_code}")
        print(response.text)
        return None

def test_list_all_templates(headers):
    """Teste 3: Listar todos os templates"""
    print_info("\n=== Teste 3: Listar todos os templates ===")
    response = requests.get(f"{BASE_URL}/admin/prompts/", headers=headers)
    
    if response.status_code == 200:
        templates = response.json()
        print_success(f"Encontrados {len(templates)} templates no total")
        for t in templates:
            status = "DEFAULT" if t['is_default'] else ("ACTIVE" if t['is_active'] else "INACTIVE")
            print(f"  - [{status}] {t['template_type']} v{t['version']} (ID: {t['id']})")
        return templates
    else:
        print_error(f"Falha ao listar templates: {response.status_code}")
        print(response.text)
        return None

def test_get_template(headers, template_type, version):
    """Teste 4: Obter template específico"""
    print_info(f"\n=== Teste 4: Obter template {template_type} v{version} ===")
    response = requests.get(f"{BASE_URL}/admin/prompts/{template_type}/{version}", headers=headers)
    
    if response.status_code == 200:
        template = response.json()
        print_success(f"Template obtido: {template['template_type']} v{template['version']}")
        print(f"  - Content length: {len(template['content'])} caracteres")
        print(f"  - Description: {template['description']}")
        return template
    else:
        print_error(f"Falha ao obter template: {response.status_code}")
        print(response.text)
        return None

def test_set_default(headers, template_id):
    """Teste 5: Definir template como padrão"""
    print_info(f"\n=== Teste 5: Definir template ID={template_id} como padrão ===")
    response = requests.post(
        f"{BASE_URL}/admin/prompts/{template_id}/set-default",
        headers=headers
    )
    
    if response.status_code == 200:
        template = response.json()
        print_success(f"Template definido como padrão: {template['template_type']} v{template['version']}")
        print(f"  - is_default: {template['is_default']}")
        return template
    else:
        print_error(f"Falha ao definir padrão: {response.status_code}")
        print(response.text)
        return None

def test_update_template(headers, template_id):
    """Teste 6: Atualizar metadados do template"""
    print_info(f"\n=== Teste 6: Atualizar template ID={template_id} ===")
    
    payload = {
        "description": f"Descrição atualizada em {time.strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    response = requests.put(
        f"{BASE_URL}/admin/prompts/{template_id}",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        template = response.json()
        print_success(f"Template atualizado: {template['description']}")
        return template
    else:
        print_error(f"Falha ao atualizar template: {response.status_code}")
        print(response.text)
        return None

def test_create_second_version(headers, template_type):
    """Teste 7: Criar segunda versão do mesmo tipo"""
    print_info(f"\n=== Teste 7: Criar segunda versão de '{template_type}' ===")
    
    payload = {
        "template_type": template_type,
        "content": f"# Template v2\n\nEsta é a SEGUNDA versão do template {template_type}.\n\nMelhorias:\n- Nova estrutura\n- Mais variáveis\n\nVariáveis: {{{{mandato}}}}, {{{{user}}}}, {{{{data}}}}\n\nConteúdo aprimorado...",
        "description": f"Segunda versão - teste de incremento automático"
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/prompts/",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        template = response.json()
        print_success(f"Segunda versão criada: version={template['version']}")
        return template
    else:
        print_error(f"Falha ao criar segunda versão: {response.status_code}")
        print(response.text)
        return None

def test_get_file_content(headers, template_type="generate_oficio"):
    """Teste 8: Obter conteúdo do arquivo (fallback)"""
    print_info(f"\n=== Teste 8: Obter conteúdo do arquivo '{template_type}.md' ===")
    response = requests.get(
        f"{BASE_URL}/admin/prompts/{template_type}/file-content",
        headers=headers
    )
    
    if response.status_code == 200:
        file_content = response.json()
        print_success(f"Arquivo encontrado: {len(file_content['content'])} caracteres")
        print(f"  - Source: {file_content['source']}")
        return file_content
    else:
        print_error(f"Falha ao obter arquivo: {response.status_code}")
        print(response.text)
        return None

def test_soft_delete(headers, template_id):
    """Teste 9: Soft delete de template"""
    print_info(f"\n=== Teste 9: Soft delete do template ID={template_id} ===")
    response = requests.delete(
        f"{BASE_URL}/admin/prompts/{template_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        template = response.json()
        print_success(f"Template desativado: is_active={template['is_active']}")
        return template
    else:
        print_error(f"Falha ao desativar template: {response.status_code}")
        print(response.text)
        return None

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("  TESTE MANUAL - SISTEMA DE TEMPLATES DE PROMPT")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Autenticar
    token = get_admin_token()
    if not token:
        print_error("\nNão foi possível autenticar. Verifique se:")
        print("  1. O servidor está rodando em http://localhost:8000")
        print("  2. Existe um usuário admin com email 'admin@example.com' e senha 'admin123'")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Executar testes
    test_list_template_types(headers)
    
    template1 = test_create_template(headers, "generate_oficio")
    if not template1:
        print_error("\nFalha crítica ao criar template. Abortando testes.")
        return
    
    test_list_all_templates(headers)
    test_get_template(headers, template1['template_type'], template1['version'])
    test_set_default(headers, template1['id'])
    test_update_template(headers, template1['id'])
    
    template2 = test_create_second_version(headers, "generate_oficio")
    if template2:
        print_info(f"\nVerificando incremento de versão: v{template1['version']} -> v{template2['version']}")
        if template2['version'] == template1['version'] + 1:
            print_success("Versão incrementada corretamente!")
        else:
            print_error(f"Erro no incremento: esperado v{template1['version']+1}, obtido v{template2['version']}")
    
    test_get_file_content(headers, "generate_oficio")
    
    # Soft delete apenas da versão 2 (não default)
    if template2 and not template2['is_default']:
        test_soft_delete(headers, template2['id'])
    
    # Resumo final
    print(f"\n{Colors.BLUE}{'='*60}")
    print("  RESUMO DOS TESTES")
    print(f"{'='*60}{Colors.RESET}")
    
    types = test_list_template_types(headers)
    all_templates = test_list_all_templates(headers)
    
    print_info(f"\nTotal de tipos: {len(types) if types else 0}")
    print_info(f"Total de templates criados: {len(all_templates) if all_templates else 0}")
    
    print(f"\n{Colors.GREEN}{'='*60}")
    print("  TESTES CONCLUÍDOS!")
    print(f"{'='*60}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
