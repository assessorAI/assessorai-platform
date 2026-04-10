import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConfigurarConta } from "./configurar-conta";
import { UserResponse } from "@/api/user/user.types";
import { PermissionLevel } from "@/types/user.types";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

// Mocks
jest.mock("./configurar-conta.module.scss", () => ({}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

jest.mock("next-auth/react", () => ({
  useSession: jest.fn(),
}));

describe("ConfigurarConta", () => {
  const mockRefresh = jest.fn();
  const mockUpdate = jest.fn();
  const mockRouter = {
    refresh: mockRefresh,
    push: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    prefetch: jest.fn(),
    replace: jest.fn(),
  };

  const mockUser: UserResponse = {
    id: "123",
    email: "joao@email.com",
    first_name: "João",
    last_name: "Silva",
    phone: "(11)99999-9999",
    role: "Assessor Legislativo",
    permission_level: PermissionLevel.Admin,
    lgpd_check: true,
    mandato: [],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSession as jest.Mock).mockReturnValue({
      data: { user: mockUser },
      status: "authenticated",
      update: mockUpdate,
    });
  });

  describe("Renderização básica", () => {
    it("deve renderizar o título do card", () => {
      // Arrange & Act
      render(<ConfigurarConta user={mockUser} />);

      // Assert
      expect(
        screen.getByText("Verifique ou altere seus dados")
      ).toBeInTheDocument();
    });

    it("deve renderizar todos os campos do formulário", () => {
      // Arrange & Act
      render(<ConfigurarConta user={mockUser} />);

      // Assert
      expect(screen.getByLabelText("Nome")).toBeInTheDocument();
      expect(screen.getByLabelText("Sobrenome")).toBeInTheDocument();
      expect(screen.getByLabelText("Cargo")).toBeInTheDocument();
      expect(screen.getByLabelText("Telefone")).toBeInTheDocument();
      expect(screen.getByLabelText("Email")).toBeInTheDocument();
    });

    it("deve renderizar o botão de salvar", () => {
      // Arrange & Act
      render(<ConfigurarConta user={mockUser} />);

      // Assert
      expect(
        screen.getByRole("button", { name: /salvar alterações/i })
      ).toBeInTheDocument();
    });
  });

  describe("Valores iniciais", () => {
    it("deve carregar os valores do usuário nos campos", () => {
      // Arrange & Act
      render(<ConfigurarConta user={mockUser} />);

      // Assert
      expect(screen.getByLabelText("Nome")).toHaveValue("João");
      expect(screen.getByLabelText("Sobrenome")).toHaveValue("Silva");
      expect(screen.getByLabelText("Email")).toHaveValue("joao@email.com");
      expect(screen.getByLabelText("Telefone")).toHaveValue("(11)99999-9999");
    });

    it("deve ter o campo de email desabilitado", () => {
      // Arrange & Act
      render(<ConfigurarConta user={mockUser} />);

      // Assert
      expect(screen.getByLabelText("Email")).toBeDisabled();
    });
  });

  describe("Campos editáveis", () => {
    it("deve permitir editar o nome", async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const nomeInput = screen.getByLabelText("Nome");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Maria");

      // Assert
      expect(nomeInput).toHaveValue("Maria");
    });

    it("deve permitir editar o sobrenome", async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const sobrenomeInput = screen.getByLabelText("Sobrenome");
      await user.clear(sobrenomeInput);
      await user.type(sobrenomeInput, "Santos");

      // Assert
      expect(sobrenomeInput).toHaveValue("Santos");
    });

    it("deve permitir editar o telefone", async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const telefoneInput = screen.getByLabelText("Telefone");
      await user.clear(telefoneInput);
      await user.type(telefoneInput, "(21)98888-8888");

      // Assert
      expect(telefoneInput).toHaveValue("(21)98888-8888");
    });
  });

  describe("Select de cargo", () => {
    it("deve mostrar o cargo selecionado do usuário", () => {
      // Arrange & Act
      render(<ConfigurarConta user={mockUser} />);

      // Assert
      const cargoElements = screen.getAllByText("Assessor Legislativo");
      expect(cargoElements.length).toBeGreaterThan(0);
    });

    it("deve ter as opções de cargo disponíveis no select oculto", () => {
      // Arrange & Act
      render(<ConfigurarConta user={mockUser} />);

      // Assert
      const hiddenSelect = document.querySelector('select[aria-hidden="true"]');
      expect(hiddenSelect).toBeInTheDocument();

      const options = hiddenSelect?.querySelectorAll("option");
      const optionTexts = Array.from(options || []).map(
        (opt) => opt.textContent
      );

      // Verifica se contém alguns dos cargos esperados
      expect(optionTexts.length).toBeGreaterThan(0);
    });
  });

  describe("Submit do formulário", () => {
    it("deve atualizar os dados do usuário com sucesso", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockUser,
          first_name: "Maria",
        }),
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const nomeInput = screen.getByLabelText("Nome");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Maria");

      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "/api/user/123",
          expect.objectContaining({
            method: "PUT",
            body: expect.any(String),
          })
        );
      });
    });

    it("deve exibir toast de sucesso após atualização", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockUser,
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "Dados da conta atualizados com sucesso"
        );
      });
    });

    it("deve chamar router.refresh após atualização bem-sucedida", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockUser,
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(mockRefresh).toHaveBeenCalled();
      });
    });

    it("deve atualizar a sessão após atualização bem-sucedida", async () => {
      // Arrange
      const user = userEvent.setup();
      const updatedUser = { ...mockUser, first_name: "Maria" };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => updatedUser,
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(mockUpdate).toHaveBeenCalledWith({
          user: expect.objectContaining({
            first_name: "Maria",
          }),
        });
      });
    });

    it("deve exibir toast de erro quando a atualização falhar", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "Erro interno do servidor. Tente novamente mais tarde."
        );
      });
    });

    it("não deve chamar router.refresh quando houver erro", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
      expect(mockRefresh).not.toHaveBeenCalled();
    });

    it("não deve atualizar a sessão quando houver erro", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
      expect(mockUpdate).not.toHaveBeenCalled();
    });

    it("deve exibir toast de erro quando houver exceção", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockRejectedValue(
        new TypeError("Failed to fetch")
      );
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "Erro de conexão. Verifique sua internet e tente novamente."
        );
      });
    });
  });

  describe("Loading state", () => {
    it("deve desabilitar o botão durante o submit", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      expect(submitButton).toBeDisabled();
    });

    it("deve reabilitar o botão após o submit com sucesso", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockUser,
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });

    it("deve reabilitar o botão após o submit com erro", async () => {
      // Arrange
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
      });
      render(<ConfigurarConta user={mockUser} />);

      // Act
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe("Validação do formulário", () => {
    it("deve ter o botão desabilitado quando o formulário não for válido", () => {
      // Arrange
      const invalidUser = {
        ...mockUser,
        first_name: "",
      };

      // Act
      render(<ConfigurarConta user={invalidUser} />);

      // Assert
      const submitButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      expect(submitButton).toBeDisabled();
    });
  });
});

