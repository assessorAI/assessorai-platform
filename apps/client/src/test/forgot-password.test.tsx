import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ForgotPasswordForm } from "@/features/auth/forgot-password/forgot-password";
import { toast } from "sonner";

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("ForgotPasswordForm - Funcionalidade Principal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve renderizar o componente com o formulário", () => {
    render(<ForgotPasswordForm />);

    expect(screen.getByText("Esqueci minha senha")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Enviar email de recuperação/i })).toBeInTheDocument();
  });

  test("deve desabilitar o botão quando o email está vazio", () => {
    render(<ForgotPasswordForm />);

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });

    expect(submitBtn).toBeDisabled();
  });

  test("deve habilitar o botão quando o usuário preenche um email válido", async () => {
    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email");
    await userEvent.type(emailInput, "teste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });

    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });

  test("deve exibir toast de sucesso quando o email é enviado", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email");
    await userEvent.type(emailInput, "teste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        "Email de recuperação enviado com sucesso",
        { description: "Verifique sua caixa de entrada para redefinir sua senha" }
      );
    });
  });

  test("deve limpar o campo após envio bem-sucedido", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    await userEvent.type(emailInput, "teste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(emailInput.value).toBe("");
    });
  });
});

describe("ForgotPasswordForm - Tratamento de Erros", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve exibir toast de erro quando a API retornar erro 400", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({}),
    });

    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email");
    await userEvent.type(emailInput, "teste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
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

    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email");
    await userEvent.type(emailInput, "naoexiste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Recurso não encontrado."
      );
    });
  });

  test("deve exibir toast de erro quando a API retornar erro 500", async () => {
    

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email");
    await userEvent.type(emailInput, "teste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
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

    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email");
    await userEvent.type(emailInput, "teste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
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

    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email");
    await userEvent.type(emailInput, "teste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Erro interno do servidor. Tente novamente mais tarde."
      );
    });
  });

  test("deve permitir nova tentativa após erro", async () => {
    

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText("Email");
    await userEvent.type(emailInput, "teste@example.com");

    const submitBtn = screen.getByRole("button", { name: /Enviar email de recuperação/i });
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await userEvent.clear(emailInput);
    await userEvent.type(emailInput, "novo@example.com");
    await waitFor(() => expect(submitBtn).not.toBeDisabled());
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalled();
    });
  });
});

