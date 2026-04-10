import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { toast } from "sonner";
import { GerarEmenda } from "@/features/gerar-emenda/gerar-emenda";
import { Emenda } from "@/api/emenda/emenda.types";


jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("@/hooks/useMandato", () => ({
  useMandato: jest.fn(() => ({ id: 1 })),
}));

const mockSugestaoEmenda: Emenda = {
  art: 5,
  tipo: "aditiva",
  texto: "Texto da emenda de teste",
};

const mockFile = new File(["conteúdo do arquivo"], "projeto-lei.pdf", {
  type: "application/pdf",
});

const mockEmendaResponse = {
  full_markdown: "# Emenda Gerada\n\nConteúdo da emenda processada",
};

describe("GerarEmenda - Funcionalidade Principal", () => {
  const mockOnEmendaGerada = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve renderizar o componente com título", () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmendaResponse,
    });

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    expect(screen.getByText("Emenda Processada")).toBeInTheDocument();
  });

  test("deve exibir a emenda gerada quando a API retornar sucesso", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmendaResponse,
    });

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Emenda Gerada/i)).toBeInTheDocument();
    });

    expect(mockOnEmendaGerada).toHaveBeenCalledTimes(1);
  });

  test("deve chamar a API com os dados corretos", async () => {
    const mockFetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmendaResponse,
    });
    global.fetch = mockFetch;

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/emenda/1",
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        })
      );
    });
  });


  test("deve chamar onEmendaGerada após sucesso", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEmendaResponse,
    });

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(mockOnEmendaGerada).toHaveBeenCalledTimes(1);
    });
  });
});

describe("GerarEmenda - Tratamento de Erros", () => {
  const mockOnEmendaGerada = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve exibir toast de erro quando a API retornar erro 400", async () => {

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({}),
    });

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Dados inválidos. Verifique as informações e tente novamente."
      );
    });

    expect(mockOnEmendaGerada).not.toHaveBeenCalled();
  });

  test("deve exibir toast de erro quando a API retornar erro 404", async () => {

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({}),
    });

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Recurso não encontrado.");
    });

    expect(mockOnEmendaGerada).not.toHaveBeenCalled();
  });

  test("deve exibir toast de erro quando a API retornar erro 422", async () => {

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({}),
    });

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Dados fornecidos não puderam ser processados."
      );
    });

    expect(mockOnEmendaGerada).not.toHaveBeenCalled();
  });

  test("deve exibir toast de erro quando a API retornar erro 500", async () => {

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });

    expect(mockOnEmendaGerada).not.toHaveBeenCalled();
  });

  test("deve exibir toast de erro quando houver erro de conexão (TypeError)", async () => {

    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new TypeError("Failed to fetch")
    );

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro de conexão. Verifique sua internet e tente novamente."
      );
    });

    expect(mockOnEmendaGerada).not.toHaveBeenCalled();
  });

  test("deve exibir toast de erro genérico quando houver exceção inesperada", async () => {

    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Unexpected error")
    );

    render(
      <GerarEmenda
        sugestaoEmenda={mockSugestaoEmenda}
        file={mockFile}
        onEmendaGerada={mockOnEmendaGerada}
      />
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });

    expect(mockOnEmendaGerada).not.toHaveBeenCalled();
  });

});

