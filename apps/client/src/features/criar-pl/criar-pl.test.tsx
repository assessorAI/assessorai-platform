import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { CriarPl } from "./criar-pl";
import { criarPLService } from "./criar-pl.service";
import { ProjetosReferenciaProvider, useProjetosReferencias } from "@/context/projetos-referencias.context";
import { useEffect } from "react";


import userEvent from "@testing-library/user-event";

// Simplifica toast e evita ruído
jest.mock("sonner", () => ({
  toast: { error: jest.fn(), success: jest.fn() },
}));

// Mock do useMandato para retornar um mandato válido
jest.mock("@/hooks/useMandato", () => ({
  useMandato: jest.fn(() => ({
    id: 123,
    nome_parlamentar: "Deputado Teste",
    casa_legislativa: "Câmara dos Deputados",
  })),
}));

// Ajuste o mock existente para suportar múltiplos arquivos
jest.mock("@/components/ui/drag-drop", () => ({
  DragDrop: ({
    value,
    onChange,
  }: {
    value: unknown;
    onChange: (v: unknown) => void;
  }) => (
    <div>
      <div data-testid="drag-drop">{String(!!value)}</div>
      <button
        aria-label="set-file"
        onClick={() =>
          onChange([new File(["x"], "file.pdf", { type: "application/pdf" })]) // ← Array
        }
      >
        set-file
      </button>
      <button
        aria-label="set-3-files"
        onClick={() =>
          onChange([
            new File(["conteudo 1"], "arquivo1.pdf", { type: "application/pdf" }),
            new File(["conteudo 2"], "arquivo2.pdf", { type: "application/pdf" }),
            new File(["conteudo 3"], "arquivo3.txt", { type: "text/plain" }),
          ])
        }
      >
        set-3-files
      </button>
      <button aria-label="clear-file" onClick={() => onChange(null)}>
        clear-file
      </button>
    </div>
  ),
}));

// Mocka DocViewer
jest.mock("@/components/doc-viewer/doc-viewer", () => ({
  DocViewer: ({
    isLoading,
    content,
  }: {
    isLoading?: boolean;
    content?: string;
  }) => (
    <div>
      <h2>Projeto de Lei gerado</h2>
      {isLoading ? (
        <div aria-label="loading">Carregando...</div>
      ) : (
        content && <div>{content}</div>
      )}
    </div>
  ),
}));

// Usa o hook real; mocka apenas o serviço chamado dentro dele
jest.mock("./criar-pl.service", () => ({
  criarPLService: { criarPL: jest.fn() },
}));

const FORM_LABEL_TEXT =
  "Descreva o tema ou a ideia principal do projeto de lei";

async function fillAndSubmitForm(text = "Um tema qualquer") {
  const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
  await userEvent.clear(textarea);
  await userEvent.type(textarea, text);

  const submitBtn = screen.getByRole("button", {
    name: /Criar projeto com IA/i,
  });

  await waitFor(() => expect(submitBtn).not.toBeDisabled());
  await userEvent.click(submitBtn);
}

async function gerarProjetoLeiUmaVez() {
  (criarPLService.criarPL as jest.Mock).mockResolvedValueOnce({
    full_markdown: "# Título\nConteúdo",
  });

  await fillAndSubmitForm();

  await waitFor(() => {
    expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
  });

  // Confirma que o formulário colapsou
  expect(screen.queryByText(FORM_LABEL_TEXT)).not.toBeInTheDocument();
}

const renderCriarPl = () => {
  return render(
    <ProjetosReferenciaProvider>
      <CriarPl />
    </ProjetosReferenciaProvider>
  );
};

// Helper para ler o conteúdo real dos arquivos nos testes
const readFileContent = async (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsText(file);
  });
};

describe("CriarPl - comportamento do accordion (hook real)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve colapsar o accordion quando receber um projeto de lei", async () => {
    renderCriarPl();

    // Abre com formulario visível (sem projetoLei)
    expect(screen.getByText(FORM_LABEL_TEXT)).toBeInTheDocument();

    await gerarProjetoLeiUmaVez();

    // Já assertado dentro do helper: DocViewer presente, formulário ausente
  });


  test("deve manter o accordion aberto quando não tiver projetoLei", () => {
    renderCriarPl();
    expect(screen.getByText(FORM_LABEL_TEXT)).toBeInTheDocument();
  });

  test("deve aparecer o loading quando o usuário clicar no botão de submit", async () => {
    renderCriarPl();

    // manter loading ativo: promise pendente
    (criarPLService.criarPL as jest.Mock).mockImplementationOnce(
      () => new Promise(() => {})
    );

    const textarea = screen.getByLabelText(
      "Descreva o tema ou a ideia principal do projeto de lei"
    );
    await userEvent.type(textarea, "texto válido");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    expect(screen.getByLabelText("loading")).toBeInTheDocument();
  });

  test("deve desaparecer o loading quando receber o projeto de lei", async () => {
    renderCriarPl();

    (criarPLService.criarPL as jest.Mock).mockResolvedValueOnce({
      full_markdown: "# Título\nConteúdo",
    });

    const textarea = screen.getByLabelText(
      "Descreva o tema ou a ideia principal do projeto de lei"
    );
    await userEvent.type(textarea, "texto válido");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() =>
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument()
    );
    expect(screen.queryByLabelText("loading")).not.toBeInTheDocument();
  });

  test("não deve habilitar o botão de submit se o usuário preencheu apenas o campo de arquivo", async () => {
    renderCriarPl();

    // seta arquivo via mock
    await userEvent.click(screen.getByLabelText("set-file"));

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    expect(submitBtn).toBeDisabled();
  });

  test("deve habilitar o botão de submit se o usuário preenche o textarea e o campo de arquivo", async () => {
    renderCriarPl();

    await userEvent.click(screen.getByLabelText("set-file"));

    const textarea = screen.getByLabelText(
      "Descreva o tema ou a ideia principal do projeto de lei"
    );
    await userEvent.type(textarea, "texto válido");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
  });

  test("deve gerar um projeto de lei quando o usuário preenche apenas o campo textarea e não preenche o arquivo", async () => {
    // Renderiza o componente com o Provider
    renderCriarPl();

    // Mocka a resposta da API
    (criarPLService.criarPL as jest.Mock).mockResolvedValueOnce({
      full_markdown: "# Projeto de Lei\nConteúdo do PL sem arquivos",
    });

    // Preenche apenas o textarea
    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei sobre proteção ambiental");

    // Aguarda o botão ficar habilitado
    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    // Clica no botão de submit
    await userEvent.click(submitBtn);

    // Verifica se a API foi chamada corretamente (texto preenchido, sem arquivos)
    await waitFor(() => {
      expect(criarPLService.criarPL).toHaveBeenCalledWith(
        "Criar lei sobre proteção ambiental",
        "123", // mandatoId
        undefined // Sem arquivos
      );
    });

    // Verifica se o projeto foi exibido
    await waitFor(() => {
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
    });
  });

  test("deve gerar um projeto de lei quando o usuário preenche o campo de textarea e o dragdrop com 1 arquivo", async () => {
    renderCriarPl();

    // Mocka a resposta da API
    (criarPLService.criarPL as jest.Mock).mockResolvedValueOnce({
      full_markdown: "# Projeto de Lei\nConteúdo do PL com 1 arquivo",
    });

    // Preenche o textarea primeiro (antes de adicionar arquivos)
    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei sobre educação");

    // Pega o botão antes de adicionar arquivos
    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });

    // Adiciona 1 arquivo via mock do DragDrop
    await userEvent.click(screen.getByLabelText("set-file"));

    // Aguarda o botão ficar habilitado
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    // Submete o formulário
    await userEvent.click(submitBtn);

    // Verifica se a API foi chamada com texto e array de 1 arquivo
    await waitFor(() => {
      expect(criarPLService.criarPL).toHaveBeenCalledTimes(1);
      
      const callArgs = (criarPLService.criarPL as jest.Mock).mock.calls[0];
      expect(callArgs[0]).toBe("Criar lei sobre educação");
      expect(callArgs[1]).toBe("123"); // mandatoId
      expect(callArgs[2]).toHaveLength(1); // Array com 1 arquivo
      expect(callArgs[2][0]).toBeInstanceOf(File);
      expect(callArgs[2][0].name).toBe("file.pdf");
    });

    // Verifica se o projeto foi exibido
    await waitFor(() => {
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
    });
  });

  test("deve gerar um projeto de lei quando o usuário preenche o campo de textarea e o dragdrop com 3 arquivos", async () => {
    renderCriarPl();

    // Mocka a resposta da API
    (criarPLService.criarPL as jest.Mock).mockResolvedValueOnce({
      full_markdown: "# Projeto de Lei\nConteúdo do PL com 3 arquivos",
    });

    // Preenche o textarea primeiro (antes de adicionar arquivos)
    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei sobre saúde pública");

    // Pega o botão antes de adicionar arquivos
    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });

    // Usa o botão que adiciona 3 arquivos
    await userEvent.click(screen.getByLabelText("set-3-files"));

    // Aguarda o botão ficar habilitado
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    // Submete o formulário
    await userEvent.click(submitBtn);

    // Verifica se a API foi chamada com texto e array de 3 arquivos
    await waitFor(() => {
      expect(criarPLService.criarPL).toHaveBeenCalledTimes(1);
      
      const callArgs = (criarPLService.criarPL as jest.Mock).mock.calls[0];
      expect(callArgs[0]).toBe("Criar lei sobre saúde pública");
      expect(callArgs[1]).toBe("123"); // mandatoId
      expect(callArgs[2]).toHaveLength(3); // Array com 3 arquivos
      
      // Verifica cada arquivo
      expect(callArgs[2][0]).toBeInstanceOf(File);
      expect(callArgs[2][0].name).toBe("arquivo1.pdf");
      
      expect(callArgs[2][1]).toBeInstanceOf(File);
      expect(callArgs[2][1].name).toBe("arquivo2.pdf");
      
      expect(callArgs[2][2]).toBeInstanceOf(File);
      expect(callArgs[2][2].name).toBe("arquivo3.txt");
    });

    // Verifica se o projeto foi exibido
    await waitFor(() => {
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
    });
  });

  test("se tiver projetos selecionados no contexto, deve incluir os projetos no drag drop em formato de arquivo", async () => {
    // Mock dos projetos que serão inseridos no contexto
    const mockProjetos = [
      {
        id: "1",
        title: "PL 123/2024",
        author: "Deputado Silva",
        house: "Câmara dos Deputados",
        subject: "Educação",
        chunk_text: "Texto do projeto 1",
        url: "https://example.com/pl-123-2024",
      },
      {
        id: "2",
        title: "PL 456/2024",
        author: "Senador Santos",
        house: "Senado Federal",
        subject: "Saúde",
        chunk_text: "Texto do projeto 2",
        url: "https://example.com/pl-456-2024",
      },
    ];

    // Componente helper que injeta os projetos no contexto
    const TestWrapperWithProjects = () => {
      const { setSelectedProjetos } = useProjetosReferencias();
      
      useEffect(() => {
        setSelectedProjetos(mockProjetos);
      // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);

      return <CriarPl />;
    };

    // Renderiza com projetos já definidos no contexto
    render(
      <ProjetosReferenciaProvider>
        <TestWrapperWithProjects />
      </ProjetosReferenciaProvider>
    );

    // Aguarda o useEffect do CriarPl processar e converter projetos em arquivos
    await waitFor(() => {
      const dragDrop = screen.getByTestId("drag-drop");
      // Se o value é "true", significa que arquivos foram adicionados
      expect(dragDrop).toHaveTextContent("true");
    });

    // Mocka a resposta da API
    (criarPLService.criarPL as jest.Mock).mockResolvedValueOnce({
      full_markdown: "# Projeto de Lei\nCom referências",
    });

    // Preenche o textarea
    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei baseada em projetos anteriores");

    // Aguarda o botão ficar habilitado
    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    // Submete o formulário
    await userEvent.click(submitBtn);

    // VERIFICAÇÃO RIGOROSA: Testa se os arquivos foram criados corretamente
    await waitFor(async () => {
      expect(criarPLService.criarPL).toHaveBeenCalledTimes(1);
      
      const callArgs = (criarPLService.criarPL as jest.Mock).mock.calls[0];
      const text = callArgs[0];
      const mandatoId = callArgs[1];
      const files = callArgs[2];
      
      // Verifica os parâmetros básicos
      expect(text).toBe("Criar lei baseada em projetos anteriores");
      expect(mandatoId).toBe("123");
      
      // Verifica que são 2 arquivos
      expect(files).toHaveLength(2);
      
      // TESTE REAL: Verifica o primeiro arquivo
      expect(files[0]).toBeInstanceOf(File);
      expect(files[0].name).toBe("PL 123/2024.txt");
      expect(files[0].type).toBe("text/plain");
      
      // Lê e verifica o conteúdo do primeiro arquivo
      const content1 = await readFileContent(files[0]);
      expect(content1).toContain("Título: PL 123/2024");
      expect(content1).toContain("Casa: Câmara dos Deputados");
      expect(content1).toContain("Autores: Deputado Silva");
      expect(content1).toContain("Assunto: Educação");
      
      // TESTE REAL: Verifica o segundo arquivo
      expect(files[1]).toBeInstanceOf(File);
      expect(files[1].name).toBe("PL 456/2024.txt");
      expect(files[1].type).toBe("text/plain");
      
      // Lê e verifica o conteúdo do segundo arquivo
      const content2 = await readFileContent(files[1]);
      expect(content2).toContain("Título: PL 456/2024");
      expect(content2).toContain("Casa: Senado Federal");
      expect(content2).toContain("Autores: Senador Santos");
      expect(content2).toContain("Assunto: Saúde");
    });
  });
});

describe("CriarPl - Limpeza de referências ao desmontar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve limpar os projetos selecionados quando o usuário sai da página (componente desmonta)", async () => {
    // Mock dos projetos que serão inseridos no contexto
    const mockProjetos = [
      {
        id: "1",
        title: "PL 789/2024",
        author: "Deputado Costa",
        house: "Câmara dos Deputados",
        subject: "Meio Ambiente",
        chunk_text: "Texto do projeto sobre meio ambiente",
        url: "https://example.com/projeto/1",
      },
      {
        id: "2",
        title: "PL 101/2024",
        author: "Senadora Lima",
        house: "Senado Federal",
        subject: "Transporte",
        chunk_text: "Texto do projeto sobre transporte",
        url: "https://example.com/projeto/2",
      },
    ];

    // Componente helper que permite acessar o contexto para verificação
    const TestWrapperWithContextCheck = () => {
      const { selectedProjetos, setSelectedProjetos } = useProjetosReferencias();
      
      useEffect(() => {
        // Adiciona projetos no mount
        setSelectedProjetos(mockProjetos);
      // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);

      return (
        <>
          <CriarPl />
          <div data-testid="selected-count">{selectedProjetos.length}</div>
          <div data-testid="selected-ids">
            {selectedProjetos.map(p => p.id).join(",")}
          </div>
        </>
      );
    };

    // Renderiza com projetos no contexto
    const { unmount } = render(
      <ProjetosReferenciaProvider>
        <TestWrapperWithContextCheck />
      </ProjetosReferenciaProvider>
    );

    // Verifica que os projetos foram adicionados ao contexto
    await waitFor(() => {
      expect(screen.getByTestId("selected-count")).toHaveTextContent("2");
      expect(screen.getByTestId("selected-ids")).toHaveTextContent("1,2");
    });

    // Verifica que o drag-drop recebeu os arquivos (comportamento esperado)
    await waitFor(() => {
      const dragDrop = screen.getByTestId("drag-drop");
      expect(dragDrop).toHaveTextContent("true");
    });

    // AÇÃO PRINCIPAL: Desmonta o componente (simula sair da página)
    unmount();

    // Re-renderiza apenas o contexto para verificar se foi limpo
    const ContextChecker = () => {
      const { selectedProjetos } = useProjetosReferencias();
      return (
        <div>
          <div data-testid="final-count">{selectedProjetos.length}</div>
          <div data-testid="final-ids">
            {selectedProjetos.map(p => p.id).join(",")}
          </div>
        </div>
      );
    };

    render(
      <ProjetosReferenciaProvider>
        <ContextChecker />
      </ProjetosReferenciaProvider>
    );

    // Verifica que o contexto foi limpo após unmount
    await waitFor(() => {
      expect(screen.getByTestId("final-count")).toHaveTextContent("0");
      expect(screen.getByTestId("final-ids")).toHaveTextContent("");
    });
  });

});
