import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BuscaReferencias } from "./busca-referencias";
import { buscaReferenciasService } from "./busca-referencias.service";
import { ProjetosReferenciaProvider } from "@/context/projetos-referencias.context";

// Mock do next-auth
jest.mock("next-auth/react", () => ({
  useSession: jest.fn(() => ({
    data: {
      user: {
        casa_legislativa: "Câmara dos Deputados",
      },
    },
    status: "authenticated",
  })),
}));

// Mock do toast
jest.mock("sonner", () => ({
  toast: { error: jest.fn(), success: jest.fn() },
}));

// Mock do serviço de busca
jest.mock("./busca-referencias.service", () => ({
  buscaReferenciasService: {
    buscarReferencias: jest.fn(),
  },
}));

// Mock do CardItem para simplificar o teste
jest.mock("@/components/card-item/card-item", () => ({
  CardItem: ({ title, description }: { title: React.ReactNode; description: string }) => (
    <div data-testid="card-item">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  ),
}));

// Mock do GridLoading
jest.mock("@/components/grid-loading/grid-loading", () => ({
  GridLoading: () => <div data-testid="grid-loading">Carregando...</div>,
}));

// Mock do CardCollapsible
jest.mock("@/components/card-collapsible/card-collapsible", () => ({
  CardCollapsible: ({ content }: { content: React.ReactNode }) => <div>{content}</div>,
}));

// Mock da função scrollToBottom
jest.mock("@/lib/scroll", () => ({
  scrollToBottom: jest.fn(),
}));


// Helper para gerar projetos mock
const generateMockProjetos = (count: number, startIndex: number = 0) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `${startIndex + i + 1}`,
    title: `PL ${startIndex + i + 1}/2024`,
    author: `Autor ${startIndex + i + 1}`,
    house: "Câmara dos Deputados",
    subject: `Assunto ${startIndex + i + 1}`,
    chunk_text: `Texto do projeto ${startIndex + i + 1}`,
  }));
};

// Helper para renderizar o componente com Provider
const renderBuscaReferencias = () => {
  return render(
    <ProjetosReferenciaProvider>
      <BuscaReferencias />
    </ProjetosReferenciaProvider>
  );
};

describe("BuscaReferencias - Testes de paginação", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve mostrar o GridLoading enquanto a API está carregando", async () => {
    // Mock: API retorna uma promise que demora para resolver
    let resolvePromise: (value: unknown) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    
    (buscaReferenciasService.buscarReferencias as jest.Mock).mockReturnValueOnce(promise);

    renderBuscaReferencias();

    // Preenche o campo de busca
    const input = screen.getByPlaceholderText(
      /Escreva aqui uma palavra chave ou o tema da proposição legislativa/i
    );
    await userEvent.type(input, "educação");

    // Clica no botão de busca
    const searchButton = screen.getByRole("button", { name: /Buscar proposições/i });
    await userEvent.click(searchButton);

    // Verifica que o GridLoading está presente enquanto carrega
    await waitFor(() => {
      expect(screen.getByTestId("grid-loading")).toBeInTheDocument();
      expect(screen.getByText("Carregando...")).toBeInTheDocument();
    });

    // Verifica que ainda não há cards renderizados
    expect(screen.queryAllByTestId("card-item")).toHaveLength(0);

    // Resolve a promise com os dados
    const mockProjetos = generateMockProjetos(60);
    resolvePromise!(mockProjetos);

    // Aguarda os resultados aparecerem
    await waitFor(() => {
      expect(screen.getByText(/60 referências encontradas para 'educação'/i)).toBeInTheDocument();
    });

    // Verifica que o GridLoading desapareceu
    expect(screen.queryByTestId("grid-loading")).not.toBeInTheDocument();

    // Verifica que os cards estão presentes
    const cards = screen.getAllByTestId("card-item");
    expect(cards).toHaveLength(12);
  });

  test("deve retornar da API externa uma lista contendo 60 items e renderizar em tela 12 items", async () => {
    // Mock: API retorna 60 projetos
    const mockProjetos = generateMockProjetos(60);
    (buscaReferenciasService.buscarReferencias as jest.Mock).mockResolvedValueOnce(
      mockProjetos
    );

    renderBuscaReferencias();

    // Preenche o campo de busca
    const input = screen.getByPlaceholderText(
      /Escreva aqui uma palavra chave ou o tema da proposição legislativa/i
    );
    await userEvent.type(input, "educação");

    // Clica no botão de busca
    const searchButton = screen.getByRole("button", { name: /Buscar proposições/i });
    await userEvent.click(searchButton);

    // Aguarda a API ser chamada
    await waitFor(() => {
      expect(buscaReferenciasService.buscarReferencias).toHaveBeenCalledWith("educação", 0);
    });

    // Aguarda os resultados aparecerem
    await waitFor(() => {
      expect(screen.getByText(/60 referências encontradas para 'educação'/i)).toBeInTheDocument();
    });

    // Verifica que apenas 12 items foram renderizados
    const cards = screen.getAllByTestId("card-item");
    expect(cards).toHaveLength(12);

    // Verifica que o botão "Ver mais" está presente
    expect(screen.getByRole("button", { name: /Ver mais/i })).toBeInTheDocument();
    
    // Verifica que o botão "Carregar mais resultados" NÃO está presente
    expect(
      screen.queryByRole("button", { name: /Carregar mais resultados/i })
    ).not.toBeInTheDocument();
  });

  test("Ao clicar no botão 'ver mais', deve renderizar 24 itens na tela", async () => {
    // Mock: API retorna 60 projetos
    const mockProjetos = generateMockProjetos(60);
    (buscaReferenciasService.buscarReferencias as jest.Mock).mockResolvedValueOnce(
      mockProjetos
    );

    renderBuscaReferencias();

    // Faz a busca
    const input = screen.getByPlaceholderText(
      /Escreva aqui uma palavra chave ou o tema da proposição legislativa/i
    );
    await userEvent.type(input, "educação");
    
    const searchButton = screen.getByRole("button", { name: /Buscar proposições/i });
    await userEvent.click(searchButton);

    // Aguarda os primeiros 12 items
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(12);
    });

    // Clica no botão "Ver mais"
    const verMaisButton = screen.getByRole("button", { name: /Ver mais/i });
    await userEvent.click(verMaisButton);

    // Verifica que agora são 24 items
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(24);
    });
  });

  test("Ao clicar no botão 'ver mais' novamente, deve renderizar 36 itens na tela", async () => {
    // Mock: API retorna 60 projetos
    const mockProjetos = generateMockProjetos(60);
    (buscaReferenciasService.buscarReferencias as jest.Mock).mockResolvedValueOnce(
      mockProjetos
    );

    renderBuscaReferencias();

    // Faz a busca
    const input = screen.getByPlaceholderText(
      /Escreva aqui uma palavra chave ou o tema da proposição legislativa/i
    );
    await userEvent.type(input, "educação");
    
    const searchButton = screen.getByRole("button", { name: /Buscar proposições/i });
    await userEvent.click(searchButton);

    // Aguarda os primeiros 12 items
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(12);
    });

    // Clica no botão "Ver mais" pela primeira vez
    let verMaisButton = screen.getByRole("button", { name: /Ver mais/i });
    await userEvent.click(verMaisButton);

    // Aguarda 24 items
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(24);
    });

    // Clica no botão "Ver mais" pela segunda vez
    verMaisButton = screen.getByRole("button", { name: /Ver mais/i });
    await userEvent.click(verMaisButton);

    // Verifica que agora são 36 items
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(36);
    });
  });

  test("Depois de estar perto do limite de resultados, deve aparecer o botão 'carregar mais resultados'", async () => {
    // Mock: API retorna 60 projetos
    const mockProjetos = generateMockProjetos(60);
    (buscaReferenciasService.buscarReferencias as jest.Mock).mockResolvedValueOnce(
      mockProjetos
    );

    renderBuscaReferencias();

    // Faz a busca
    const input = screen.getByPlaceholderText(
      /Escreva aqui uma palavra chave ou o tema da proposição legislativa/i
    );
    await userEvent.type(input, "educação");
    
    const searchButton = screen.getByRole("button", { name: /Buscar proposições/i });
    await userEvent.click(searchButton);

    // Aguarda os primeiros 12 items
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(12);
    });

    // Clica "Ver mais" 4 vezes para chegar a 60 items (12 → 24 → 36 → 48 → 60)
    // O botão deve mudar quando estiver perto do fim (>= 57 items)
    for (let i = 0; i < 4; i++) {
      const verMaisButton = screen.getByRole("button", { name: /Ver mais/i });
      await userEvent.click(verMaisButton);
      
      await waitFor(() => {
        const cards = screen.getAllByTestId("card-item");
        expect(cards).toHaveLength((i + 2) * 12);
      });
    }

    // Verifica que agora temos 60 items (todos os resultados)
    const cards = screen.getAllByTestId("card-item");
    expect(cards).toHaveLength(60);

    // Verifica que o botão mudou para "Carregar mais resultados"
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Carregar mais resultados/i })
      ).toBeInTheDocument();
    });
    
    // Verifica que o botão "Ver mais" NÃO está presente
    expect(
      screen.queryByRole("button", { name: /Ver mais/i })
    ).not.toBeInTheDocument();
  });

  test("Ao clicar no botão 'carregar mais resultados', deve retornar da API 60 novos itens e renderizar em tela 72 itens totais", async () => {
    // Mock: Primeira chamada retorna 60 projetos
    const firstBatch = generateMockProjetos(60, 0);
    (buscaReferenciasService.buscarReferencias as jest.Mock).mockResolvedValueOnce(
      firstBatch
    );

    renderBuscaReferencias();

    // Faz a busca inicial
    const input = screen.getByPlaceholderText(
      /Escreva aqui uma palavra chave ou o tema da proposição legislativa/i
    );
    await userEvent.type(input, "educação");
    
    const searchButton = screen.getByRole("button", { name: /Buscar proposições/i });
    await userEvent.click(searchButton);

    // Aguarda os primeiros 12 items
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(12);
    });

    // Clica "Ver mais" 4 vezes para chegar a 60 items (todos os resultados do primeiro batch)
    for (let i = 0; i < 4; i++) {
      const verMaisButton = screen.getByRole("button", { name: /Ver mais/i });
      await userEvent.click(verMaisButton);
      
      await waitFor(() => {
        const cards = screen.getAllByTestId("card-item");
        expect(cards).toHaveLength((i + 2) * 12);
      });
    }

    // Verifica que temos 60 items mostrando
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(60);
    });

    // Aguarda o botão "Carregar mais resultados" aparecer
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Carregar mais resultados/i })
      ).toBeInTheDocument();
    });

    // Mock: Segunda chamada retorna mais 60 projetos (total 120)
    const secondBatch = generateMockProjetos(60, 60);
    (buscaReferenciasService.buscarReferencias as jest.Mock).mockResolvedValueOnce(
      secondBatch
    );

    // Clica no botão "Carregar mais resultados"
    const carregarMaisButton = screen.getByRole("button", {
      name: /Carregar mais resultados/i,
    });
    await userEvent.click(carregarMaisButton);

    // Verifica que a API foi chamada com offset correto (60)
    await waitFor(() => {
      expect(buscaReferenciasService.buscarReferencias).toHaveBeenCalledWith(
        "educação",
        60 // offset é o total de resultados que já temos
      );
    });

    // Verifica que agora temos 120 referências no total
    await waitFor(() => {
      expect(
        screen.getByText(/120 referências encontradas para 'educação'/i)
      ).toBeInTheDocument();
    });

    // Verifica que agora são renderizados 72 items
    // (60 do primeiro batch + 12 do segundo batch)
    await waitFor(() => {
      const cards = screen.getAllByTestId("card-item");
      expect(cards).toHaveLength(72);
    });
  });
});

