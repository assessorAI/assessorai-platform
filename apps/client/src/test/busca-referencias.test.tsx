import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BuscaReferencias } from "@/features/busca-referencias/busca-referencias";
import { ProjetosReferenciaProvider } from "@/context/projetos-referencias.context";
import { toast } from "sonner";

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("@/hooks/useMandato", () => ({
  useMandato: jest.fn(() => ({
    id: 1,
    nome_parlamentar: "Vereador Teste",
    casa_legislativa: "Câmara Municipal",
  })),
}));

const PLACEHOLDER_TEXT = "Escreva aqui uma palavra chave ou o tema da proposição legislativa";
const BUTTON_TEXT = "Buscar proposições";

describe("BuscaReferencias - Funcionalidade Principal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve renderizar o componente com o formulário de busca", () => {
    render(
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    expect(screen.getByPlaceholderText(PLACEHOLDER_TEXT)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') })).toBeInTheDocument();
  });

  test("deve desabilitar o botão quando o campo está vazio", () => {
    render(
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    const submitBtn = screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') });
    expect(submitBtn).toBeDisabled();
  });

  test("deve habilitar o botão quando o usuário digita algo", async () => {
    render(
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    const searchInput = screen.getByPlaceholderText(PLACEHOLDER_TEXT);
    await userEvent.type(searchInput, "meio ambiente");

    const submitBtn = screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') });
    expect(submitBtn).not.toBeDisabled();
  });
});

describe("BuscaReferencias - Tratamento de Erros", () => {
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
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    const searchInput = screen.getByPlaceholderText(PLACEHOLDER_TEXT);
    await userEvent.type(searchInput, "teste");

    const submitBtn = screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Dados inválidos. Verifique as informações e tente novamente."
      );
    });
  });

  test("deve exibir toast de erro quando a API retornar erro 404", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({}),
    });

    render(
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    const searchInput = screen.getByPlaceholderText(PLACEHOLDER_TEXT);
    await userEvent.type(searchInput, "teste");

    const submitBtn = screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Recurso não encontrado.");
    });
  });

  test("deve exibir toast de erro quando a API retornar erro 422", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({}),
    });

    render(
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    const searchInput = screen.getByPlaceholderText(PLACEHOLDER_TEXT);
    await userEvent.type(searchInput, "teste");

    const submitBtn = screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Dados fornecidos não puderam ser processados."
      );
    });
  });

  test("deve exibir toast de erro quando a API retornar erro 500", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    render(
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    const searchInput = screen.getByPlaceholderText(PLACEHOLDER_TEXT);
    await userEvent.type(searchInput, "teste");

    const submitBtn = screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });
  });

  test("deve exibir toast de erro quando houver erro de conexão (TypeError)", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new TypeError("Failed to fetch")
    );

    render(
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    const searchInput = screen.getByPlaceholderText(PLACEHOLDER_TEXT);
    await userEvent.type(searchInput, "teste");

    const submitBtn = screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro de conexão. Verifique sua internet e tente novamente."
      );
    });
  });

  test("deve exibir toast de erro genérico quando houver exceção inesperada", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Unexpected error")
    );

    render(
      <ProjetosReferenciaProvider>
        <BuscaReferencias />
      </ProjetosReferenciaProvider>
    );

    const searchInput = screen.getByPlaceholderText(PLACEHOLDER_TEXT);
    await userEvent.type(searchInput, "teste");

    const submitBtn = screen.getByRole("button", { name: new RegExp(BUTTON_TEXT, 'i') });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });
  });
});

