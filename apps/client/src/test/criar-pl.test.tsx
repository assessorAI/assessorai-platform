import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { toast } from "sonner";
import { CriarPl } from "@/features/criar-pl/criar-pl";
import { ProjetosReferenciaProvider, useProjetosReferencias } from "@/context/projetos-referencias.context";
import { useEffect } from "react";
import userEvent from "@testing-library/user-event";


jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("@/hooks/useMandato", () => ({
  useMandato: jest.fn(() => ({
    id: 123,
    nome_parlamentar: "Deputado Teste",
    casa_legislativa: "Câmara dos Deputados",
  })),
}));

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
          onChange([new File(["x"], "file.pdf", { type: "application/pdf" })])
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
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      full_markdown: "# Título\nConteúdo",
    }),
  });

  await fillAndSubmitForm();

  await waitFor(() => {
    expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
  });

  expect(screen.queryByText(FORM_LABEL_TEXT)).not.toBeInTheDocument();
}

const renderCriarPl = () => {
  return render(
    <ProjetosReferenciaProvider>
      <CriarPl />
    </ProjetosReferenciaProvider>
  );
};

describe("CriarPl - comportamento do accordion (hook real)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve colapsar o accordion quando receber um projeto de lei", async () => {
    renderCriarPl();

    expect(screen.getByText(FORM_LABEL_TEXT)).toBeInTheDocument();

    await gerarProjetoLeiUmaVez();
  });


  test("deve manter o accordion aberto quando não tiver projetoLei", () => {
    renderCriarPl();
    expect(screen.getByText(FORM_LABEL_TEXT)).toBeInTheDocument();
  });

  test("deve aparecer o loading quando o usuário clicar no botão de submit", async () => {
    renderCriarPl();

    (global.fetch as jest.Mock).mockImplementationOnce(
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

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        full_markdown: "# Título\nConteúdo",
      }),
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
    renderCriarPl();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        full_markdown: "# Projeto de Lei\nConteúdo do PL sem arquivos",
      }),
    });

    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei sobre proteção ambiental");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
    });
  });

  test("deve gerar um projeto de lei quando o usuário preenche o campo de textarea e o dragdrop com 1 arquivo", async () => {
    renderCriarPl();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        full_markdown: "# Projeto de Lei\nConteúdo do PL com 1 arquivo",
      }),
    });

    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei sobre educação");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });

    await userEvent.click(screen.getByLabelText("set-file"));

    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
    });
  });

  test("deve gerar um projeto de lei quando o usuário preenche o campo de textarea e o dragdrop com 3 arquivos", async () => {
    renderCriarPl();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        full_markdown: "# Projeto de Lei\nConteúdo do PL com 3 arquivos",
      }),
    });

    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei sobre saúde pública");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });

    await userEvent.click(screen.getByLabelText("set-3-files"));

    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
    });
  });

  test("se tiver projetos selecionados no contexto, deve incluir os projetos no drag drop em formato de arquivo", async () => {
    const mockProjetos = [
      {
        id: "1",
        title: "PL 123/2024",
        author: "Deputado Silva",
        house: "Câmara dos Deputados",
        subject: "Educação",
        chunk_text: "Texto do projeto 1",
        url: "http://example.com/1"
      },
      {
        id: "2",
        title: "PL 456/2024",
        author: "Senador Santos",
        house: "Senado Federal",
        subject: "Saúde",
        chunk_text: "Texto do projeto 2",
        url: "http://example.com/2"
      },
    ];

    const TestWrapperWithProjects = () => {
      const { setSelectedProjetos } = useProjetosReferencias();
      
      useEffect(() => {
        setSelectedProjetos(mockProjetos);
      // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);

      return <CriarPl />;
    };

    render(
      <ProjetosReferenciaProvider>
        <TestWrapperWithProjects />
      </ProjetosReferenciaProvider>
    );

    await waitFor(() => {
      const dragDrop = screen.getByTestId("drag-drop");
      expect(dragDrop).toHaveTextContent("true");
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        full_markdown: "# Projeto de Lei\nCom referências",
      }),
    });

    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei baseada em projetos anteriores");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
    });
  });
});

describe("CriarPl - Tratamento de Erros (refactor)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve exibir toast de erro quando a API retornar erro 400 (Bad Request)", async () => {
    
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({}),
    });

    renderCriarPl();

    await fillAndSubmitForm("Texto de teste");

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Dados inválidos. Verifique as informações e tente novamente."
      );
    });

    expect(screen.queryByText("Projeto de Lei gerado")).not.toBeInTheDocument();
    expect(screen.getByText(FORM_LABEL_TEXT)).toBeInTheDocument();
  });

  test("deve exibir toast de erro quando a API retornar erro 422 (Unprocessable Entity)", async () => {
    
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({}),
    });

    renderCriarPl();

    await fillAndSubmitForm("Texto com formato inválido");

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Dados fornecidos não puderam ser processados."
      );
    });

    expect(screen.queryByText("Projeto de Lei gerado")).not.toBeInTheDocument();
  });

  test("deve exibir toast de erro quando a API retornar erro 500 (Internal Server Error)", async () => {
    
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    renderCriarPl();

    // Preenche e submete o formulário
    await fillAndSubmitForm("Texto de teste");

    // Verifica que o toast de erro foi chamado
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });

    expect(screen.queryByLabelText("loading")).not.toBeInTheDocument();
    expect(screen.queryByText("Projeto de Lei gerado")).not.toBeInTheDocument();
  });

  test("deve exibir toast de erro quando houver falha de conexão de rede (status 503)", async () => {
    
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 503,
      json: async () => ({}),
    });

    renderCriarPl();

    // Preenche e submete o formulário
    await fillAndSubmitForm("Texto de teste");

    // Verifica que o toast de erro foi chamado
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro de conexão. Verifique sua internet e tente novamente."
      );
    });

    expect(screen.queryByText("Projeto de Lei gerado")).not.toBeInTheDocument();
  });

  test("deve exibir toast de erro quando houver falha de conexão de rede (TypeError)", async () => {
    
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new TypeError("Failed to fetch")
    );

    renderCriarPl();

    await fillAndSubmitForm("Texto de teste");

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro de conexão. Verifique sua internet e tente novamente."
      );
    });

    expect(screen.queryByLabelText("loading")).not.toBeInTheDocument();
    expect(screen.queryByText("Projeto de Lei gerado")).not.toBeInTheDocument();
  });

  test("deve exibir toast de erro genérico quando houver exceção inesperada", async () => {
    
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Unexpected error")
    );

    renderCriarPl();

    // Preenche e submete o formulário
    await fillAndSubmitForm("Texto de teste");

    // Verifica que o toast de erro foi chamado
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });

    expect(screen.queryByText("Projeto de Lei gerado")).not.toBeInTheDocument();
  });

  test("deve exibir toast de erro quando falhar ao enviar com arquivos anexados", async () => {
    
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    renderCriarPl();

    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.type(textarea, "Criar lei sobre educação");

    await userEvent.click(screen.getByLabelText("set-file"));

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });

    expect(screen.queryByText("Projeto de Lei gerado")).not.toBeInTheDocument();
  });

  test("deve permitir nova tentativa após exibir erro", async () => {
    
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    renderCriarPl();

    await fillAndSubmitForm("Primeiro texto");

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        full_markdown: "# Projeto de Lei\nConteúdo gerado",
      }),
    });

    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.clear(textarea);
    await userEvent.type(textarea, "Segundo texto");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Projeto de Lei gerado")).toBeInTheDocument();
    });
  });

  test("deve exibir toast de erro múltiplas vezes quando houver erros consecutivos", async () => {
    
    renderCriarPl();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({}),
    });

    await fillAndSubmitForm("Texto 1");

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Dados inválidos. Verifique as informações e tente novamente."
      );
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.clear(textarea);
    await userEvent.type(textarea, "Texto 2");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });

    expect(toast.error).toHaveBeenCalledTimes(2);
  });

  test("deve desabilitar o botão durante nova requisição após erro", async () => {
    
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    renderCriarPl();

    await fillAndSubmitForm("Texto teste");

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });

    (global.fetch as jest.Mock).mockImplementationOnce(
      () => new Promise(() => {})
    );

    const textarea = screen.getByLabelText(FORM_LABEL_TEXT);
    await userEvent.clear(textarea);
    await userEvent.type(textarea, "Novo texto");

    const submitBtn = screen.getByRole("button", {
      name: /Criar projeto com IA/i,
    });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(submitBtn).toBeDisabled();
    });

    expect(screen.getByLabelText("loading")).toBeInTheDocument();
  });
});

