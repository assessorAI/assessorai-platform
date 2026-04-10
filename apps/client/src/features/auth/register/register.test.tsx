import { buildRegisterRequest } from '@/lib/register.service';
import { getFieldsService } from '@/lib/get-fields.service';
import { FormDataRegister } from './register-step.context';
import { PermissionLevel } from '@/types/user.types';
import { cargoParlamentarEnum } from '@/types/mandato.types';

global.fetch = jest.fn();

describe('Register:', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockFormData: FormDataRegister = {
    first_name: 'João',
    last_name: 'Silva',
    role: 'Assessor Legislativo',
    email: 'joao.silva@exemplo.com',
    phone: '(11)98765-4321',
    
    nome_parlamentar: 'João Silva',
    uf: 'SP',
    municipio: 'São Paulo',
    cargo_parlamentar: cargoParlamentarEnum.VEREADOR,
    casa_legislativa: 'Câmara Municipal',
    partido: 'PT',
    
    perfil_mandato: 'Legislador',
    posicionamento_mandato: 'De esquerda',
    primeiro_mandato: true,
    
    password: 'Senha@123',
    confirm_password: 'Senha@123',
    lgpd_check: true,
  };

  describe('Cadastro bem-sucedido com dados completos', () => {
    it('deve construir corretamente o request com todos os dados dos steps', () => {
      const request = buildRegisterRequest(mockFormData);

      expect(request).toEqual({
        email: 'joao.silva@exemplo.com',
        password: 'Senha@123',
        first_name: 'João',
        last_name: 'Silva',
        phone: '(11)98765-4321',
        lgpd_check: 'true',
        permission_level: PermissionLevel.Manager,
        role: 'Assessor Legislativo',
      });
    });
  });

  describe('getCasaLegislativa', () => {
    it('deve retornar Câmara Municipal de Osasco, se município é Osasco, UF é São Paulo e cargo é vereador', () => {
      const result = getFieldsService.getCasaLegislativa('Vereador', 'São Paulo', 'Osasco');
      
      expect(result).toBe('Câmara Municipal de Osasco');
    });

    it('deve retornar Assembleia Legislativa do Estado de São Paulo, se município é Osasco, UF é São Paulo e cargo é deputado estadual', () => {
      const result = getFieldsService.getCasaLegislativa('Deputado Estadual', 'São Paulo', 'Osasco');
      
      expect(result).toBe('Assembleia Legislativa do Estado de São Paulo');
    });

    it('deve retornar Câmara dos Deputados, se município é Osasco, UF é São Paulo e cargo é deputado federal', () => {
      const result = getFieldsService.getCasaLegislativa('Deputado Federal', 'São Paulo', 'Osasco');
      
      expect(result).toBe('Câmara dos Deputados');
    });

    it('deve retornar Senado Federal, se município é Osasco, UF é São Paulo e cargo é Senador', () => {
      const result = getFieldsService.getCasaLegislativa('Senador', 'São Paulo', 'Osasco');
      
      expect(result).toBe('Senado Federal');
    });

    it('deve retornar Câmara Legislativa do Distrito Federal, se município é Brasília, UF é Distrito Federal e cargo é deputado estadual', () => {
      const result = getFieldsService.getCasaLegislativa('Deputado Estadual', 'Distrito Federal', 'Brasília');
      
      expect(result).toBe('Câmara Legislativa do Distrito Federal');
    });
  });
});
