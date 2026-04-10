import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ShowMandato } from "./show-mandato";
import { Mandato } from "@/api/mandato/mandato.types";
import { useHandleBuscaCampos } from "@/hooks/useHandleGetFields";
import { restClient } from "@/lib/rest-client";
import { toast } from "sonner";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock das dependências
jest.mock("@/hooks/useHandleGetFields");
jest.mock("@/lib/rest-client");
jest.mock("sonner");

// Mock dos dados de mandato
const mockMandato: Mandato = {
  id: 1,
  nome_parlamentar: "Deputado João Silva",
  cargo_parlamentar: "Deputado Estadual",
  casa_legislativa: "Assembleia Legislativa do Estado de São Paulo",
  partido: "NOVO",
  ue: "SP",
  municipio: "São Paulo",
  espectro_politico: "De direita",
  perfil_parlamentar: "Legislador",
  users: [1],
  gerente: [
    {
      id: 1,
      nome: "Gerente Teste",
      email: "gerente@teste.com",
    },
  ],
  created_at: "2024-01-01T00:00:00.000Z",
};

// Mock dos dados de UFs e municípios
const mockUfList = [
  { id: 1, sigla: "SP", nome: "São Paulo" },
  { id: 2, sigla: "RJ", nome: "Rio de Janeiro" },
];

const mockMunicipioList = [
  { id: 1, nome: "São Paulo" },
  { id: 2, nome: "Campinas" },
  { id: 3, nome: "Santos" },
];

// Helper function para renderizar o componente com o wrapper do Sheet
const renderShowMandato = (mandato: Mandato) => {
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
          <ShowMandato mandato={mandato} />
        </SheetContent>
      </Sheet>
    </QueryClientProvider>
  );
};

describe("ShowMandato Component", () => {
  const mockHandleBuscaUF = jest.fn();
  const mockHandleBuscaMunicipios = jest.fn();
  const mockGetCasaLegislativa = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock padrão do hook useHandleBuscaCampos
    (useHandleBuscaCampos as jest.Mock).mockReturnValue({
      ufList: mockUfList,
      municipioList: mockMunicipioList,
      getCasaLegislativa: mockGetCasaLegislativa,
      handleBuscaUF: mockHandleBuscaUF,
      handleBuscaMunicipios: mockHandleBuscaMunicipios,
      isLoading: false,
      error: null,
    });

    mockGetCasaLegislativa.mockReturnValue(
      "Assembleia Legislativa do Estado de São Paulo"
    );
  });

  describe("Renderização inicial", () => {
    it("deve renderizar os detalhes do mandato corretamente", () => {
      renderShowMandato(mockMandato);

      // Verificar título
      expect(screen.getByText("Detalhes do mandato")).toBeInTheDocument();

      // Verificar campos do formulário
      expect(screen.getByDisplayValue("Deputado João Silva")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Deputado Estadual")).toBeInTheDocument();
      expect(
        screen.getByDisplayValue("Assembleia Legislativa do Estado de São Paulo")
      ).toBeInTheDocument();
    });

    it("deve renderizar os campos desabilitados inicialmente", () => {
      renderShowMandato(mockMandato);

      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      expect(nomeInput).toBeDisabled();
    });

    it("não deve exibir os botões de salvar e cancelar inicialmente", () => {
      renderShowMandato(mockMandato);

      expect(screen.queryByText("Salvar alterações")).not.toBeInTheDocument();
      expect(screen.queryByText("Cancelar")).not.toBeInTheDocument();
    });

    it("deve carregar a lista de UFs ao montar o componente", () => {
      renderShowMandato(mockMandato);

      expect(mockHandleBuscaUF).toHaveBeenCalledTimes(1);
    });
  });

  describe("Modo de edição", () => {
    it("deve ativar o modo de edição ao clicar no botão de editar", async () => {
      const user = userEvent.setup();
      renderShowMandato(mockMandato);

      // Buscar botão de editar (ícone de lápis)
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Verificar se os campos ficaram habilitados
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      expect(nomeInput).not.toBeDisabled();

      // Verificar se os botões de ação aparecem
      expect(screen.getByText("Salvar alterações")).toBeInTheDocument();
      expect(screen.getByText("Cancelar")).toBeInTheDocument();
    });

    it("deve desabilitar o botão salvar se o formulário não estiver válido", async () => {
      const user = userEvent.setup();
      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // O botão deve estar desabilitado pois não há mudanças
      const saveButton = screen.getByText("Salvar alterações");
      expect(saveButton).toBeDisabled();
    });

    it("deve habilitar o botão salvar quando houver mudanças válidas", async () => {
      const user = userEvent.setup();
      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Deputado Maria Santos");

      // Aguardar validação
      await waitFor(() => {
        const saveButton = screen.getByText("Salvar alterações");
        expect(saveButton).not.toBeDisabled();
      });
    });
  });

  describe("Salvar alterações", () => {
    it("deve salvar as alterações com sucesso", async () => {
      const user = userEvent.setup();
      (restClient as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Deputado Maria Santos");

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
          "/api/mandato/1",
          expect.objectContaining({
            method: "PUT",
          })
        );
      });

      // Verificar toast de sucesso
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("Mandato atualizado com sucesso");
      });
    });

    it("deve exibir erro ao falhar ao salvar", async () => {
      const user = userEvent.setup();
      const errorMessage = { customMessage: "Erro ao atualizar mandato" };
      (restClient as jest.Mock).mockRejectedValueOnce(errorMessage);

      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Deputado Maria Santos");

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
        expect(toast.error).toHaveBeenCalledWith("Erro ao atualizar mandato");
      });
    });

    it("deve enviar os dados corretos na requisição", async () => {
      const user = userEvent.setup();
      (restClient as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Deputado Maria Santos");

      // Salvar
      await waitFor(() => {
        const saveButton = screen.getByText("Salvar alterações");
        expect(saveButton).not.toBeDisabled();
      });

      const saveButton = screen.getByText("Salvar alterações");
      await user.click(saveButton);

      // Confirmar no dialog
      await waitFor(() => {
        expect(screen.getByText("Deseja salvar as alterações?")).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole("button", { name: "Confirmar" });
      await user.click(confirmButton);

      // Verificar corpo da requisição
      await waitFor(() => {
        expect(restClient).toHaveBeenCalledWith(
          "/api/mandato/1",
          expect.objectContaining({
            method: "PUT",
            body: expect.stringContaining("Deputado Maria Santos"),
          })
        );
      });
    });
  });

  describe("Descartar alterações", () => {
    it("deve exibir dialog ao clicar em cancelar com alterações pendentes", async () => {
      const user = userEvent.setup();
      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.type(nomeInput, " Editado");

      // Clicar em cancelar
      const cancelButton = screen.getByText("Cancelar");
      await user.click(cancelButton);

      // Verificar dialog
      await waitFor(() => {
        expect(
          screen.getByText("Deseja descartar as alterações feitas?")
        ).toBeInTheDocument();
      });
    });

    it("deve descartar alterações ao confirmar no dialog", async () => {
      const user = userEvent.setup();
      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Deputado Maria Santos");

      // Clicar em cancelar
      const cancelButton = screen.getByText("Cancelar");
      await user.click(cancelButton);

      // Confirmar descarte
      await waitFor(() => {
        expect(
          screen.getByText("Deseja descartar as alterações feitas?")
        ).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole("button", { name: "Confirmar" });
      await user.click(confirmButton);

      // Verificar que o valor voltou ao original
      await waitFor(() => {
        expect(screen.getByDisplayValue("Deputado João Silva")).toBeInTheDocument();
        expect(screen.queryByDisplayValue("Deputado Maria Santos")).not.toBeInTheDocument();
      });
    });

    it("deve sair do modo de edição sem dialog quando não houver alterações", async () => {
      const user = userEvent.setup();
      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Verificar que está no modo de edição
      expect(screen.getByText("Salvar alterações")).toBeInTheDocument();

      // Clicar em cancelar sem fazer alterações
      const cancelButton = screen.getByText("Cancelar");
      await user.click(cancelButton);

      // Verificar que saiu do modo de edição sem exibir dialog
      await waitFor(() => {
        expect(
          screen.queryByText("Deseja descartar as alterações feitas?")
        ).not.toBeInTheDocument();
        expect(screen.queryByText("Salvar alterações")).not.toBeInTheDocument();
      });
    });

    it("deve cancelar o descarte ao clicar em cancelar no dialog", async () => {
      const user = userEvent.setup();
      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.type(nomeInput, " Editado");

      // Clicar em cancelar
      const cancelButton = screen.getByText("Cancelar");
      await user.click(cancelButton);

      // Aguardar dialog aparecer
      await waitFor(() => {
        expect(
          screen.getByText("Deseja descartar as alterações feitas?")
        ).toBeInTheDocument();
      });

      // Cancelar o descarte
      const dialogCancelButton = screen.getByRole("button", { name: "Cancelar" });
      await user.click(dialogCancelButton);

      // Verificar que ainda está no modo de edição
      await waitFor(() => {
        expect(screen.getByText("Salvar alterações")).toBeInTheDocument();
      });
    });
  });

  describe("Toggle do modo de edição", () => {
    it("deve sair do modo de edição e resetar o form ao clicar no botão de editar novamente", async () => {
      const user = userEvent.setup();
      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Deputado Maria Santos");

      // Clicar no botão de editar novamente
      await user.click(editButton);

      // Verificar que saiu do modo de edição e resetou o formulário
      await waitFor(() => {
        expect(screen.queryByText("Salvar alterações")).not.toBeInTheDocument();
        expect(screen.getByDisplayValue("Deputado João Silva")).toBeInTheDocument();
      });
    });
  });

  describe("Estados de carregamento", () => {
    it("deve exibir o spinner enquanto salva as alterações", async () => {
      const user = userEvent.setup();
      let resolvePromise: (value: unknown) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      (restClient as jest.Mock).mockReturnValueOnce(promise);

      renderShowMandato(mockMandato);

      // Ativar modo de edição
      const editButton = screen.getByRole("button", { name: "" });
      await user.click(editButton);

      // Fazer uma alteração
      const nomeInput = screen.getByDisplayValue("Deputado João Silva");
      await user.clear(nomeInput);
      await user.type(nomeInput, "Deputado Maria Santos");

      // Salvar
      await waitFor(() => {
        const saveButton = screen.getByText("Salvar alterações");
        expect(saveButton).not.toBeDisabled();
      });

      const saveButton = screen.getByText("Salvar alterações");
      await user.click(saveButton);

      // Confirmar no dialog
      await waitFor(() => {
        expect(screen.getByText("Deseja salvar as alterações?")).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole("button", { name: "Confirmar" });
      await user.click(confirmButton);

      // Verificar que o spinner aparece (você pode precisar ajustar o seletor do spinner)
      await waitFor(() => {
        expect(saveButton).toContainHTML("svg");
      });

      // Resolver a promise para limpar o teste
      resolvePromise!({ ok: true, json: async () => ({}) });
    });
  });
});