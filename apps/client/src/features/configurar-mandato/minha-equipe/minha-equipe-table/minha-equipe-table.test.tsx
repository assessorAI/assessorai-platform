import React from "react";
import { render, screen } from "@testing-library/react";
import { MinhaEquipeTable } from "./minha-equipe-table";
import { UserResponse } from "@/api/user/user.types";
import { PermissionLevel } from "@/types/user.types";
import { UserStatus } from "@/types/user-status.type";
import { useSession } from "next-auth/react";

// Mock do módulo de estilos SCSS
jest.mock("./minha-equipe-table.module.scss", () => ({}));

// Mock do next/navigation
jest.mock("next/navigation", () => ({
  useParams: jest.fn(() => ({ id: "mandato-123" })),
  useRouter: jest.fn(() => ({
    refresh: jest.fn(),
    push: jest.fn(),
  })),
}));

// Mock do next-auth/react
jest.mock("next-auth/react", () => ({
  useSession: jest.fn(() => ({
    data: {
      user: {
        id: "999",
        permission_level: PermissionLevel.Manager,
      },
    },
    status: "authenticated",
  })),
}));

// Mock do react-transition-progress/next
jest.mock("react-transition-progress/next", () => ({
  Link: ({ children, href, target, className }: {
    children: React.ReactNode;
    href: string;
    target?: string;
    className?: string;
  }) => (
    <a href={href} target={target} className={className}>
      {children}
    </a>
  ),
}));

// Mock do sonner (toast)
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock do RemoveMember (para simplificar os testes)
jest.mock("./remove-member", () => ({
  RemoveMember: ({ email }: { email: string }) => (
    <td data-testid="remove-member">
      <button>Remover {email}</button>
    </td>
  ),
}));

describe("MinhaEquipeTable", () => {
  // Mock do useSession
  const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

  // Função helper para configurar a sessão do usuário
  const setupSession = (userId: string, permissionLevel: PermissionLevel) => {
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: userId,
          permission_level: permissionLevel,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });
  };

  // Configuração padrão antes de cada teste
  beforeEach(() => {
    setupSession("999", PermissionLevel.Manager);
  });

  // Função helper para criar usuários de teste
  const createMockUser = (
    id: string,
    firstName: string,
    lastName: string,
    email: string,
    permissionLevel: PermissionLevel
  ): UserResponse => ({
    id,
    first_name: firstName,
    last_name: lastName,
    email,
    phone: "(11)98765-4321",
    permission_level: permissionLevel,
    lgpd_check: true,
    role: "Assessor",
    mandato: [],
  });

  describe("Renderização básica", () => {
    it("deve renderizar a tabela com os usuários (excluindo Manager)", () => {
      // Arrange: Configura sessão com ID "3" (será o Manager)
      setupSession("3", PermissionLevel.Manager);
      
      // Cria 2 usuários comuns e 1 Manager
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
        createMockUser("3", "Admin", "Principal", "admin@example.com", PermissionLevel.Manager),
      ];

      // Act: Renderiza o componente
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que apenas os 2 usuários comuns são exibidos
      expect(screen.getByText("João Silva")).toBeInTheDocument();
      expect(screen.getByText("maria@example.com")).toBeInTheDocument();
      
      // Verifica que o Manager não aparece (é filtrado pelo ID da sessão)
      expect(screen.queryByText("Admin Principal")).not.toBeInTheDocument();
      expect(screen.queryByText("admin@example.com")).not.toBeInTheDocument();
    });

    it("deve renderizar os cabeçalhos da tabela corretamente", () => {
      // Arrange
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica os cabeçalhos da tabela
      expect(screen.getByText("Nome")).toBeInTheDocument();
      expect(screen.getByText("Email")).toBeInTheDocument();
      expect(screen.getByText("Status")).toBeInTheDocument();
    });
  });

  describe("Filtro de usuários", () => {
    it("não deve renderizar nada quando não há membros (excluindo Manager)", () => {
      // Arrange: Configura sessão com ID "1" (será o Manager)
      setupSession("1", PermissionLevel.Manager);
      
      // Apenas um Manager que é o próprio usuário logado
      const users: UserResponse[] = [
        createMockUser("1", "Admin", "Principal", "admin@example.com", PermissionLevel.Manager),
      ];

      // Act
      const { container } = render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que nada foi renderizado (o Manager é filtrado)
      expect(container.firstChild).toBeNull();
    });

    it("não deve renderizar nada quando o array de usuários está vazio", () => {
      // Arrange
      const users: UserResponse[] = [];

      // Act
      const { container } = render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(container.firstChild).toBeNull();
    });
  });

  describe("Limite de membros", () => {
    it("deve mostrar mensagem de limite quando houver exatamente 3 membros", () => {
      // Arrange: Cria 3 usuários não-managers
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
        createMockUser("3", "Pedro", "Costa", "pedro@example.com", PermissionLevel.User),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que a mensagem de limite aparece
      expect(
        screen.getByText(/você atingiu o limite de três convites/i)
      ).toBeInTheDocument();
    });

    it("deve mostrar mensagem de limite quando houver mais de 3 membros", () => {
      // Arrange: Cria 4 usuários não-managers
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
        createMockUser("3", "Pedro", "Costa", "pedro@example.com", PermissionLevel.User),
        createMockUser("4", "Ana", "Lima", "ana@example.com", PermissionLevel.User),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(
        screen.getByText(/você atingiu o limite de três convites/i)
      ).toBeInTheDocument();
    });

    it("não deve mostrar mensagem de limite quando houver menos de 3 membros", () => {
      // Arrange: Cria apenas 2 usuários
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que a mensagem NÃO aparece
      expect(
        screen.queryByText(/você atingiu o limite de três convites/i)
      ).not.toBeInTheDocument();
    });
  });

  describe("Status dos usuários", () => {
    it("deve exibir status 'Membro ativo' para usuário com permissão User", () => {
      // Arrange
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText(UserStatus.ACTIVE)).toBeInTheDocument();
    });

    it("deve exibir status 'Membro ativo' para usuário com permissão Admin", () => {
      // Arrange
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.Admin),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText(UserStatus.ACTIVE)).toBeInTheDocument();
    });

    it("deve exibir status 'Convite enviado' para usuário com permissão Invited", () => {
      // Arrange
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.Invited),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText(UserStatus.INVITED)).toBeInTheDocument();
    });

    it("deve exibir status 'Membro ativo' para usuário com permissão Viewer", () => {
      // Arrange
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.Viewer),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText(UserStatus.ACTIVE)).toBeInTheDocument();
    });
  });

  describe("Nome dos usuários", () => {
    it("deve exibir nome completo do usuário quando first_name e last_name estão preenchidos", () => {
      // Arrange
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText("João Silva")).toBeInTheDocument();
    });

    it("deve exibir 'Nome não informado' quando first_name está vazio", () => {
      // Arrange
      const users: UserResponse[] = [
        {
          id: "1",
          first_name: "",
          last_name: "Silva",
          email: "joao@example.com",
          phone: "(11)98765-4321",
          permission_level: PermissionLevel.User,
          lgpd_check: true,
          role: "Assessor",
          mandato: [],
        },
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText("Nome não informado")).toBeInTheDocument();
    });

    it("deve exibir 'Nome não informado' quando last_name está vazio", () => {
      // Arrange
      const users: UserResponse[] = [
        {
          id: "1",
          first_name: "João",
          last_name: "",
          email: "joao@example.com",
          phone: "(11)98765-4321",
          permission_level: PermissionLevel.User,
          lgpd_check: true,
          role: "Assessor",
          mandato: [],
        },
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText("Nome não informado")).toBeInTheDocument();
    });

    it("deve exibir 'Nome não informado' quando ambos first_name e last_name estão vazios", () => {
      // Arrange
      const users: UserResponse[] = [
        {
          id: "1",
          first_name: "",
          last_name: "",
          email: "joao@example.com",
          phone: "(11)98765-4321",
          permission_level: PermissionLevel.User,
          lgpd_check: true,
          role: "Assessor",
          mandato: [],
        },
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText("Nome não informado")).toBeInTheDocument();
    });
  });

  describe("Emails dos usuários", () => {
    it("deve exibir o email de cada usuário corretamente", () => {
      // Arrange
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert
      expect(screen.getByText("joao@example.com")).toBeInTheDocument();
      expect(screen.getByText("maria@example.com")).toBeInTheDocument();
    });
  });

  describe("Integração com RemoveMember", () => {
    it("deve renderizar o componente RemoveMember para cada usuário", () => {
      // Arrange
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
      ];

      // Act
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que há 2 componentes RemoveMember (um para cada usuário)
      const removeButtons = screen.getAllByTestId("remove-member");
      expect(removeButtons).toHaveLength(2);
    });
  });

  describe("Filtragem e mensagens por permissão", () => {
    it("deve remover o usuário autenticado da lista de usuários", () => {
      // Arrange: Configura sessão com usuário de ID "123"
      setupSession("123", PermissionLevel.User);

      // Cria lista com o próprio usuário autenticado e outros usuários
      const users: UserResponse[] = [
        createMockUser("123", "Usuário", "Logado", "logado@example.com", PermissionLevel.User),
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
      ];

      // Act: Renderiza o componente
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que o usuário autenticado NÃO aparece na tabela
      expect(screen.queryByText("Usuário Logado")).not.toBeInTheDocument();
      expect(screen.queryByText("logado@example.com")).not.toBeInTheDocument();

      // Verifica que os outros usuários aparecem normalmente
      expect(screen.getByText("João Silva")).toBeInTheDocument();
      expect(screen.getByText("maria@example.com")).toBeInTheDocument();
    });

    it("deve mostrar hasThreeMembersNode se o usuário for Manager e tiver 3 membros na equipe", () => {
      // Arrange: Configura sessão com usuário Manager
      setupSession("999", PermissionLevel.Manager);

      // Cria 4 usuários não-managers (mais que o limite)
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
        createMockUser("3", "Pedro", "Costa", "pedro@example.com", PermissionLevel.User)
      ];

      // Act: Renderiza o componente
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que a mensagem de limite aparece
      expect(
        screen.getByText(/você atingiu o limite de três convites/i)
      ).toBeInTheDocument();

      // Verifica que o link de contato está presente
      expect(screen.getByText(/entre em contato com o nosso time/i)).toBeInTheDocument();
    });

    it("não deve mostrar hasThreeMembersNode se o usuário for Admin mesmo com mais de 3 membros", () => {
      // Arrange: Configura sessão com usuário Admin
      setupSession("999", PermissionLevel.Admin);

      // Cria 4 usuários não-managers (mais que o limite para Manager)
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
        createMockUser("3", "Pedro", "Costa", "pedro@example.com", PermissionLevel.User),
        createMockUser("4", "Ana", "Lima", "ana@example.com", PermissionLevel.User),
      ];

      // Act: Renderiza o componente
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que a mensagem de limite NÃO aparece (Admin não tem limite)
      expect(
        screen.queryByText(/você atingiu o limite de três convites/i)
      ).not.toBeInTheDocument();
    });

    it("não deve mostrar hasThreeMembersNode se o usuário for Manager mas tiver menos de 3 membros", () => {
      // Arrange: Configura sessão com usuário Manager
      setupSession("999", PermissionLevel.Manager);

      // Cria apenas 2 usuários não-managers (abaixo do limite)
      const users: UserResponse[] = [
        createMockUser("1", "João", "Silva", "joao@example.com", PermissionLevel.User),
        createMockUser("2", "Maria", "Santos", "maria@example.com", PermissionLevel.User),
      ];

      // Act: Renderiza o componente
      render(<MinhaEquipeTable users={users} />);

      // Assert: Verifica que a mensagem de limite NÃO aparece
      expect(
        screen.queryByText(/você atingiu o limite de três convites/i)
      ).not.toBeInTheDocument();
    });
  });
});

