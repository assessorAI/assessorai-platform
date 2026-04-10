// src/test/analise-constitucionalidade.test.tsx
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AnaliseConstitucionalidade } from "@/features/analise-constitucionalidade/analise-constitucionalidade";
import { toast } from "sonner";

// Mock do toast para verificar se foi chamado
jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

// Mock do useMandato para retornar um mandato válido
jest.mock("@/hooks/useMandato", () => ({
  useMandato: jest.fn(() => ({
    id: 2,
    nome_parlamentar: "Deputado Teste",
    casa_legislativa: "Câmara dos Deputados",
  })),
}));

// Mock do DragDrop para simular upload de arquivo
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
        aria-label="upload-file"
        onClick={() =>
          onChange(
            new File(["conteúdo"], "projeto-lei.pdf", {
              type: "application/pdf",
            })
          )
        }
      >
        Upload arquivo
      </button>
      <button aria-label="clear-file" onClick={() => onChange(null)}>
        Limpar
      </button>
    </div>
  ),
}));

// Mock do CardCollapsible para simplificar o teste
jest.mock("@/components/card-collapsible/card-collapsible", () => ({
  CardCollapsible: ({
    title,
    content,
  }: {
    title: string;
    content: React.ReactNode;
  }) => (
    <div>
      <h2>{title}</h2>
      {content}
    </div>
  ),
}));

// Mock do CardPlaceholder
jest.mock("@/components/card-placeholder/card-placeholder", () => ({
  CardPlaceholder: ({ text }: { text: string }) => <div>{text}</div>,
}));

// Mock do CardLoading
jest.mock("@/components/card-loading/card-loading", () => ({
  CardLoading: () => <div>Carregando análise...</div>,
}));

describe("AnaliseConstitucionalidade - Teste Integrado", () => {
  let originalFetch: typeof global.fetch;

  beforeAll(() => {
    // Salva o fetch original
    originalFetch = global.fetch;
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterAll(() => {
    // Restaura o fetch original
    global.fetch = originalFetch;
  });

  describe("Cenário de erro", () => {
    it("deve mostrar toast de erro quando API externa retornar erro 422", async () => {
      // Mock do fetch global para simular erro do backend
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({
          error: "Dados fornecidos não puderam ser processados.",
        }),
      }) as jest.Mock;

      // Renderiza o componente
      render(<AnaliseConstitucionalidade />);

      // Verifica que o placeholder está visível
      expect(
        screen.getByText("Sua análise será exibida aqui")
      ).toBeInTheDocument();

      // Simula upload de arquivo
      const uploadButton = screen.getByLabelText("upload-file");
      await userEvent.click(uploadButton);

      // Aguarda o DragDrop detectar o arquivo
      await waitFor(() => {
        const dragDrop = screen.getByTestId("drag-drop");
        expect(dragDrop).toHaveTextContent("true");
      });

      // Clica no botão "Analisar com IA"
      const analisarButton = screen.getByRole("button", {
        name: /Analisar com IA/i,
      });

      await waitFor(() => {
        expect(analisarButton).not.toBeDisabled();
      });

      await userEvent.click(analisarButton);

      // Verifica que o toast de erro foi chamado com a mensagem correta
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "Dados fornecidos não puderam ser processados."
        );
      });

      // Verifica que o fetch foi chamado corretamente
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/analise-constitucionalidade/2",
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        })
      );

      // Verifica que a análise NÃO foi exibida
      expect(
        screen.queryByText("Análise de constitucionalidade")
      ).not.toBeInTheDocument();
    });

    it("deve mostrar toast de erro quando backend retornar erro 500", async () => {
      // Mock do fetch para simular erro interno do servidor
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          error: "Erro interno no servidor",
        }),
      }) as jest.Mock;

      render(<AnaliseConstitucionalidade />);

      // Upload de arquivo
      await userEvent.click(screen.getByLabelText("upload-file"));

      await waitFor(() => {
        expect(screen.getByTestId("drag-drop")).toHaveTextContent("true");
      });

      // Clica em analisar
      const analisarButton = screen.getByRole("button", {
        name: /Analisar com IA/i,
      });

      await waitFor(() => expect(analisarButton).not.toBeDisabled());
      await userEvent.click(analisarButton);

      // Verifica toast de erro
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith("Erro interno no servidor");
      });
    });

    it("deve mostrar toast de erro quando a internet do usuário cair", async () => {
      // Mock do fetch para simular erro de rede (sem internet)
      global.fetch = jest.fn().mockRejectedValueOnce(
        new TypeError("Failed to fetch")
      ) as jest.Mock;

      render(<AnaliseConstitucionalidade />);

      // Upload de arquivo
      await userEvent.click(screen.getByLabelText("upload-file"));

      await waitFor(() => {
        expect(screen.getByTestId("drag-drop")).toHaveTextContent("true");
      });

      // Clica em analisar
      const analisarButton = screen.getByRole("button", {
        name: /Analisar com IA/i,
      });

      await waitFor(() => expect(analisarButton).not.toBeDisabled());
      await userEvent.click(analisarButton);

      // Verifica toast de erro com mensagem de erro de rede
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "Erro de conexão. Verifique sua internet e tente novamente."
        );
      });

      // Verifica que o fetch foi chamado
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/analise-constitucionalidade/2",
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        })
      );
    });
  });

  describe("Cenário de sucesso", () => {
    it("deve mostrar a análise de constitucionalidade quando backend retornar sucesso", async () => {
      // Mock do fetch para simular sucesso do backend
      const mockAnaliseResponse = {
        parecer: "Favorável",
        gravidade: "Baixa",
        justificativa:
          "O projeto de lei está em conformidade com a Constituição Federal, respeitando os princípios fundamentais e não apresentando vícios de inconstitucionalidade.",
        artigos_destacados: ["Art. 5º", "Art. 37"],
        sugestao: "Aprovação sem ressalvas.",
      };

      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockAnaliseResponse,
      }) as jest.Mock;

      // Renderiza o componente
      render(<AnaliseConstitucionalidade />);

      // Simula upload de arquivo
      await userEvent.click(screen.getByLabelText("upload-file"));

      await waitFor(() => {
        expect(screen.getByTestId("drag-drop")).toHaveTextContent("true");
      });

      // Clica no botão "Analisar com IA"
      const analisarButton = screen.getByRole("button", {
        name: /Analisar com IA/i,
      });

      await waitFor(() => expect(analisarButton).not.toBeDisabled());
      await userEvent.click(analisarButton);

      await waitFor(() => {
        expect(
          screen.getByText("Análise de constitucionalidade")
        ).toBeInTheDocument();
      });

      // Verifica o parecer
      expect(screen.getByText(/Parecer:/i)).toBeInTheDocument();
      expect(screen.getByText("Favorável")).toBeInTheDocument();

      // Verifica a gravidade
      expect(screen.getByText(/Gravidade:/i)).toBeInTheDocument();
      expect(screen.getByText("Baixa")).toBeInTheDocument();

      // Verifica a justificativa
      expect(
        screen.getByText(/O projeto de lei está em conformidade/i)
      ).toBeInTheDocument();

      // Verifica que o toast de erro NÃO foi chamado
      expect(toast.error).not.toHaveBeenCalled();

      // Verifica que o fetch foi chamado corretamente
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/analise-constitucionalidade/2",
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        })
      );
    });

    it("deve mostrar loading durante o processamento da análise", async () => {
      // Mock com promessa pendente para manter loading
      global.fetch = jest.fn().mockImplementationOnce(
        () => new Promise(() => {}) // Promise que nunca resolve
      ) as jest.Mock;

      render(<AnaliseConstitucionalidade />);

      // Upload arquivo
      await userEvent.click(screen.getByLabelText("upload-file"));

      await waitFor(() => {
        expect(screen.getByTestId("drag-drop")).toHaveTextContent("true");
      });

      // Clica em analisar
      const analisarButton = screen.getByRole("button", {
        name: /Analisar com IA/i,
      });

      await waitFor(() => expect(analisarButton).not.toBeDisabled());
      await userEvent.click(analisarButton);

      // Verifica que o loading está presente
      await waitFor(() => {
        expect(screen.getByText("Carregando análise...")).toBeInTheDocument();
      });

      // Verifica que o botão está desabilitado durante loading
      expect(analisarButton).toBeDisabled();
    });

    it("deve exibir diferentes tipos de parecer corretamente", async () => {
      const mockAnaliseContraria = {
        parecer: "Contrário",
        gravidade: "Alta",
        justificativa: "O projeto viola a Constituição Federal.",
        artigos_destacados: ["Art. 1º"],
        sugestao: "Rejeitar o projeto.",
      };

      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockAnaliseContraria,
      }) as jest.Mock;

      render(<AnaliseConstitucionalidade />);

      // Upload e análise
      await userEvent.click(screen.getByLabelText("upload-file"));

      await waitFor(() => {
        expect(screen.getByTestId("drag-drop")).toHaveTextContent("true");
      });

      const analisarButton = screen.getByRole("button", {
        name: /Analisar com IA/i,
      });

      await waitFor(() => expect(analisarButton).not.toBeDisabled());
      await userEvent.click(analisarButton);

      // Verifica que o parecer contrário é exibido
      await waitFor(() => {
        expect(screen.getByText("Contrário")).toBeInTheDocument();
        expect(screen.getByText("Alta")).toBeInTheDocument();
        expect(
          screen.getByText(/O projeto viola a Constituição Federal/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("Validação de formulário", () => {
    it("botão deve estar desabilitado quando não há arquivo", () => {
      render(<AnaliseConstitucionalidade />);

      const analisarButton = screen.getByRole("button", {
        name: /Analisar com IA/i,
      });

      expect(analisarButton).toBeDisabled();
    });

    it("botão deve ser habilitado quando arquivo válido é carregado", async () => {
      render(<AnaliseConstitucionalidade />);

      // Upload arquivo
      await userEvent.click(screen.getByLabelText("upload-file"));

      await waitFor(() => {
        expect(screen.getByTestId("drag-drop")).toHaveTextContent("true");
      });

      // Verifica que botão foi habilitado
      const analisarButton = screen.getByRole("button", {
        name: /Analisar com IA/i,
      });

      await waitFor(() => {
        expect(analisarButton).not.toBeDisabled();
      });
    });
  }                                                        );
});
