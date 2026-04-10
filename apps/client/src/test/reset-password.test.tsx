import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ResetPassword } from "@/features/auth/reset-password/reset-password";
import { useSearchParams } from "next/navigation";

jest.mock("next/navigation", () => ({
  useSearchParams: jest.fn(),
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    refresh: jest.fn(),
  })),
}));

const mockSearchParams = useSearchParams as jest.Mock;

describe("ResetPassword - Funcionalidade Principal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams.mockReturnValue({
      get: jest.fn((key) => (key === "token" ? "valid-token-123" : null)),
    });
  });

  test("deve renderizar o componente com o formulário", () => {
    render(<ResetPassword />);

    expect(screen.getByText("Recuperação de senha")).toBeInTheDocument();
    expect(screen.getAllByLabelText("Senha")[0]).toBeInTheDocument();
    expect(screen.getByLabelText("Confirmar senha")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Continuar/i })).toBeInTheDocument();
  });

  test("deve exibir regras de senha", () => {
    render(<ResetPassword />);

    expect(screen.getByText(/Mínimo de 8 caracteres/i)).toBeInTheDocument();
    expect(screen.getByText(/Pelo menos um número/i)).toBeInTheDocument();
    expect(screen.getByText(/Pelo menos uma letra/i)).toBeInTheDocument();
    expect(screen.getByText(/Pelo menos um caractere especial/i)).toBeInTheDocument();
  });

  test("deve validar senha que não atende requisitos mínimos", async () => {
    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "fraca");
    await userEvent.type(confirmPasswordInput, "fraca");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("A senha escolhida não cumpre todos os requisitos.")).toBeInTheDocument();
    });
  });

  test("deve validar quando senhas não coincidem", async () => {
    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaDiferente123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("As senhas digitadas não são iguais.")).toBeInTheDocument();
    });
  });

  test("deve exibir tela de sucesso quando a senha é resetada", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Senha alterada com sucesso")).toBeInTheDocument();
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

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    expect(submitBtn).toBeDisabled();
    expect(screen.getByRole("status")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Senha alterada com sucesso")).toBeInTheDocument();
    });
  });
});

describe("ResetPassword - Tratamento de Erros", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams.mockReturnValue({
      get: jest.fn((key) => (key === "token" ? "valid-token-123" : null)),
    });
  });

  test("deve exibir erro quando token não está presente", async () => {
    mockSearchParams.mockReturnValue({
      get: jest.fn(() => null),
    });

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Não foi possível redefinir a senha, o seu token de recuperação expirou ou é inválido")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando a API retornar erro 400", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({}),
    });

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Não foi possível redefinir a senha, o seu token de recuperação expirou ou é inválido")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando a API retornar erro 404", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({}),
    });

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Não foi possível redefinir a senha, o seu token de recuperação expirou ou é inválido")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando a API retornar erro 500", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Não foi possível redefinir a senha, o seu token de recuperação expirou ou é inválido")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando houver erro de conexão (TypeError)", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new TypeError("Failed to fetch")
    );

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Não foi possível redefinir a senha, o seu token de recuperação expirou ou é inválido")).toBeInTheDocument();
    });
  });

  test("deve exibir erro quando houver exceção inesperada", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Unexpected error")
    );

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Não foi possível redefinir a senha, o seu token de recuperação expirou ou é inválido")).toBeInTheDocument();
    });
  });

  test("deve permitir nova tentativa após erro", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    render(<ResetPassword />);

    const passwordInput = screen.getAllByLabelText("Senha")[0];
    const confirmPasswordInput = screen.getByLabelText("Confirmar senha");
    
    await userEvent.type(passwordInput, "SenhaForte123!");
    await userEvent.type(confirmPasswordInput, "SenhaForte123!");

    const submitBtn = screen.getByRole("button", { name: /Continuar/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Não foi possível redefinir a senha, o seu token de recuperação expirou ou é inválido")).toBeInTheDocument();
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
      expect(screen.getByText("Senha alterada com sucesso")).toBeInTheDocument();
    });
  });
});

