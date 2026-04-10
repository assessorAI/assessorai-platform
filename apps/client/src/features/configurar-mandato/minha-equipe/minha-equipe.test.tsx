import React from "react";
import { render, screen } from "@testing-library/react";
import { MinhaEquipe } from "./minha-equipe";
import { UserResponse } from "@/api/user/user.types";
import { PermissionLevel } from "@/types/user.types";
import { useSession } from "next-auth/react";

// Mock do módulo de estilos SCSS
jest.mock("./minha-equipe.module.scss", () => ({}));

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

// Mock do next/navigation
jest.mock("next/navigation", () => ({
  useParams: jest.fn(() => ({ id: "mandato-123" })),
  useRouter: jest.fn(() => ({
    refresh: jest.fn(),
    push: jest.fn(),
  })),
}));

// Mock do fetch global
global.fetch = jest.fn();

// Mock do sonner (biblioteca de toast)
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Dados mock de usuários
const mockUsers: UserResponse[] = [
  {
    id: "1",
    email: "usuario1@example.com",
    first_name: "João",
    last_name: "Silva",
    phone: "",
    permission_level: PermissionLevel.Manager,
    lgpd_check: true,
    role: "Chefe de Gabinete",
    mandato: [],
  },
  {
    id: "2",
    email: "usuario2@example.com",
    first_name: "Maria",
    last_name: "Santos",
    phone: "",
    permission_level: PermissionLevel.User,
    lgpd_check: true,
    role: "Assessor Legislativo",
    mandato: [],
  },
];

describe("MinhaEquipe - Controle de Permissões", () => {
  const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve renderizar formulário e tabela quando o usuário é do tipo Admin", () => {
    // Arrange: Configura sessão com usuário Admin
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "999",
          permission_level: PermissionLevel.Admin,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<MinhaEquipe users={mockUsers} />);

    // Assert: Verifica que o título está presente
    expect(screen.getByText("Minha equipe")).toBeInTheDocument();

    // Verifica que a descrição está presente (apenas para quem pode adicionar)
    expect(
      screen.getByText(
        /Envie convite para até três membros da sua equipe digitando o email do convidado abaixo/i
      )
    ).toBeInTheDocument();

    // Verifica que o formulário está presente (campo de email)
    expect(screen.getByRole("textbox", { name: /email/i })).toBeInTheDocument();

    // Verifica que a tabela está presente
    expect(screen.getByText("usuario1@example.com")).toBeInTheDocument();
    expect(screen.getByText("usuario2@example.com")).toBeInTheDocument();
  });

  test("deve renderizar formulário e tabela quando o usuário é do tipo Manager", () => {
    // Arrange: Configura sessão com usuário Manager
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "999",
          permission_level: PermissionLevel.Manager,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<MinhaEquipe users={mockUsers} />);

    // Assert: Verifica que o título está presente
    expect(screen.getByText("Minha equipe")).toBeInTheDocument();

    // Verifica que a descrição está presente
    expect(
      screen.getByText(
        /Envie convite para até três membros da sua equipe digitando o email do convidado abaixo/i
      )
    ).toBeInTheDocument();

    // Verifica que o formulário está presente
    expect(screen.getByRole("textbox", { name: /email/i })).toBeInTheDocument();

    // Verifica que a tabela está presente
    expect(screen.getByText("usuario1@example.com")).toBeInTheDocument();
    expect(screen.getByText("usuario2@example.com")).toBeInTheDocument();
  });

  test("deve renderizar apenas tabela (sem formulário) quando o usuário é do tipo User", () => {
    // Arrange: Configura sessão com usuário User
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "999",
          permission_level: PermissionLevel.User,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<MinhaEquipe users={mockUsers} />);

    // Assert: Verifica que o título está presente
    expect(screen.getByText("Minha equipe")).toBeInTheDocument();

    // Verifica que a descrição NÃO está presente (User não pode adicionar)
    expect(
      screen.queryByText(
        /Envie convite para até três membros da sua equipe digitando o email do convidado abaixo/i
      )
    ).not.toBeInTheDocument();

    // Verifica que o formulário NÃO está presente
    expect(screen.queryByRole("textbox", { name: /email/i })).not.toBeInTheDocument();

    // Verifica que a tabela ESTÁ presente (User pode visualizar)
    expect(screen.getByText("usuario1@example.com")).toBeInTheDocument();
    expect(screen.getByText("usuario2@example.com")).toBeInTheDocument();
  });

  test("deve renderizar apenas tabela (sem formulário) quando o usuário é do tipo Viewer", () => {
    // Arrange: Configura sessão com usuário Viewer
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "999",
          permission_level: PermissionLevel.Viewer,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<MinhaEquipe users={mockUsers} />);

    // Assert: Verifica que o título está presente
    expect(screen.getByText("Minha equipe")).toBeInTheDocument();

    // Verifica que a descrição NÃO está presente
    expect(
      screen.queryByText(
        /Envie convite para até três membros da sua equipe digitando o email do convidado abaixo/i
      )
    ).not.toBeInTheDocument();

    // Verifica que o formulário NÃO está presente
    expect(screen.queryByRole("textbox", { name: /email/i })).not.toBeInTheDocument();

    // Verifica que a tabela ESTÁ presente (Viewer pode visualizar)
    expect(screen.getByText("usuario1@example.com")).toBeInTheDocument();
    expect(screen.getByText("usuario2@example.com")).toBeInTheDocument();
  });

  test("deve permitir que usuário User visualize todos os membros da equipe", () => {
    // Arrange: Configura sessão com usuário User
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "999",
          permission_level: PermissionLevel.User,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<MinhaEquipe users={mockUsers} />);

    // Assert: Verifica que todos os usuários estão visíveis na tabela
    expect(screen.getByText("João Silva")).toBeInTheDocument();
    expect(screen.getByText("Maria Santos")).toBeInTheDocument();
    expect(screen.getByText("usuario1@example.com")).toBeInTheDocument();
    expect(screen.getByText("usuario2@example.com")).toBeInTheDocument();
    
    // Verifica que os status estão visíveis
    const membrosAtivos = screen.getAllByText("Membro ativo");
    expect(membrosAtivos).toHaveLength(2);
  });

  test("deve permitir que usuário Viewer visualize todos os membros da equipe", () => {
    // Arrange: Configura sessão com usuário Viewer
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "999",
          permission_level: PermissionLevel.Viewer,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<MinhaEquipe users={mockUsers} />);

    // Assert: Verifica que todos os usuários estão visíveis na tabela
    expect(screen.getByText("João Silva")).toBeInTheDocument();
    expect(screen.getByText("Maria Santos")).toBeInTheDocument();
    expect(screen.getByText("usuario1@example.com")).toBeInTheDocument();
    expect(screen.getByText("usuario2@example.com")).toBeInTheDocument();
    
    // Verifica que os status estão visíveis
    const membrosAtivos = screen.getAllByText("Membro ativo");
    expect(membrosAtivos).toHaveLength(2);
  });
});

