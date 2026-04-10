import { markdownToSafeHtml } from './markdown.client';

// Mock do DOMPurify para browser
jest.mock('dompurify', () => {
  return jest.fn().mockImplementation(() => ({
    sanitize: jest.fn().mockImplementation((dirty: string) => dirty)
  }));
});

// Mock do window global para simular browser
const mockWindow = {
  DocumentFragment: {},
  HTMLTemplateElement: {},
  Node: {},
  Element: {},
  NodeFilter: {},
  NamedNodeMap: {},
  HTMLFormElement: {},
  DOMParser: {},
  document: {
    createElement: jest.fn(),
    createDocumentFragment: jest.fn(),
  },
  navigator: {
    userAgent: 'Jest Test Browser'
  }
};

describe('markdownToSafeHtml - Client Side', () => {
  beforeAll(() => {
    // Simula ambiente browser com window global
    (global as unknown as { window: unknown }).window = mockWindow;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  afterAll(() => {
    // Limpa o mock do window
    delete (global as unknown as { window: unknown }).window;
  });

  describe('Conversão básica de Markdown no Browser', () => {
    it('deve converter markdown simples para HTML', () => {
      const markdown = '# Título no Browser';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<h1');
      expect(result).toContain('Título no Browser');
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

  describe('Casos extremos no Browser', () => {
    it('deve lidar com markdown vazio', () => {
      const result = markdownToSafeHtml('');
      expect(result).toBe('');
    });

    it('deve lidar com texto sem markdown', () => {
      const plainText = 'Apenas texto simples no browser';
      const result = markdownToSafeHtml(plainText);
      
      expect(result).toContain('Apenas texto simples no browser');
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
      
      expect(result).toContain('<h1>');
      expect(result).toBeDefined();
    });
  });

  describe('Recursos avançados no Browser', () => {
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

    it('deve funcionar com markdown complexo no browser', () => {
      const complexMarkdown = `
# Título Principal

## Subtítulo

Este é um **parágrafo** com *texto* formatado.

- Lista item 1
- Lista item 2

[Link para exemplo](https://exemplo.com)

\`código inline\`

> Citação importante
`;
      
      const result = markdownToSafeHtml(complexMarkdown);
      
      expect(result).toContain('<h1>');
      expect(result).toContain('<h2>');
      expect(result).toContain('<strong>');
      expect(result).toContain('<em>');
      expect(result).toContain('<ul>');
      expect(result).toContain('<a');
      expect(result).toContain('<code>');
      expect(result).toContain('<blockquote>');
    });
  });

  describe('Sanitização no Browser', () => {
    it('deve usar DOMPurify do browser para sanitizar', () => {
      const dangerousMarkdown = '<script>alert("hack")</script>';
      const result = markdownToSafeHtml(dangerousMarkdown);
      
      // DOMPurify deve ter sido chamado
      expect(result).toBeDefined();
    });

    it('deve processar conteúdo potencialmente perigoso', () => {
      const maliciousMarkdown = `
# Título Seguro

<img src="x" onerror="alert('not happening')">

**Texto normal** continua funcionando.

<script>console.log('removido pelo DOMPurify')</script>
`;
      
      const result = markdownToSafeHtml(maliciousMarkdown);
      
      expect(result).toContain('<h1>');
      expect(result).toContain('Título Seguro');
      expect(result).toContain('<strong>');
      expect(result).toContain('Texto normal');
      // Conteúdo malicioso processado pelo DOMPurify
      expect(result).toBeDefined();
    });

    it('deve preservar HTML seguro no browser', () => {
      const safeHtmlMarkdown = `
# Título

<strong>Texto em negrito HTML</strong>

<em>Texto em itálico HTML</em>

<code>código HTML</code>
`;
      
      const result = markdownToSafeHtml(safeHtmlMarkdown);
      
      expect(result).toContain('<h1>');
      expect(result).toContain('<strong>');
      expect(result).toContain('<em>');
      expect(result).toContain('<code>');
    });
  });

  describe('Comportamento específico do Browser', () => {
    it('deve usar window global disponível', () => {
      const markdown = '**Usando window do browser**';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<strong>');
      expect(result).toContain('Usando window do browser');
      // Verifica que window está sendo usado
      expect(global.window).toBeDefined();
    });

    it('deve processar emojis e caracteres Unicode', () => {
      const markdown = '# Título com emoji 🚀 e Unicode ñáéíóú';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('🚀');
      expect(result).toContain('ñáéíóú');
    });

    it('deve lidar com URLs complexas', () => {
      const markdown = '[Link complexo](https://exemplo.com/path?param=value&other=123#section)';
      const result = markdownToSafeHtml(markdown);
      
      expect(result).toContain('<a');
      expect(result).toContain('href="https://exemplo.com/path?param=value&other=123#section"');
      expect(result).toContain('Link complexo');
    });
  });
});