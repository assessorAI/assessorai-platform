import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ComboboxAsync } from "./combobox-async";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PaginatedResponse } from "./combobox-async.types";

// ResizeObserver não existe no jsdom - necessário para o cmdk (Command)
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock do useDebounce - retorna o valor imediatamente para simplificar os testes
jest.mock("@/hooks/useDebounce", () => ({
  useDebounce: <T,>(value: T) => value,
}));

type MockItem = {
  id: number;
  name: string;
};

const createMockFetchOptions = (items: MockItem[]): jest.Mock => {
  return jest.fn().mockResolvedValue({
    data: items,
    total: items.length,
    offset: 0,
    limit: 20,
    hasMore: false,
  } satisfies PaginatedResponse<MockItem>);
};

const defaultItems: MockItem[] = [
  { id: 1, name: "Opção A" },
  { id: 2, name: "Opção B" },
  { id: 3, name: "Opção C" },
];

const defaultProps = {
  fetchOptions: createMockFetchOptions(defaultItems),
  getOptionLabel: (item: MockItem) => item.name,
  getOptionValue: (item: MockItem) => String(item.id),
  queryKey: ["test-combobox"],
};

const renderComboboxAsync = (
  props: Partial<{
    value: MockItem | null;
    onValueChange: jest.Mock;
    placeholder: string;
    emptyText: string;
    disabled: boolean;
    readOnly: boolean;
  }> = {}
) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ComboboxAsync<MockItem>
        {...defaultProps}
        value={props.value ?? null}
        onValueChange={props.onValueChange ?? jest.fn()}
        placeholder={props.placeholder ?? "Selecione..."}
        emptyText={props.emptyText ?? "Nenhum resultado encontrado"}
        disabled={props.disabled ?? false}
        readOnly={props.readOnly ?? false}
      />
    </QueryClientProvider>
  );
};

describe("ComboboxAsync", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Renderização inicial", () => {
    it("deve exibir o placeholder quando nenhum valor está selecionado", () => {
      renderComboboxAsync();

      expect(screen.getByRole("combobox")).toHaveTextContent("Selecione...");
    });

    it("deve exibir placeholder customizado quando fornecido", () => {
      renderComboboxAsync({ placeholder: "Escolha uma opção" });

      expect(screen.getByRole("combobox")).toHaveTextContent("Escolha uma opção");
    });

    it("deve exibir o label do item selecionado quando há valor", () => {
      renderComboboxAsync({ value: { id: 1, name: "Opção A" } });

      expect(screen.getByRole("combobox")).toHaveTextContent("Opção A");
    });
  });

  describe("Interação com o popover", () => {
    it("deve abrir o popover ao clicar no trigger e buscar opções", async () => {
      const user = userEvent.setup();
      const fetchOptions = createMockFetchOptions(defaultItems);
      render(
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <ComboboxAsync<MockItem>
            {...defaultProps}
            fetchOptions={fetchOptions}
          />
        </QueryClientProvider>
      );

      const trigger = screen.getByRole("combobox");
      await user.click(trigger);

      await waitFor(() => {
        expect(fetchOptions).toHaveBeenCalledWith({
          search: "",
          offset: 0,
          limit: 20,
        });
      });
    });

    it("deve exibir opções quando carregadas", async () => {
      const user = userEvent.setup();
      renderComboboxAsync();

      await user.click(screen.getByRole("combobox"));

      await waitFor(() => {
        expect(screen.getByText("Opção A")).toBeInTheDocument();
        expect(screen.getByText("Opção B")).toBeInTheDocument();
        expect(screen.getByText("Opção C")).toBeInTheDocument();
      });
    });

    it("deve exibir loading durante a busca inicial", async () => {
      const user = userEvent.setup();
      let resolvePromise: (value: PaginatedResponse<MockItem>) => void;
      const fetchOptions = jest.fn().mockImplementation(
        () =>
          new Promise<PaginatedResponse<MockItem>>((resolve) => {
            resolvePromise = resolve;
          })
      );

      render(
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <ComboboxAsync<MockItem>
            {...defaultProps}
            fetchOptions={fetchOptions}
          />
        </QueryClientProvider>
      );

      await user.click(screen.getByRole("combobox"));

      expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument();

      resolvePromise!({
        data: defaultItems,
        total: 3,
        offset: 0,
        limit: 20,
        hasMore: false,
      });

      await waitFor(() => {
        expect(screen.getByText("Opção A")).toBeInTheDocument();
      });
    });

    it("deve exibir emptyText quando não há resultados", async () => {
      const user = userEvent.setup();
      const fetchOptions = createMockFetchOptions([]);

      render(
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <ComboboxAsync<MockItem>
            {...defaultProps}
            fetchOptions={fetchOptions}
            emptyText="Nenhum item encontrado"
          />
        </QueryClientProvider>
      );

      await user.click(screen.getByRole("combobox"));

      await waitFor(() => {
        expect(screen.getByText("Nenhum item encontrado")).toBeInTheDocument();
      });
    });
  });

  describe("Seleção de opções", () => {
    it("deve chamar onValueChange ao selecionar uma opção", async () => {
      const user = userEvent.setup();
      const onValueChange = jest.fn();
      renderComboboxAsync({ onValueChange });

      await user.click(screen.getByRole("combobox"));

      await waitFor(() => {
        expect(screen.getByText("Opção B")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Opção B"));

      expect(onValueChange).toHaveBeenCalledWith({ id: 2, name: "Opção B" });
    });

    it("deve fechar o popover após selecionar uma opção", async () => {
      const user = userEvent.setup();
      const onValueChange = jest.fn();
      renderComboboxAsync({ onValueChange });

      await user.click(screen.getByRole("combobox"));
      await waitFor(() => expect(screen.getByText("Opção A")).toBeInTheDocument());
      await user.click(screen.getByText("Opção A"));

      expect(onValueChange).toHaveBeenCalledWith({ id: 1, name: "Opção A" });
      expect(screen.getByRole("combobox")).toHaveAttribute("aria-expanded", "false");
    });

    it("deve incluir item selecionado nas opções mesmo quando não está na página carregada", async () => {
      const selectedItem = { id: 99, name: "Item Selecionado" };
      const fetchOptions = createMockFetchOptions(defaultItems);

      render(
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <ComboboxAsync<MockItem>
            {...defaultProps}
            fetchOptions={fetchOptions}
            value={selectedItem}
          />
        </QueryClientProvider>
      );

      const user = userEvent.setup();
      await user.click(screen.getByRole("combobox"));

      await waitFor(() => {
        expect(screen.getByRole("option", { name: "Item Selecionado" })).toBeInTheDocument();
        expect(screen.getByRole("option", { name: "Opção A" })).toBeInTheDocument();
      });
    });
  });

  describe("Limpar seleção", () => {
    it("deve chamar onValueChange com null ao clicar no botão de limpar", async () => {
      const user = userEvent.setup();
      const onValueChange = jest.fn();
      renderComboboxAsync({
        value: { id: 1, name: "Opção A" },
        onValueChange,
      });

      const clearButton = screen.getByRole("button", { name: "" });
      await user.click(clearButton);

      expect(onValueChange).toHaveBeenCalledWith(null);
    });
  });

  describe("Estados disabled e readOnly", () => {
    it("deve desabilitar o trigger quando disabled=true", () => {
      renderComboboxAsync({ disabled: true });

      const trigger = screen.getByRole("combobox");
      expect(trigger).toBeDisabled();
    });

    it("deve desabilitar o trigger quando readOnly=true", () => {
      renderComboboxAsync({ readOnly: true });

      const trigger = screen.getByRole("combobox");
      expect(trigger).toBeDisabled();
    });

    it("deve ter aria-readonly quando readOnly=true", () => {
      renderComboboxAsync({ readOnly: true });

      const trigger = screen.getByRole("combobox");
      expect(trigger).toHaveAttribute("aria-readonly", "true");
    });
  });

  describe("Busca", () => {
    it("deve buscar com o termo digitado no campo de busca", async () => {
      const user = userEvent.setup();
      const fetchOptions = createMockFetchOptions(defaultItems);

      render(
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <ComboboxAsync<MockItem>
            {...defaultProps}
            fetchOptions={fetchOptions}
          />
        </QueryClientProvider>
      );

      await user.click(screen.getByRole("combobox"));
      await waitFor(() => expect(fetchOptions).toHaveBeenCalled());

      const searchInput = screen.getByPlaceholderText("Buscar...");
      await user.type(searchInput, "teste");

      await waitFor(() => {
        expect(fetchOptions).toHaveBeenLastCalledWith({
          search: "teste",
          offset: 0,
          limit: 20,
        });
      });
    });
  });

  describe("Paginação", () => {
    it("deve passar pageSize correto para fetchOptions", async () => {
      const fetchOptions = createMockFetchOptions(defaultItems);

      render(
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <ComboboxAsync<MockItem>
            {...defaultProps}
            fetchOptions={fetchOptions}
            pageSize={10}
          />
        </QueryClientProvider>
      );

      const user = userEvent.setup();
      await user.click(screen.getByRole("combobox"));

      await waitFor(() => {
        expect(fetchOptions).toHaveBeenCalledWith({
          search: "",
          offset: 0,
          limit: 10,
        });
      });
    });
  });
});
