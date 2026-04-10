import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DadosMandato } from "@/features/configurar-mandato/dados-mandato/dados-mandato";
import { Mandato } from "@/api/mandato/mandato.types";
import { toast } from "sonner";
import { PermissionLevel } from "@/types/user.types";
import { useSession } from "next-auth/react";

global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

const mockRouter = {
  refresh: jest.fn(),
  push: jest.fn(),
};

jest.mock("next/navigation", () => ({
  useRouter: () => mockRouter,
}));

// Mock do next-auth/react
jest.mock("next-auth/react", () => ({
  useSession: jest.fn(() => ({
    data: {
      user: {
        id: "1",
        permission_level: PermissionLevel.Manager,
      },
    },
    status: "authenticated",
  })),
}));

const mockMandato: Mandato = {
  id: 1,
  nome_parlamentar: "João Silva",                       //                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
  ue: "SP",
  municipio: "São Paulo",
  cargo_parlamentar: "Vereador",
  casa_legislativa: "Câmara Municipal",
  partido: "PT",
  perfil_parlamentar: "Legislador",
  espectro_politico: "De centro esquerda",
  users: [1],
  created_at: new Date().toISOString(),
  gerente: [
    {
      id: 1,
      nome: "Gerente Teste",
      email: "gerente@teste.com",
    },
  ],
};

describe("DadosMandato - Funcionalidade Principal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve renderizar o componente com os dados do mandato", () => {
    render(<DadosMandato mandato={mockMandato} />);

    expect(screen.getByText("Dados do Mandato")).toBeInTheDocument();
    expect(screen.getByDisplayValue("João Silva")).toBeInTheDocument();
    expect(screen.getByDisplayValue("SP")).toBeInTheDocument();
    expect(screen.getByDisplayValue("São Paulo")).toBeInTheDocument();
  });

  test("deve desabilitar campos somente leitura", () => {
    render(<DadosMandato mandato={mockMandato} />);

    const nomeParlamentarInput = screen.getByDisplayValue("João Silva");
    const ufInput = screen.getByDisplayValue("SP");
    const municipioInput = screen.getByDisplayValue("São Paulo");

    expect(nomeParlamentarInput).toHaveAttribute("readonly");
    expect(ufInput).toHaveAttribute("readonly");
    expect(municipioInput).toHaveAttribute("readonly");
  });

  test("deve exibir toast de sucesso ao atualizar dados", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        "Dados do mandato atualizados com sucesso"
      );
    });
  });

  test("deve chamar router.refresh após atualização bem-sucedida", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockRouter.refresh).toHaveBeenCalled();
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

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
    await userEvent.click(submitBtn);

    expect(submitBtn).toBeDisabled();
    expect(screen.getByRole("status")).toBeInTheDocument();

    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });

  test("deve permitir selecionar perfil parlamentar", async () => {
    render(<DadosMandato mandato={mockMandato} />);

    const articuladorRadio = screen.getByRole("radio", { name: /Articulador/i });
    await userEvent.click(articuladorRadio);

    expect(articuladorRadio).toBeChecked();
  });
});

describe("DadosMandato - Tratamento de Erros", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve exibir toast de erro quando a API retornar erro 400", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({}),
    });

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
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

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
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

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
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

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
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

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
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

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
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

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalled();
    });
  });

  test("não deve chamar router.refresh quando houver erro", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    render(<DadosMandato mandato={mockMandato} />);

    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockRouter.refresh).not.toHaveBeenCalled();
    });
  });
});

describe("DadosMandato - Controle de Permissões", () => {
  const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve permitir a edição de todos os campos quando o usuário é do tipo Admin", () => {
    // Arrange: Configura sessão com usuário Admin
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "1",
          permission_level: PermissionLevel.Admin,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<DadosMandato mandato={mockMandato} />);

    // Assert: Verifica que todos os campos estão editáveis (não readonly)
    const nomeParlamentarInput = screen.getByDisplayValue("João Silva");
    const ufInput = screen.getByDisplayValue("SP");
    const municipioInput = screen.getByDisplayValue("São Paulo");
    const cargoInput = screen.getByDisplayValue("Vereador");
    const casaLegislativaInput = screen.getByDisplayValue("Câmara Municipal");
    const comboboxButtons = screen.getAllByRole("combobox");
    const partidoButton = comboboxButtons.find(button => 
      button.textContent?.includes("PT") || button.textContent?.includes("Partido dos Trabalhadores")
    );
    if (!partidoButton) {
      throw new Error("Não foi possível encontrar o botão do partido político");
    }

    // Verifica que nenhum campo está readonly (Admin pode editar tudo)
    expect(nomeParlamentarInput).not.toHaveAttribute("readonly");
    expect(ufInput).not.toHaveAttribute("readonly");
    expect(municipioInput).not.toHaveAttribute("readonly");
    expect(cargoInput).not.toHaveAttribute("readonly");
    expect(casaLegislativaInput).not.toHaveAttribute("readonly");
    expect(partidoButton).not.toBeDisabled();

    // Verifica que os campos de perfil e posicionamento também estão habilitados
    const legisladorRadio = screen.getByRole("radio", { name: /Legislador/i });
    expect(legisladorRadio).not.toBeDisabled();
  });

  test("deve permitir a edição somente dos campos perfil do mandato e posicionamento do mandato quando o usuário é do tipo Manager", () => {
    // Arrange: Configura sessão com usuário Manager
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "1",
          permission_level: PermissionLevel.Manager,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<DadosMandato mandato={mockMandato} />);

    // Assert: Verifica que campos básicos estão readonly (Manager não pode editar)
    const nomeParlamentarInput = screen.getByDisplayValue("João Silva");
    const ufInput = screen.getByDisplayValue("SP");
    const municipioInput = screen.getByDisplayValue("São Paulo");
    const cargoInput = screen.getByDisplayValue("Vereador");
    const casaLegislativaInput = screen.getByDisplayValue("Câmara Municipal");
    const comboboxButtons = screen.getAllByRole("combobox");
    const partidoButton = comboboxButtons.find(button => 
      button.textContent?.includes("PT") || button.textContent?.includes("Partido dos Trabalhadores")
    );
    if (!partidoButton) {
      throw new Error("Não foi possível encontrar o botão do partido político");
    }

    expect(nomeParlamentarInput).toHaveAttribute("readonly");
    expect(ufInput).toHaveAttribute("readonly");
    expect(municipioInput).toHaveAttribute("readonly");
    expect(cargoInput).toHaveAttribute("readonly");
    expect(casaLegislativaInput).toHaveAttribute("readonly");
    expect(partidoButton).toBeDisabled();

    // Verifica que os campos de perfil e posicionamento estão habilitados (Manager pode editar)
    const legisladorRadio = screen.getByRole("radio", { name: /Legislador/i });
    expect(legisladorRadio).not.toBeDisabled();

    // Verifica que o select de posicionamento não está desabilitado
    const comboboxes = screen.getAllByRole("combobox");
    const posicionamentoSelect = comboboxes.find(combobox => 
      combobox.textContent?.includes("Posicionamento") || 
      combobox.textContent?.includes("De centro esquerda") ||
      combobox.getAttribute("aria-label")?.includes("posicionamento")
    ) || comboboxes[comboboxes.length - 1]; // Pega o último combobox (posicionamento)
    expect(posicionamentoSelect).not.toBeDisabled();
  });

  test("deve bloquear edição de todos os campos quando o usuário é do tipo User", () => {
    // Arrange: Configura sessão com usuário User
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "1",
          permission_level: PermissionLevel.User,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<DadosMandato mandato={mockMandato} />);

    // Assert: Verifica que todos os campos de input estão readonly
    const nomeParlamentarInput = screen.getByDisplayValue("João Silva");
    const ufInput = screen.getByDisplayValue("SP");
    const municipioInput = screen.getByDisplayValue("São Paulo");
    const cargoInput = screen.getByDisplayValue("Vereador");
    const casaLegislativaInput = screen.getByDisplayValue("Câmara Municipal");
    const comboboxButtons = screen.getAllByRole("combobox");
    const partidoButton = comboboxButtons.find(button => 
      button.textContent?.includes("PT") || button.textContent?.includes("Partido dos Trabalhadores")
    );
    if (!partidoButton) {
      throw new Error("Não foi possível encontrar o botão do partido político");
    }

    expect(nomeParlamentarInput).toHaveAttribute("readonly");
    expect(ufInput).toHaveAttribute("readonly");
    expect(municipioInput).toHaveAttribute("readonly");
    expect(cargoInput).toHaveAttribute("readonly");
    expect(casaLegislativaInput).toHaveAttribute("readonly");
    expect(partidoButton).toBeDisabled();

    // Verifica que os campos de perfil e posicionamento estão desabilitados
    const legisladorRadio = screen.getByRole("radio", { name: /Legislador/i });
    expect(legisladorRadio).toBeDisabled();

    const comboboxes = screen.getAllByRole("combobox");
    const posicionamentoSelect = comboboxes.find(combobox => 
      combobox.textContent?.includes("Posicionamento") || 
      combobox.textContent?.includes("De centro esquerda") ||
      combobox.getAttribute("aria-label")?.includes("posicionamento")
    ) || comboboxes[comboboxes.length - 1]; // Pega o último combobox (posicionamento)
    expect(posicionamentoSelect).toBeDisabled();
  });

  test("deve desabilitar o botão de salvar quando o usuário é do tipo User", () => {
    // Arrange: Configura sessão com usuário User
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "1",
          permission_level: PermissionLevel.User,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<DadosMandato mandato={mockMandato} />);

    // Assert: Verifica que o botão de salvar está desabilitado
    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
    expect(submitBtn).toBeDisabled();
  });

  test("deve bloquear edição de todos os campos quando o usuário é do tipo Viewer", () => {
    // Arrange: Configura sessão com usuário Viewer
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "1",
          permission_level: PermissionLevel.Viewer,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<DadosMandato mandato={mockMandato} />);

    // Assert: Verifica que todos os campos de input estão readonly
    const nomeParlamentarInput = screen.getByDisplayValue("João Silva");
    const ufInput = screen.getByDisplayValue("SP");
    const municipioInput = screen.getByDisplayValue("São Paulo");
    const cargoInput = screen.getByDisplayValue("Vereador");
    const casaLegislativaInput = screen.getByDisplayValue("Câmara Municipal");
    const comboboxButtons = screen.getAllByRole("combobox");
    const partidoButton = comboboxButtons.find(button => 
      button.textContent?.includes("PT") || button.textContent?.includes("Partido dos Trabalhadores")
    );
    if (!partidoButton) {
      throw new Error("Não foi possível encontrar o botão do partido político");
    }

    expect(nomeParlamentarInput).toHaveAttribute("readonly");
    expect(ufInput).toHaveAttribute("readonly");
    expect(municipioInput).toHaveAttribute("readonly");
    expect(cargoInput).toHaveAttribute("readonly");
    expect(casaLegislativaInput).toHaveAttribute("readonly");
    expect(partidoButton).toBeDisabled();

    // Verifica que os campos de perfil e posicionamento estão desabilitados
    const legisladorRadio = screen.getByRole("radio", { name: /Legislador/i });
    expect(legisladorRadio).toBeDisabled();

    const comboboxes = screen.getAllByRole("combobox");
    const posicionamentoSelect = comboboxes.find(combobox => 
      combobox.textContent?.includes("Posicionamento") || 
      combobox.textContent?.includes("De centro esquerda") ||
      combobox.getAttribute("aria-label")?.includes("posicionamento")
    ) || comboboxes[comboboxes.length - 1]; // Pega o último combobox (posicionamento)
    expect(posicionamentoSelect).toBeDisabled();
  });

  test("deve desabilitar o botão de salvar quando o usuário é do tipo Viewer", () => {
    // Arrange: Configura sessão com usuário Viewer
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "1",
          permission_level: PermissionLevel.Viewer,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<DadosMandato mandato={mockMandato} />);

    // Assert: Verifica que o botão de salvar está desabilitado
    const submitBtn = screen.getByRole("button", { name: /Salvar alterações/i });
    expect(submitBtn).toBeDisabled();
  });

  test("deve permitir que usuário User visualize os dados do mandato", () => {
    // Arrange: Configura sessão com usuário User
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "1",
          permission_level: PermissionLevel.User,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<DadosMandato mandato={mockMandato} />);

    // Assert: Verifica que todos os dados estão visíveis
    expect(screen.getByText("Dados do Mandato")).toBeInTheDocument();
    expect(screen.getByDisplayValue("João Silva")).toBeInTheDocument();
    expect(screen.getByDisplayValue("SP")).toBeInTheDocument();
    expect(screen.getByDisplayValue("São Paulo")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Vereador")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Câmara Municipal")).toBeInTheDocument();
    expect(screen.getByText(/Partido dos Trabalhadores \(PT\)/i)).toBeInTheDocument();
  });

  test("deve permitir que usuário Viewer visualize os dados do mandato", () => {
    // Arrange: Configura sessão com usuário Viewer
    mockUseSession.mockReturnValue({
      data: {
        user: {
          id: "1",
          permission_level: PermissionLevel.Viewer,
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      status: "authenticated",
      update: jest.fn(),
    });

    // Act: Renderiza o componente
    render(<DadosMandato mandato={mockMandato} />);

    // Assert: Verifica que todos os dados estão visíveis
    expect(screen.getByText("Dados do Mandato")).toBeInTheDocument();
    expect(screen.getByDisplayValue("João Silva")).toBeInTheDocument();
    expect(screen.getByDisplayValue("SP")).toBeInTheDocument();
    expect(screen.getByDisplayValue("São Paulo")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Vereador")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Câmara Municipal")).toBeInTheDocument();
    expect(screen.getByText(/Partido dos Trabalhadores \(PT\)/i)).toBeInTheDocument();
  });
});
