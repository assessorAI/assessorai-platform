import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CrieSenha } from "@/features/auth/register-member/steps/crie-senha";
import { useSearchParams } from "next/navigation";

global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  useSearchParams: jest.fn(),
  useRouter: jest.fn(),
}));

const mockSearchParams = useSearchParams as jest.Mock;
const mockUseRouter = jest.fn();

jest.mock("next/navigation", () => ({
  useSearchParams: jest.fn(),
  useRouter: () => mockUseRouter,
}));

const mockContextValue = {
  currentStep: 2,
  nextStep: jest.fn(),
  prevStep: jest.fn(),
  updateData: jest.fn(),
  formData: {
    first_name: "João",
    last_name: "Silva",
    email: "joao@email.com",
  },
};

jest.mock("@/features/auth/register-member/register-member-step.context", () => ({
  useStep: () => mockContextValue,
}));

describe("RegisterMember - Funcionalidade Principal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams.mockReturnValue({
      get: jest.fn((key) => (key === "token" ? "valid-token-123" : null)),
    });
  });

  test("deve renderizar o componente com o formulário", () => {
    render(<CrieSenha />);

    expect(screen.getByText("Crie sua senha")).toBeInTheDocument();
    expect(screen.getAllByLabelText("Senha")[0]).toBeInTheDocument();
    expect(screen.getByLabelText("Confirmar senha")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Finalizar cadastro/i })).toBeInTheDocument();
  });

  test("deve exibir regras de senha", () => {
    render(<CrieSenha />);

    expect(screen.getByText(/Mínimo de 8 caracteres/i)).toBeInTheDocument();
    expect(screen.getByText(/Pelo menos um número/i)).toBeInTheDocument();
    expect(screen.getByText(/Pelo menos uma letra/i)).toBeInTheDocument();
    expect(screen.getByText(/Pelo menos um caractere especial/i)).toBeInTheDocument();
  });

  test("deve validar checkbox LGPD obrigatório", async () => {
    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });

    expect(submitBtn).toBeDisabled();
  });

  test("deve chamar nextStep após registro bem-sucedido", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockContextValue.nextStep).toHaveBeenCalled();
    });
  });

  test("deve exibir loading durante o envio", async () => {
    (global.fetch as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: async () => ({}),
            });
          }, 100);
        })
    );

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    expect(submitBtn).toBeDisabled();
    expect(screen.getByRole("status")).toBeInTheDocument();

    await waitFor(() => {
      expect(mockContextValue.nextStep).toHaveBeenCalled();
    });
  });
});

describe("RegisterMember - Tratamento de Erros", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams.mockReturnValue({
      get: jest.fn((key) => (key === "token" ? "valid-token-123" : null)),
    });
  });

  test("deve exibir erro quando a API retornar erro 400", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: "Bad Request",
    });

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Erro ao registrar usuário")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando a API retornar erro 404", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
    });

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Erro ao registrar usuário")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando a API retornar erro 500", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Erro ao registrar usuário")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando houver erro de conexão (TypeError)", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new TypeError("Failed to fetch")
    );

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Erro ao registrar usuário")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando houver exceção inesperada", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Unexpected error")
    );

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Erro ao registrar usuário")).toBeInTheDocument();
    });
  });

  test("deve permitir nova tentativa após erro", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Erro ao registrar usuário")).toBeInTheDocument();
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await userEvent.clear(passwordInput);
    await userEvent.clear(confirmPasswordInput);
    await userEvent.type(passwordInput, "NovaSenha123!");
    await userEvent.type(confirmPasswordInput, "NovaSenha123!");
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockContextValue.nextStep).toHaveBeenCalled();
    });
  });

  test("não deve chamar nextStep quando houver erro", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    render(<CrieSenha />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);

    const submitBtn = screen.getByRole("button", { name: /Finalizar cadastro/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Erro ao registrar usuário")).toBeInTheDocument();
    });

    expect(mockContextValue.nextStep).not.toHaveBeenCalled();
  });
});

