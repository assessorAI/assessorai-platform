import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BuscaReferenciasResult } from "./busca-referencias-result";
import { ProjetosReferenciaProvider, useProjetosReferencias } from "@/context/projetos-referencias.context";
import { ProjetoReferencia } from "@/context/projetos-referencias.context";

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

// Mock do next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock do CardItem
jest.mock("@/components/card-item/card-item", () => ({
  CardItem: ({ title, description }: { title: React.ReactNode; description: string }) => (
    <div data-testid="card-item">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  ),
}));

// Mock do CardSelectable usando useController
jest.mock("@/components/card-selectable/card-selectable", () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { useController } = require("react-hook-form");
  
  return {
    CardSelectable: ({ 
      id, 
      title, 
      description, 
      control 
    }: { 
      id: string; 
      title: string; 
      description: string; 
      control: unknown;
    }) => {
      const { field } = useController({
        name: "options",
        control,
        defaultValue: [],
      });

      const isChecked = field.value.includes(id);

      const handleChange = () => {
        if (isChecked) {
          field.onChange(field.value.filter((optId: string) => optId !== id));
        } else {
          field.onChange([...field.value, id]);
        }
      };

      return (
        <div data-testid={`card-selectable-${id}`}>
          <input
            type="checkbox"
            checked={isChecked}
            onChange={handleChange}
            data-testid={`checkbox-${id}`}
          />
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
      );
    },
  };
});

// Mock do BuscaReferenciasResultDetail
jest.mock("./busca-referencias-result-detail", () => ({
  BuscaReferenciasResultDetail: () => <div>Detail</div>,
}));

// Mock da função scrollToBottom
jest.mock("@/lib/scroll", () => ({
  scrollToBottom: jest.fn(),
}));

// Helper para gerar projetos mock
const generateMockProjetos = (count: number, startIndex: number = 0): ProjetoReferencia[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `${startIndex + i + 1}`,
    title: `PL ${startIndex + i + 1}/2024`,
    author: `Autor ${startIndex + i + 1}`,
    house: "Câmara dos Deputados",
    subject: `Assunto ${startIndex + i + 1}`,
    chunk_text: `Texto do projeto ${startIndex + i + 1}`,
    url: `https://example.com/projeto/${startIndex + i + 1}`,
  }));
};

// Helper para renderizar o componente com Provider
const renderBuscaReferenciasResult = (
  results: ProjetoReferencia[],
  searchedTerm: string = "educação",
  onReachEnd: jest.Mock = jest.fn(),
  isLoading: boolean = false
) => {
  return render(
    <ProjetosReferenciaProvider>
      <BuscaReferenciasResult
        results={results}
        searchedTerm={searchedTerm}
        onReachEnd={onReachEnd}
        isLoading={isLoading}
      />
    </ProjetosReferenciaProvider>
  );
};

describe("BuscaReferenciasResult - Testes de seleção de referências", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve aparecer os cards para selecionar quando o usuário clicar em 'Selecionar referências'", async () => {
    const mockResults = generateMockProjetos(12);
    
    renderBuscaReferenciasResult(mockResults);

    // Verifica que inicialmente os CardItem estão presentes
    const cardItems = screen.getAllByTestId("card-item");
    expect(cardItems).toHaveLength(12);

    // Verifica que os CardSelectable não estão presentes
    expect(screen.queryByTestId("card-selectable-1")).not.toBeInTheDocument();

    // Clica no botão "Selecionar referências"
    const selectButton = screen.getByRole("button", { name: /Selecionar referências/i });
    await userEvent.click(selectButton);

    // Verifica que agora os CardSelectable aparecem
    await waitFor(() => {
      expect(screen.getByTestId("card-selectable-1")).toBeInTheDocument();
      expect(screen.getByTestId("card-selectable-2")).toBeInTheDocument();
      expect(screen.getByTestId("card-selectable-3")).toBeInTheDocument();
    });

    // Verifica que o botão "Cancelar" está presente
    expect(screen.getByRole("button", { name: /Cancelar/i })).toBeInTheDocument();

    // Verifica que o botão "Anexar à criação de PL" está presente
    expect(screen.getByRole("button", { name: /Anexar à criação de PL/i })).toBeInTheDocument();

    // Verifica que os CardItem não estão mais presentes
    expect(screen.queryAllByTestId("card-item")).toHaveLength(0);
  });

  test("deve desaparecer os cards para selecionar e aparecer a lista de itens quando o usuário clicar em 'cancelar'", async () => {
    const mockResults = generateMockProjetos(12);
    
    renderBuscaReferenciasResult(mockResults);

    // Clica em "Selecionar referências"
    const selectButton = screen.getByRole("button", { name: /Selecionar referências/i });
    await userEvent.click(selectButton);

    // Verifica que os CardSelectable estão presentes
    await waitFor(() => {
      expect(screen.getByTestId("card-selectable-1")).toBeInTheDocument();
    });

    // Clica no botão "Cancelar"
    const cancelButton = screen.getByRole("button", { name: /Cancelar/i });
    await userEvent.click(cancelButton);

    // Verifica que os CardSelectable desapareceram
    await waitFor(() => {
      expect(screen.queryByTestId("card-selectable-1")).not.toBeInTheDocument();
    });

    // Verifica que os CardItem voltaram a aparecer
    const cardItems = screen.getAllByTestId("card-item");
    expect(cardItems).toHaveLength(12);

    // Verifica que o botão "Selecionar referências" voltou a aparecer
    expect(screen.getByRole("button", { name: /Selecionar referências/i })).toBeInTheDocument();
  });

  test("Ao selecionar 3 itens e clicar em 'anexar à criação de PL', deve adicionar os itens selecionados no contexto e aparecer o conteúdo de referencesArea", async () => {
    const mockResults = generateMockProjetos(12);
    
    // Componente wrapper para poder acessar o contexto
    const TestWrapper = () => {
      const { selectedProjetos } = useProjetosReferencias();
      
      return (
        <>
          <BuscaReferenciasResult
            results={mockResults}
            searchedTerm="educação"
            onReachEnd={jest.fn()}
            isLoading={false}
          />
          {/* Div para testar o contexto */}
          <div data-testid="selected-count">{selectedProjetos.length}</div>
        </>
      );
    };

    render(
      <ProjetosReferenciaProvider>
        <TestWrapper />
      </ProjetosReferenciaProvider>
    );

    // Clica em "Selecionar referências"
    const selectButton = screen.getByRole("button", { name: /Selecionar referências/i });
    await userEvent.click(selectButton);

    // Aguarda os CardSelectable aparecerem
    await waitFor(() => {
      expect(screen.getByTestId("card-selectable-1")).toBeInTheDocument();
    });

    // Seleciona 3 itens (IDs: 1, 2, 3)
    const checkbox1 = screen.getByTestId("checkbox-1");
    const checkbox2 = screen.getByTestId("checkbox-2");
    const checkbox3 = screen.getByTestId("checkbox-3");

    await userEvent.click(checkbox1);
    await userEvent.click(checkbox2);
    await userEvent.click(checkbox3);

    // Verifica que os checkboxes estão marcados
    expect(checkbox1).toBeChecked();
    expect(checkbox2).toBeChecked();
    expect(checkbox3).toBeChecked();

    // Clica no botão "Anexar à criação de PL"
    const attachButton = screen.getByRole("button", { name: /Anexar à criação de PL/i });
    await userEvent.click(attachButton);

    // Verifica que o contexto foi atualizado
    await waitFor(() => {
      const selectedCount = screen.getByTestId("selected-count");
      expect(selectedCount).toHaveTextContent("3");
    });

    // Verifica que a área de referências anexadas aparece
    await waitFor(() => {
      expect(screen.getByText("Referências anexadas")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/As proposições selecionadas foram anexadas à área de Criação de Projeto de Lei/i)
    ).toBeInTheDocument();

    // Verifica que o botão de navegação está presente
    expect(
      screen.getByRole("button", { name: /Ir para Criação de Projeto de Lei/i })
    ).toBeInTheDocument();

    // Verifica que os CardSelectable desapareceram
    expect(screen.queryByTestId("card-selectable-1")).not.toBeInTheDocument();
  });

  test("deve navegar para a página de criar PL ao clicar no botão 'Ir para Criação de Projeto de Lei'", async () => {
    const mockResults = generateMockProjetos(12);
    
    render(
      <ProjetosReferenciaProvider>
        <BuscaReferenciasResult
          results={mockResults}
          searchedTerm="educação"
          onReachEnd={jest.fn()}
          isLoading={false}
        />
      </ProjetosReferenciaProvider>
    );

    // Clica em "Selecionar referências"
    const selectButton = screen.getByRole("button", { name: /Selecionar referências/i });
    await userEvent.click(selectButton);

    // Seleciona 1 item
    await waitFor(() => {
      expect(screen.getByTestId("checkbox-1")).toBeInTheDocument();
    });
    
    const checkbox1 = screen.getByTestId("checkbox-1");
    await userEvent.click(checkbox1);

    // Anexa à criação de PL
    const attachButton = screen.getByRole("button", { name: /Anexar à criação de PL/i });
    await userEvent.click(attachButton);

    // Aguarda a área de referências aparecer
    await waitFor(() => {
      expect(screen.getByText("Referências anexadas")).toBeInTheDocument();
    });

    // Clica no botão de navegação
    const navigateButton = screen.getByRole("button", {
      name: /Ir para Criação de Projeto de Lei/i,
    });
    await userEvent.click(navigateButton);

    // Verifica que o router.push foi chamado com a rota correta
    expect(mockPush).toHaveBeenCalledWith("/producao-legislativa/criar-pl");
  });

  test("o botão 'Anexar à criação de PL' deve estar desabilitado quando nenhum item está selecionado", async () => {
    const mockResults = generateMockProjetos(12);
    
    renderBuscaReferenciasResult(mockResults);

    // Clica em "Selecionar referências"
    const selectButton = screen.getByRole("button", { name: /Selecionar referências/i });
    await userEvent.click(selectButton);

    // Aguarda os CardSelectable aparecerem
    await waitFor(() => {
      expect(screen.getByTestId("card-selectable-1")).toBeInTheDocument();
    });

    // Verifica que o botão "Anexar à criação de PL" está desabilitado
    const attachButton = screen.getByRole("button", { name: /Anexar à criação de PL/i });
    expect(attachButton).toBeDisabled();

    // Seleciona 1 item
    const checkbox1 = screen.getByTestId("checkbox-1");
    await userEvent.click(checkbox1);

    // Aguarda o botão ficar habilitado
    await waitFor(() => {
      expect(attachButton).not.toBeDisabled();
    });

    // Desmarca o item
    await userEvent.click(checkbox1);

    // Verifica que o botão volta a ficar desabilitado
    await waitFor(() => {
      expect(attachButton).toBeDisabled();
    });
  });

  test("deve RESETAR a seleção de itens quando cancela e volta a selecionar referências", async () => {
    const mockResults = generateMockProjetos(12);
    
    renderBuscaReferenciasResult(mockResults);

    // Clica em "Selecionar referências"
    let selectButton = screen.getByRole("button", { name: /Selecionar referências/i });
    await userEvent.click(selectButton);

    // Seleciona 2 itens
    await waitFor(() => {
      expect(screen.getByTestId("checkbox-1")).toBeInTheDocument();
    });
    
    const checkbox1 = screen.getByTestId("checkbox-1");
    const checkbox2 = screen.getByTestId("checkbox-2");
    const checkbox3 = screen.getByTestId("checkbox-3");
    
    await userEvent.click(checkbox1);
    await userEvent.click(checkbox2);

    // Verifica que estão marcados
    expect(checkbox1).toBeChecked();
    expect(checkbox2).toBeChecked();
    expect(checkbox3).not.toBeChecked(); // Este não foi marcado

    // Verifica que o botão "Anexar à criação de PL" está habilitado (2 itens selecionados)
    const attachButton = screen.getByRole("button", { name: /Anexar à criação de PL/i });
    expect(attachButton).not.toBeDisabled();

    // Cancela
    const cancelButton = screen.getByRole("button", { name: /Cancelar/i });
    await userEvent.click(cancelButton);

    // Volta a clicar em "Selecionar referências"
    await waitFor(() => {
      selectButton = screen.getByRole("button", { name: /Selecionar referências/i });
    });
    await userEvent.click(selectButton);

    // Verifica que os checkboxes foram RESETADOS (nenhum está marcado)
    await waitFor(() => {
      const newCheckbox1 = screen.getByTestId("checkbox-1");
      const newCheckbox2 = screen.getByTestId("checkbox-2");
      const newCheckbox3 = screen.getByTestId("checkbox-3");
      
      expect(newCheckbox1).not.toBeChecked();
      expect(newCheckbox2).not.toBeChecked();
      expect(newCheckbox3).not.toBeChecked();
    });

    // Verifica que o botão "Anexar à criação de PL" está DESABILITADO (nenhum item selecionado)
    const newAttachButton = screen.getByRole("button", { name: /Anexar à criação de PL/i });
    expect(newAttachButton).toBeDisabled();

    // Verifica que podemos selecionar novamente (não é falso positivo)
    const newCheckbox1 = screen.getByTestId("checkbox-1");
    await userEvent.click(newCheckbox1);

    // Agora deve estar marcado
    await waitFor(() => {
      expect(newCheckbox1).toBeChecked();
    });

    // E o botão deve ficar habilitado novamente
    await waitFor(() => {
      expect(newAttachButton).not.toBeDisabled();
    });
  });
});

describe("BuscaReferenciasResult - Testes de loading", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve ocultar o botão 'Ver mais/Carregar mais' quando isLoading é true", async () => {
    const mockResults = generateMockProjetos(60);
    
    renderBuscaReferenciasResult(mockResults, "educação", jest.fn(), true);

    // Verifica que os cards estão visíveis
    const cards = screen.getAllByTestId("card-item");
    expect(cards).toHaveLength(12);

    // Verifica que o texto de quantidade está presente
    expect(screen.getByText(/60 referências encontradas para 'educação'/i)).toBeInTheDocument();

    // Verifica que o botão "Ver mais" NÃO está presente
    expect(screen.queryByRole("button", { name: /Ver mais/i })).not.toBeInTheDocument();

    // Verifica que o botão "Carregar mais resultados" também NÃO está presente
    expect(screen.queryByRole("button", { name: /Carregar mais resultados/i })).not.toBeInTheDocument();
  });

  test("deve manter os cards visíveis durante loading", async () => {
    const mockResults = generateMockProjetos(24);
    
    const { rerender } = render(
      <ProjetosReferenciaProvider>
        <BuscaReferenciasResult
          results={mockResults}
          searchedTerm="educação"
          onReachEnd={jest.fn()}
          isLoading={false}
        />
      </ProjetosReferenciaProvider>
    );

    // Verifica que 12 cards estão visíveis
    let cards = screen.getAllByTestId("card-item");
    expect(cards).toHaveLength(12);

    // Muda para loading=true
    rerender(
      <ProjetosReferenciaProvider>
        <BuscaReferenciasResult
          results={mockResults}
          searchedTerm="educação"
          onReachEnd={jest.fn()}
          isLoading={true}
        />
      </ProjetosReferenciaProvider>
    );

    // Verifica que os cards continuam visíveis
    cards = screen.getAllByTestId("card-item");
    expect(cards).toHaveLength(12);

    // Mas o botão desapareceu
    expect(screen.queryByRole("button", { name: /Ver mais/i })).not.toBeInTheDocument();
  });

  test("deve permitir visualizar os cards enquanto carrega mais resultados", async () => {
    const mockResults = generateMockProjetos(60);
    
    renderBuscaReferenciasResult(mockResults, "educação", jest.fn(), true);

    // Verifica que pode visualizar todos os 12 cards iniciais
    const cards = screen.getAllByTestId("card-item");
    expect(cards).toHaveLength(12);

    // Verifica que cada card tem seu conteúdo correto
    expect(screen.getByText("PL 1/2024")).toBeInTheDocument();
    expect(screen.getByText("Assunto 1")).toBeInTheDocument();
    expect(screen.getByText("PL 12/2024")).toBeInTheDocument();
    expect(screen.getByText("Assunto 12")).toBeInTheDocument();

    // Verifica que o texto de quantidade está presente
    expect(screen.getByText(/60 referências encontradas/i)).toBeInTheDocument();

    // Confirma que apenas o botão de paginação foi ocultado (não todo o componente)
    expect(screen.queryByRole("button", { name: /Ver mais/i })).not.toBeInTheDocument();
  });
});

describe("BuscaReferenciasResult - Testes com projetos no contexto", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("não deve mostrar o texto 'X referências encontradas' quando há projetos selecionados", async () => {
    const mockResults = generateMockProjetos(60);
    
    // Componente wrapper com projetos já selecionados
    const TestWrapperWithSelectedProjects = () => {
      const { setSelectedProjetos } = useProjetosReferencias();
      
      // Simula que já há projetos selecionados
      React.useEffect(() => {
        setSelectedProjetos([
          mockResults[0],
          mockResults[1],
          mockResults[2],
        ]);
      }, [setSelectedProjetos]);
      
      return (
        <BuscaReferenciasResult
          results={mockResults}
          searchedTerm="educação"
          onReachEnd={jest.fn()}
          isLoading={false}
        />
      );
    };

    render(
      <ProjetosReferenciaProvider>
        <TestWrapperWithSelectedProjects />
      </ProjetosReferenciaProvider>
    );

    // Aguarda o efeito executar
    await waitFor(() => {
      // Verifica que o texto de quantidade NÃO está presente
      expect(screen.queryByText(/referências encontradas/i)).not.toBeInTheDocument();
    });

    // Verifica que os cards ainda são exibidos
    const cards = screen.getAllByTestId("card-item");
    expect(cards.length).toBeGreaterThan(0);
  });

  test("não deve mostrar o botão 'Ver mais' quando há projetos selecionados", async () => {
    const mockResults = generateMockProjetos(60);
    
    const TestWrapperWithSelectedProjects = () => {
      const { setSelectedProjetos } = useProjetosReferencias();
      
      React.useEffect(() => {
        setSelectedProjetos([mockResults[0]]);
      }, [setSelectedProjetos]);
      
      return (
        <BuscaReferenciasResult
          results={mockResults}
          searchedTerm="educação"
          onReachEnd={jest.fn()}
          isLoading={false}
        />
      );
    };

    render(
      <ProjetosReferenciaProvider>
        <TestWrapperWithSelectedProjects />
      </ProjetosReferenciaProvider>
    );

    // Aguarda o efeito executar
    await waitFor(() => {
      // Verifica que o botão "Ver mais" NÃO está presente
      expect(screen.queryByRole("button", { name: /Ver mais/i })).not.toBeInTheDocument();
    });

    // Verifica que o botão "Carregar mais resultados" também NÃO está presente
    expect(screen.queryByRole("button", { name: /Carregar mais resultados/i })).not.toBeInTheDocument();
  });

});

describe("BuscaReferenciasResult - Testes de estado vazio", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve mostrar uma mensagem quando não foram encontrados resultados para a busca", async () => {
    const emptyResults: ProjetoReferencia[] = [];
    
    renderBuscaReferenciasResult(emptyResults, "xyzabc123", jest.fn(), false);
  
    // Verifica que nenhum card é renderizado
    expect(screen.queryAllByTestId("card-item")).toHaveLength(0);
  
    // Verifica a mensagem de sem resultados
    expect(screen.getByText(/Filtro sem resultados./i)).toBeInTheDocument();
    
    // Verifica que não há texto de quantidade
    expect(screen.queryByText(/referências encontradas/i)).not.toBeInTheDocument();
  });

  test("não deve mostrar botão 'Selecionar referências' quando não há resultados", async () => {
    const emptyResults: ProjetoReferencia[] = [];
    
    renderBuscaReferenciasResult(emptyResults, "termo inexistente", jest.fn(), false);

    // Verifica que o botão "Selecionar referências" NÃO está presente
    expect(screen.queryByRole("button", { name: /Selecionar referências/i })).not.toBeInTheDocument();
  });

  test("não deve mostrar o texto de quantidade quando não há resultados", async () => {
    const emptyResults: ProjetoReferencia[] = [];
    
    renderBuscaReferenciasResult(emptyResults, "busca sem resultado", jest.fn(), false);

    // Verifica que o texto de quantidade NÃO está presente
    expect(screen.queryByText(/referências encontradas/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/0 referências/i)).not.toBeInTheDocument();
  });

  test("não deve mostrar botão 'Ver mais' quando não há resultados", async () => {
    const emptyResults: ProjetoReferencia[] = [];
    
    renderBuscaReferenciasResult(emptyResults, "nada aqui", jest.fn(), false);

    // Verifica que o botão "Ver mais" NÃO está presente
    expect(screen.queryByRole("button", { name: /Ver mais/i })).not.toBeInTheDocument();
  });
});

describe("BuscaReferenciasResult - Testes de integração avançada", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("deve adicionar projetos ao contexto sem duplicar IDs", async () => {
    const mockResults = generateMockProjetos(12);
    
    const TestWrapper = () => {
      const { selectedProjetos, setSelectedProjetos } = useProjetosReferencias();
      
      // Simula que já há 1 projeto selecionado (ID: 1)
      React.useEffect(() => {
        if (selectedProjetos.length === 0) {
          setSelectedProjetos([mockResults[0]]);
        }
      // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);
      
      return (
        <>
          <BuscaReferenciasResult
            results={mockResults}
            searchedTerm="educação"
            onReachEnd={jest.fn()}
            isLoading={false}
          />
          <div data-testid="selected-ids">
            {selectedProjetos.map(p => p.id).join(",")}
          </div>
          <div data-testid="selected-count">{selectedProjetos.length}</div>
        </>
      );
    };

    render(
      <ProjetosReferenciaProvider>
        <TestWrapper />
      </ProjetosReferenciaProvider>
    );

    // Aguarda o projeto inicial ser adicionado
    await waitFor(() => {
      expect(screen.getByTestId("selected-count")).toHaveTextContent("1");
      expect(screen.getByTestId("selected-ids")).toHaveTextContent("1");
    });

    // Verifica que a lista de cards está visível (não mostra área de referências quando tem apenas 1)
    const cards = screen.queryAllByTestId("card-item");
    expect(cards.length).toBeGreaterThan(0);

    // Verifica que não há IDs duplicados
    const selectedIds = screen.getByTestId("selected-ids").textContent;
    const idsArray = selectedIds?.split(",").filter(id => id) || [];
    const uniqueIds = new Set(idsArray);
    
    // Verifica que não há duplicatas
    expect(idsArray.length).toBe(uniqueIds.size);
    expect(idsArray.length).toBe(1); // Deve ter apenas 1 ID
  });
});

