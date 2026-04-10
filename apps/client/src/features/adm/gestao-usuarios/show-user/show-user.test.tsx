import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ShowUser } from "./show-user";
import { UserResponse } from "@/api/user/user.types";
import { PermissionLevel } from "@/types/user.types";
import { restClient } from "@/lib/rest-client";
import { toast } from "sonner";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock das dependências
jest.mock("@/lib/rest-client");
jest.mock("sonner");
jest.mock("@/lib/get-mandatos");

// Mock dos dados de usuário
const mockUser: UserResponse = {
    id: "1",
    first_name: "João",
    last_name: "Silva",
    email: "joao@example.com",
    phone: "(11)98765-4321",
    role: "Assessor Legislativo",
    permission_level: PermissionLevel.User,
    lgpd_check: true,
    last_login: new Date().toISOString(),
    mandato: [
      {
        id: 1,
        nome_parlamentar: "Deputado Teste",
        casa_legislativa: "Casa Teste",
        ue: "SP",
        municipio: "São Paulo",
        partido: "PT",
        cargo_parlamentar: "Deputado",
        perfil_parlamentar: "Legislador",
        espectro_politico: "De esquerda",
        users: [1],
        created_at: new Date().toISOString(),
        gerente: [
          {
            id: 1,
            nome: "Gerente Teste",
            email: "gerente@teste.com",
          },
        ],
      },
    ],
  };
  

// Helper function para renderizar o componente com o wrapper do Sheet
const renderShowUser = (user: UserResponse) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <Sheet open={true}>
        <SheetContent>
          <ShowUser user={user} />
        </SheetContent>
      </Sheet>
    </QueryClientProvider>
  );
};

describe("ShowUser Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Renderização inicial", () => {
    it("deve renderizar os detalhes do usuário corretamente", () => {
      renderShowUser(mockUser);

      // Verificar título
      expect(screen.getByText("Detalhes do usuário")).toBeInTheDocument();

      // Verificar campos do formulário
      expect(screen.getByDisplayValue("João")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Silva")).toBeInTheDocument();
      expect(screen.getByDisplayValue("joao@example.com")).toBeInTheDocument();
      expect(screen.getByDisplayValue("(11)98765-4321")).toBeInTheDocument();
    });

    it("deve renderizar os campos desabilitados inicialmente", () => {
      renderShowUser(mockUser);

      const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
      const lastNameInput = screen.getByPlaceholderText("Seu sobrenome");

      expect(firstNameInput).toBeDisabled();
      expect(lastNameInput).toBeDisabled();
    });

    it("não deve exibir os botões de salvar e cancelar inicialmente", () => {
      renderShowUser(mockUser);

      expect(screen.queryByText("Salvar alterações")).not.toBeInTheDocument();
      expect(screen.queryByText("Cancelar")).not.toBeInTheDocument();
    });
  });

  describe("Modo de edição", () => {
    it("deve ativar o modo de edição ao clicar no botão de editar", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Buscar botão de editar (ícone de lápis)
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Verificar se os campos ficaram habilitados
      const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
      expect(firstNameInput).not.toBeDisabled();

      // Verificar se os botões de ação aparecem
      expect(screen.getByText("Salvar alterações")).toBeInTheDocument();
      expect(screen.getByText("Cancelar")).toBeInTheDocument();
    });

    it("deve desabilitar o botão salvar se o formulário não estiver válido", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // O botão deve estar desabilitado pois não há mudanças
      const saveButton = screen.getByText("Salvar alterações");
      expect(saveButton).toBeDisabled();
    });

    it("deve habilitar o botão salvar quando houver mudanças válidas", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Fazer uma alteração
      const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
      await user.clear(firstNameInput);
      await user.type(firstNameInput, "Maria");

      // Aguardar validação
      await waitFor(() => {
        const saveButton = screen.getByText("Salvar alterações");
        expect(saveButton).not.toBeDisabled();
      });
    });
  });

  describe("Validação do formulário", () => {
    it("deve exibir erro quando o nome tiver menos de 2 caracteres", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Digitar nome inválido
      const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
      await user.clear(firstNameInput);
      await user.type(firstNameInput, "J");

      // Verificar mensagem de erro
      await waitFor(() => {
        expect(screen.getByText("Nome deve ter no mínimo 2 caracteres")).toBeInTheDocument();
      });
    });

    it("deve exibir erro quando o email for inválido", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Digitar email inválido
      const emailInput = screen.getByPlaceholderText("seu@email.com");
      await user.clear(emailInput);
      await user.type(emailInput, "emailinvalido");

      // Verificar mensagem de erro
      await waitFor(() => {
        expect(screen.getByText("Email inválido")).toBeInTheDocument();
      });
    });

    it("deve exibir erro quando as senhas não conferirem", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Encontrar os campos de senha
      const senhaInputs = screen.getAllByLabelText(/senha/i);
      const passwordInput = senhaInputs[0];
      const confirmPasswordInput = senhaInputs[1];

      // Digitar senhas diferentes
      await user.type(passwordInput, "senha123");
      await user.type(confirmPasswordInput, "senha456");

      // Verificar mensagem de erro
      await waitFor(() => {
        expect(screen.getByText("As senhas não conferem")).toBeInTheDocument();
      });
    });

    it("deve aceitar quando o campo senha estiver vazio", async () => {
        const user = userEvent.setup();
        renderShowUser(mockUser);
      
        // Ativar modo de edição
        const editButton = screen.getByRole("button", { name: "Editar usuário" });
        await user.click(editButton);
      
        // Fazer uma alteração no nome para ativar o botão
        const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
        await user.clear(firstNameInput);
        await user.type(firstNameInput, "Maria");
      
        // Garantir que os campos de senha estão vazios
        const senhaInputs = screen.getAllByLabelText(/senha/i);
        const passwordInput = senhaInputs[0] as HTMLInputElement;
        const confirmPasswordInput = senhaInputs[1] as HTMLInputElement;
        
        expect(passwordInput.value).toBe("");
        expect(confirmPasswordInput.value).toBe("");
      
        // Não deve ter erro de senha
        await waitFor(() => {
          expect(screen.queryByText("As senhas não conferem")).not.toBeInTheDocument();
          expect(screen.queryByText("Senha deve ter no mínimo 6 caracteres")).not.toBeInTheDocument();
        });
      
        // O botão de salvar deve estar habilitado pois há alterações válidas
        const saveButton = screen.getByText("Salvar alterações");
        expect(saveButton).not.toBeDisabled();
      });
  });

  describe("Salvar alterações", () => {
    it("deve salvar as alterações com sucesso", async () => {
      const user = userEvent.setup();
      (restClient as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Fazer uma alteração
      const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
      await user.clear(firstNameInput);
      await user.type(firstNameInput, "Maria");

      // Salvar
      await waitFor(() => {
        const saveButton = screen.getByText("Salvar alterações");
        expect(saveButton).not.toBeDisabled();
      });

      const saveButton = screen.getByText("Salvar alterações");
      await user.click(saveButton);

      // Aguardar o dialog de confirmação
      await waitFor(() => {
        expect(screen.getByText("Deseja salvar as alterações?")).toBeInTheDocument();
      });

      // Confirmar
      const confirmButton = screen.getByRole("button", { name: "Confirmar" });
      await user.click(confirmButton);

      // Verificar se a requisição foi feita
      await waitFor(() => {
        expect(restClient).toHaveBeenCalledWith(
          "/api/user/1",
          expect.objectContaining({
            method: "PUT",
          })
        );
      });

      // Verificar toast de sucesso
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("Usuário atualizado com sucesso");
      });
    });

    it("deve exibir erro ao falhar ao salvar", async () => {
      const user = userEvent.setup();
      const errorMessage = { customMessage: "Erro ao atualizar usuário" };
      (restClient as jest.Mock).mockRejectedValueOnce(errorMessage);

      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Fazer uma alteração
      const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
      await user.clear(firstNameInput);
      await user.type(firstNameInput, "Maria");

      // Salvar
      await waitFor(() => {
        const saveButton = screen.getByText("Salvar alterações");
        expect(saveButton).not.toBeDisabled();
      });

      const saveButton = screen.getByText("Salvar alterações");
      await user.click(saveButton);

      // Aguardar o dialog de confirmação
      await waitFor(() => {
        expect(screen.getByText("Deseja salvar as alterações?")).toBeInTheDocument();
      });

      // Confirmar
      const confirmButton = screen.getByRole("button", { name: "Confirmar" });
      await user.click(confirmButton);

      // Verificar toast de erro
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith("Erro ao atualizar usuário");
      });
    });
  });

  describe("Descartar alterações", () => {
    it("deve exibir dialog ao clicar em cancelar com alterações pendentes", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Fazer uma alteração
      const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
      await user.type(firstNameInput, "Teste");

      // Clicar em cancelar
      const cancelButton = screen.getByText("Cancelar");
      await user.click(cancelButton);

      // Verificar dialog
      await waitFor(() => {
        expect(screen.getByText("Deseja descartar as alterações feitas?")).toBeInTheDocument();
      });
    });

    it("deve descartar alterações ao confirmar no dialog", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Fazer uma alteração
      const firstNameInput = screen.getByPlaceholderText("Seu primeiro nome");
      await user.clear(firstNameInput);
      await user.type(firstNameInput, "Maria");

      // Clicar em cancelar
      const cancelButton = screen.getByText("Cancelar");
      await user.click(cancelButton);

      // Confirmar descarte
      await waitFor(() => {
        expect(screen.getByText("Deseja descartar as alterações feitas?")).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole("button", { name: "Confirmar" });
      await user.click(confirmButton);

      // Verificar que o valor voltou ao original
      await waitFor(() => {
        expect(screen.getByDisplayValue("João")).toBeInTheDocument();
        expect(screen.queryByDisplayValue("Maria")).not.toBeInTheDocument();
      });
    });

    it("deve sair do modo de edição sem dialog quando não houver alterações", async () => {
      const user = userEvent.setup();
      renderShowUser(mockUser);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "Editar usuário" });
      await user.click(editButton);

      // Verificar que está no modo de edição
      expect(screen.getByText("Salvar alterações")).toBeInTheDocument();

      // Clicar em cancelar sem fazer alterações
      const cancelButton = screen.getByText("Cancelar");
      await user.click(cancelButton);

      // Verificar que saiu do modo de edição sem exibir dialog
      await waitFor(() => {
        expect(screen.queryByText("Deseja descartar as alterações feitas?")).not.toBeInTheDocument();
        expect(screen.queryByText("Salvar alterações")).not.toBeInTheDocument();
      });
    });
  });

});