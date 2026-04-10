import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MinhaEquipeForm } from "./minha-equipe-form";
import { UserResponse } from "@/api/user/user.types";
import { PermissionLevel } from "@/types/user.types";
import { toast } from "sonner";
import { useSession } from "next-auth/react";

// Mock do módulo de estilos SCSS
jest.mock("./minha-equipe-form.module.scss", () => ({}));

// Mock do next-auth para simular a sessão do usuário
jest.mock("next-auth/react", () => ({
  useSession: jest.fn(() => ({
    data: {
      user: {
        permission_level: PermissionLevel.Manager,
      },
    },
    status: "authenticated",
  })),
}));

// Mock do next/navigation para simular useParams e useRouter
jest.mock("next/navigation", () => ({
  useParams: jest.fn(() => ({ id: "mandato-123" })),
  useRouter: jest.fn(() => ({
    refresh: jest.fn(),
    push: jest.fn(),
  })),
}));

// Mock do sonner (biblioteca de toast)
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock do fetch global
global.fetch = jest.fn();

describe("MinhaEquipeForm", () => {
  // Limpa os mocks antes de cada teste
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Função helper para criar usuários de teste
  const createMockUser = (
    email: string,
    permissionLevel: PermissionLevel
  ): UserResponse => ({
    email,
    first_name: "João",
    last_name: "Silva",
    phone: "(11)98765-4321",
    permission_level: permissionLevel,
    lgpd_check: true,
    role: "Assessor",
    id: `user-${email}`,
    mandato: [],
  });

  describe("Limite de membros", () => {
    it("não deve permitir adicionar novo membro se já tiver 3 membros (excluindo Manager)", () => {
      // Arrange: Cria 3 usuários não-managers + 1 manager
      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
        createMockUser("user2@example.com", PermissionLevel.User),
        createMockUser("user3@example.com", PermissionLevel.User),
        createMockUser("manager@example.com", PermissionLevel.Manager),
      ];

      // Act: Renderiza o componente com 3 membros
      render(<MinhaEquipeForm users={users} />);

      // Assert: Verifica que o botão está desabilitado
      const submitButton = screen.getByRole("button", {
        name: /enviar convite/i,
      });
      expect(submitButton).toBeDisabled();
    });

    it("deve permitir adicionar novo membro se houver menos de 3 membros", () => {
      // Arrange: Cria apenas 2 usuários não-managers
      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
        createMockUser("user2@example.com", PermissionLevel.User),
        createMockUser("manager@example.com", PermissionLevel.Manager),
      ];

      // Act: Renderiza o componente com 2 membros
      render(<MinhaEquipeForm users={users} />);

      // Assert: Verifica que o botão NÃO está desabilitado
      const submitButton = screen.getByRole("button", {
        name: /enviar convite/i,
      });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe("Envio de convite", () => {
    it("deve adicionar novo membro com sucesso quando a quantidade for menor que 3", async () => {
      // Arrange: Cria apenas 1 usuário não-manager
      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
      ];

      // Mock do fetch para simular resposta de sucesso
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      // Pega a referência do mock do router
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const { useRouter } = require("next/navigation");
      const mockRefresh = jest.fn();
      useRouter.mockReturnValue({
        refresh: mockRefresh,
        push: jest.fn(),
      });

      // Act: Renderiza o componente
      render(<MinhaEquipeForm users={users} />);

      // Preenche o campo de email
      const emailInput = screen.getByPlaceholderText(
        /insira o e-mail do convidado/i
      );
      await userEvent.type(emailInput, "novomembro@example.com");

      // Clica no botão de enviar
      const submitButton = screen.getByRole("button", {
        name: /enviar convite/i,
      });
      await userEvent.click(submitButton);

      // Assert: Verifica que o fetch foi chamado corretamente
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "/api/mandato/mandato-123/users",
          {
            method: "POST",
            body: JSON.stringify({ email: "novomembro@example.com" }),
          }
        );
      });

      // Verifica que o toast de sucesso foi exibido
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "Convite enviado com sucesso"
        );
      });

      // Verifica que o router.refresh foi chamado para atualizar a página
      await waitFor(() => {
        expect(mockRefresh).toHaveBeenCalled();
      });
    });

    it("deve exibir erro quando o envio do convite falhar", async () => {
      // Arrange: Cria apenas 1 usuário não-manager
      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
      ];

      // Mock do fetch para simular resposta de erro
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
      });

      // Act: Renderiza o componente
      render(<MinhaEquipeForm users={users} />);

      // Preenche o campo de email
      const emailInput = screen.getByPlaceholderText(
        /insira o e-mail do convidado/i
      );
      await userEvent.type(emailInput, "novomembro@example.com");

      // Clica no botão de enviar
      const submitButton = screen.getByRole("button", {
        name: /enviar convite/i,
      });
      await userEvent.click(submitButton);

      // Assert: Verifica que o toast de erro foi exibido
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith("Dados inválidos. Verifique as informações e tente novamente.");
      });
    });
  });

  describe("Estado de loading", () => {
    it("deve mostrar loading ao clicar em enviar convite e parar quando terminar", async () => {
      // Arrange: Cria apenas 1 usuário não-manager
      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
      ];

      // Mock do fetch com delay para simular requisição
      (global.fetch as jest.Mock).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({ success: true }),
                }),
              100
            )
          )
      );

      // Act: Renderiza o componente
      render(<MinhaEquipeForm users={users} />);

      // Preenche o campo de email
      const emailInput = screen.getByPlaceholderText(
        /insira o e-mail do convidado/i
      );
      await userEvent.type(emailInput, "novomembro@example.com");

      // Pega o botão de enviar
      const submitButton = screen.getByRole("button", {
        name: /enviar convite/i,
      });

      // Verifica que inicialmente o botão NÃO está desabilitado
      expect(submitButton).not.toBeDisabled();

      // Clica no botão de enviar
      await userEvent.click(submitButton);

      // Assert: Verifica que o botão fica desabilitado durante o loading
      expect(submitButton).toBeDisabled();

      // Aguarda a requisição terminar
      await waitFor(
        () => {
          expect(toast.success).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      // Verifica que o botão volta a ficar habilitado após o loading
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });

    it("deve parar o loading mesmo quando houver erro no envio", async () => {
      // Arrange: Cria apenas 1 usuário não-manager
      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
      ];

      // Mock do fetch com delay e erro
      (global.fetch as jest.Mock).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: false,
                  status: 500,
                }),
              100
            )
          )
      );

      // Act: Renderiza o componente
      render(<MinhaEquipeForm users={users} />);

      // Preenche o campo de email
      const emailInput = screen.getByPlaceholderText(
        /insira o e-mail do convidado/i
      );
      await userEvent.type(emailInput, "novomembro@example.com");

      // Pega o botão de enviar
      const submitButton = screen.getByRole("button", {
        name: /enviar convite/i,
      });

      // Clica no botão de enviar
      await userEvent.click(submitButton);

      // Assert: Verifica que o botão fica desabilitado durante o loading
      expect(submitButton).toBeDisabled();

      // Aguarda o erro
      await waitFor(
        () => {
          expect(toast.error).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      // Verifica que o botão volta a ficar habilitado após o erro
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe("Permissões", () => {
    it("não deve renderizar o formulário se o usuário não tiver permissão para adicionar membros", () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { useSession } = require("next-auth/react");
      useSession.mockImplementation(() => ({
        data: {
          user: {
            permission_level: PermissionLevel.Viewer, // Viewer não pode adicionar membros
          },
        },
        status: "authenticated",
      }));

      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
      ];

      // Act: Renderiza o componente
      const { container } = render(<MinhaEquipeForm users={users} />);

      // Assert: Verifica que nada foi renderizado
      expect(container.firstChild).toBeNull();
    });
  });

  describe("Limite de membros por tipo de usuário", () => {
    const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

    beforeEach(() => {
      jest.clearAllMocks();
    });

    it("deve poder adicionar no máximo 3 membros da equipe quando o usuário é do tipo Manager", () => {
      // Arrange: Configura sessão com usuário Manager
      mockUseSession.mockReturnValue({
        data: {
          user: {
            permission_level: PermissionLevel.Manager,
          },
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } as any,
        status: "authenticated",
        update: jest.fn(),
      });

      // Cria exatamente 3 usuários não-managers (atingindo o limite)
      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
        createMockUser("user2@example.com", PermissionLevel.User),
        createMockUser("user3@example.com", PermissionLevel.User),
        createMockUser("manager@example.com", PermissionLevel.Manager),
      ];

      // Act: Renderiza o componente
      render(<MinhaEquipeForm users={users} />);

      // Assert: Verifica que o botão de enviar convite está desabilitado
      const submitButton = screen.getByRole("button", {
        name: /enviar convite/i,
      });
      expect(submitButton).toBeDisabled();

      // Verifica que o input de email também está desabilitado
      const emailInput = screen.getByPlaceholderText(
        /insira o e-mail do convidado/i
      );
      expect(emailInput).toBeDisabled();
    });

    it("deve poder adicionar mais de 3 membros da equipe quando o usuário é do tipo Admin", () => {
      // Arrange: Configura sessão com usuário Admin
      mockUseSession.mockReturnValue({
        data: {
          user: {
            permission_level: PermissionLevel.Admin,
          },
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } as any,
        status: "authenticated",
        update: jest.fn(),
      });

      // Cria 4 usuários não-managers (mais do que o limite para Manager)
      const users: UserResponse[] = [
        createMockUser("user1@example.com", PermissionLevel.User),
        createMockUser("user2@example.com", PermissionLevel.User),
        createMockUser("user3@example.com", PermissionLevel.User),
        createMockUser("user4@example.com", PermissionLevel.User),
        createMockUser("admin@example.com", PermissionLevel.Admin),
      ];

      // Act: Renderiza o componente
      render(<MinhaEquipeForm users={users} />);

      // Assert: Verifica que o botão de enviar convite NÃO está desabilitado
      // (Admin pode adicionar mais de 3 membros)
      const submitButton = screen.getByRole("button", {
        name: /enviar convite/i,
      });
      expect(submitButton).not.toBeDisabled();

      // Verifica que o input de email também NÃO está desabilitado
      const emailInput = screen.getByPlaceholderText(
        /insira o e-mail do convidado/i
      );
      expect(emailInput).not.toBeDisabled();
    });
  });
});