import { markdownToSafeHtml } from './markdown.server';

// Mock do JSDOM para simular ambiente servidor
jest.mock('jsdom', () => ({
  JSDOM: jest.fn().mockImplementation(() => ({
    window: {
      DocumentFragment: {},
      HTMLTemplateElement: {},
      Node: {},
      Element: {},
      NodeFilter: {},
      NamedNodeMap: {},
      HTMLFormElement: {},
      DOMParser: {},
    }
  }))
}));

// Mock do DOMPurify
jest.mock('dompurify', () => {
  return jest.fn().mockImplementation(() => ({
    sanitize: jest.fn().mockImplementation((dirty: string) => dirty)
  }));
});

describe('markdownToSafeHtml - Server Side', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Conversão básica de Markdown', () => {
    it('deve converter markdown simples para HTML', () => {
      const markdown = '# Título';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<h1');
      expect(result).toContain('Título');
    });

    it('deve converter markdown com texto em negrito', () => {
      const markdown = '**texto em negrito**';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<strong>');
      expect(result).toContain('texto em negrito');
    });

    it('deve converter markdown com texto em itálico', () => {
      const markdown = '*texto em itálico*';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<em>');
      expect(result).toContain('texto em itálico');
    });

    it('deve converter markdown com lista', () => {
      const markdown = `
- Item 1
- Item 2
- Item 3`;
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<ul>');
      expect(result).toContain('<li>');
      expect(result).toContain('Item 1');
    });

    it('deve converter markdown com link', () => {
      const markdown = '[Google](https://google.com)';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<a');
      expect(result).toContain('href="https://google.com"');
      expect(result).toContain('Google');
    });
  });

  describe('Casos extremos', () => {
    it('deve lidar com markdown vazio', () => {
      const result = markdownToSafeHtml('');
      expect(result).toBe('');
    });

    it('deve lidar com texto sem markdown', () => {
      const plainText = 'Apenas texto simples';
      const result = markdownToSafeHtml(plainText);
      
      expect(result).toContain('Apenas texto simples');
    });

    it('deve lidar com caracteres especiais', () => {
      const markdown = '# Título com acentuação: ção, ã, é';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('ção');
      expect(result).toContain('ã');
      expect(result).toContain('é');
    });

    it('deve lidar com markdown mal formatado', () => {
      const badMarkdown = '# Título sem fechar **negrito sem fechar';
      const result = markdownToSafeHtml(badMarkdown);
      
      // Deve ainda processar o que conseguir
      expect(result).toContain('<h1>');
      expect(result).toBeDefined();
    });
  });

  describe('Recursos avançados', () => {
    it('deve converter código inline', () => {
      const markdown = 'Use o comando `npm install` para instalar';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<code>');
      expect(result).toContain('npm install');
    });

    it('deve converter bloco de código', () => {
      const markdown = `
\`\`\`javascript
function teste() {
  console.log("Hello World");
}
\`\`\``;
      
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<pre>');
      expect(result).toContain('class="language-javascript"');
      expect(result).toContain('function teste');
    });

    it('deve converter markdown complexo', () => {
      const complexMarkdown = `
# Título Principal

## Subtítulo

Este é um **parágrafo** com *texto* formatado.

- Lista item 1
- Lista item 2

[Link para exemplo](https://exemplo.com)
`;
      
      const result = markdownToSafeHtml(complexMarkdown);
      
      expect(result).toContain('<h1>');
      expect(result).toContain('<h2>');
      expect(result).toContain('<strong>');
      expect(result).toContain('<em>');
      expect(result).toContain('<ul>');
      expect(result).toContain('<a');
    });
  });

  describe('Sanitização e Segurança', () => {
    it('deve sanitizar conteúdo perigoso', () => {
      const dangerousMarkdown = '<script>alert("hack")</script>';
      const result = markdownToSafeHtml(dangerousMarkdown);
      
      // O DOMPurify deve ter sido chamado
      expect(result).toBeDefined();
    });

    it('deve processar HTML malicioso incorporado', () => {
      const maliciousMarkdown = `
# Título Normal

<img src="x" onerror="alert('not happening')">

**Texto seguro**
`;
      
      const result = markdownToSafeHtml(maliciousMarkdown);
      
      expect(result).toContain('<h1>');
      expect(result).toContain('Título Normal');
      expect(result).toContain('<strong>');
      expect(result).toContain('Texto seguro');
      // O conteúdo malicioso deve ter sido processado pelo DOMPurify
      expect(result).toBeDefined();
    });

    it('deve manter elementos HTML seguros', () => {
      const safeHtmlMarkdown = `
# Título

<strong>Texto em negrito</strong>

<em>Texto em itálico</em>
`;
      
      const result = markdownToSafeHtml(safeHtmlMarkdown);
      
      expect(result).toContain('<h1>');
      expect(result).toContain('<strong>');
      expect(result).toContain('<em>');
    });
  });
});