import { renderHook, act } from "@testing-library/react";
import { useHandleVerMais } from "./useHandleVerMais";
import { ProjetoReferencia } from "@/context/projetos-referencias.context";
import { SelectedHouse } from "./busca-referencias-result.types";

// Helper para gerar projetos mock
const generateMockProjetos = (
  count: number,
  house: string,
  startIndex: number = 0
): ProjetoReferencia[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `${startIndex + i + 1}`,
    title: `PL ${startIndex + i + 1}/2024`,
    author: house === "Câmara dos Deputados" ? `Deputado ${i + 1}` : `Senador ${i + 1}`,
    house: house,
    subject: `Assunto ${startIndex + i + 1}`,
    chunk_text: `Texto do projeto ${startIndex + i + 1}`,
  }));
};

describe("useHandleVerMais - Testes do hook isoladamente", () => {
  const MY_HOUSE = "Câmara dos Deputados";

  describe("Paginação básica", () => {
    test("deve iniciar mostrando 12 itens", () => {
      const mockResults = generateMockProjetos(60, MY_HOUSE);
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.ALL, MY_HOUSE)
      );

      // Verifica que inicia mostrando 12 items
      expect(result.current.resultsToShow).toHaveLength(12);
      expect(result.current.totalResults).toBe(60);
    });

    test("deve mostrar 24 itens após clicar em 'Ver mais' uma vez", () => {
      const mockResults = generateMockProjetos(60, MY_HOUSE);
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.ALL, MY_HOUSE)
      );

      // Estado inicial: 12 items
      expect(result.current.resultsToShow).toHaveLength(12);

      // Clica em "Ver mais"
      act(() => {
        result.current.next();
      });

      // Agora deve mostrar 24 items
      expect(result.current.resultsToShow).toHaveLength(24);
    });

    test("deve mostrar 36 itens após clicar em 'Ver mais' duas vezes", () => {
      const mockResults = generateMockProjetos(60, MY_HOUSE);
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.ALL, MY_HOUSE)
      );

      // Clica "Ver mais" duas vezes
      act(() => {
        result.current.next();
        result.current.next();
      });

      // Deve mostrar 36 items
      expect(result.current.resultsToShow).toHaveLength(36);
    });

    test("deve mostrar todos os 60 itens após clicar em 'Ver mais' 4 vezes", () => {
      const mockResults = generateMockProjetos(60, MY_HOUSE);
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.ALL, MY_HOUSE)
      );

      // Clica "Ver mais" 4 vezes (12 → 24 → 36 → 48 → 60)
      act(() => {
        result.current.next();
        result.current.next();
        result.current.next();
        result.current.next();
      });

      // Deve mostrar todos os 60 items
      expect(result.current.resultsToShow).toHaveLength(60);
      expect(result.current.totalResults).toBe(60);
    });
  });

  describe("Lógica de shouldFetchMore", () => {
    test("shouldFetchMore deve ser false quando ainda tem muitos resultados para mostrar", () => {
      const mockResults = generateMockProjetos(60, MY_HOUSE);
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.ALL, MY_HOUSE)
      );

      // No início (mostrando 12 de 60), shouldFetchMore deve ser false
      expect(result.current.shouldFetchMore).toBe(false);
    });

    test("shouldFetchMore deve ser true quando está mostrando todos os resultados", () => {
      const mockResults = generateMockProjetos(60, MY_HOUSE);
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.ALL, MY_HOUSE)
      );

      // Clica "Ver mais" 4 vezes para mostrar todos os 60 items
      act(() => {
        result.current.next();
        result.current.next();
        result.current.next();
        result.current.next();
      });

      // Agora shouldFetchMore deve ser true (mostrando 60 de 60)
      expect(result.current.shouldFetchMore).toBe(true);
    });

    test("shouldFetchMore deve ser true quando está perto do fim (dentro de 3 itens)", () => {
      const mockResults = generateMockProjetos(60, MY_HOUSE);
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.ALL, MY_HOUSE)
      );

      // Clica "Ver mais" 3 vezes para mostrar 48 items
      act(() => {
        result.current.next();
        result.current.next();
        result.current.next();
      });

      // 48 items mostrados, 60 total
      // filteredResults.length (60) - itemsPerPage (48) = 12
      // Como 12 > 3, shouldFetchMore ainda é false
      expect(result.current.shouldFetchMore).toBe(false);

      // Clica mais uma vez para mostrar 60 items
      act(() => {
        result.current.next();
      });

      // Agora shouldFetchMore deve ser true
      expect(result.current.shouldFetchMore).toBe(true);
    });
  });

  describe("Filtro por casa legislativa - Todas as casas", () => {
    test("quando selecionado 'Todas as casas', deve mostrar todos os projetos", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.ALL, MY_HOUSE)
      );

      // Deve mostrar 12 items inicialmente
      expect(result.current.resultsToShow).toHaveLength(12);
      expect(result.current.totalResults).toBe(60);
      
      // Clica "Ver mais" 3 vezes para mostrar 48 items
      // Assim garantimos que teremos tanto da Câmara quanto do Senado
      act(() => {
        result.current.next();
        result.current.next();
        result.current.next();
      });

      // Agora deve ter 48 items
      expect(result.current.resultsToShow).toHaveLength(48);
      
      // Verifica que tem projetos de ambas as casas
      const houses = result.current.resultsToShow.map(p => p.house);
      expect(houses).toContain("Câmara dos Deputados");
      expect(houses).toContain("Senado Federal");
      
      // Conta quantos de cada casa
      const camaraCount = houses.filter(h => h === "Câmara dos Deputados").length;
      const senadoCount = houses.filter(h => h === "Senado Federal").length;
      
      // Deve ter 30 da Câmara e 18 do Senado (total 48)
      expect(camaraCount).toBe(30);
      expect(senadoCount).toBe(18);
    });
  });

  describe("Filtro por casa legislativa - Minha Casa", () => {
    test("quando selecionado 'Minha Casa legislativa', deve mostrar apenas projetos da Câmara dos Deputados", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.MY_HOUSE, MY_HOUSE)
      );

      // Deve mostrar 12 items, todos da Câmara
      expect(result.current.resultsToShow).toHaveLength(12);
      
      // Verifica que TODOS são da Câmara dos Deputados
      result.current.resultsToShow.forEach(projeto => {
        expect(projeto.house).toBe("Câmara dos Deputados");
        expect(projeto.author).toContain("Deputado");
      });
    });

    test("quando filtrado por 'Minha Casa', o total deve refletir apenas projetos da minha casa", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.MY_HOUSE, MY_HOUSE)
      );

      // Total de resultados originais é 60, mas total filtrado é 30
      expect(result.current.totalResults).toBe(60);
      
      // Clica "Ver mais" para ver mais projetos filtrados
      act(() => {
        result.current.next();
      });

      // Agora mostra 24 items, todos da Câmara
      expect(result.current.resultsToShow).toHaveLength(24);
      result.current.resultsToShow.forEach(projeto => {
        expect(projeto.house).toBe("Câmara dos Deputados");
      });
    });

    test("deve poder mostrar todos os 30 projetos da Câmara quando filtrado", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.MY_HOUSE, MY_HOUSE)
      );

      // Clica "Ver mais" 2 vezes para mostrar 36 items
      // Mas como só tem 30 da Câmara, deve mostrar apenas 30
      act(() => {
        result.current.next();
        result.current.next();
      });

      // Deve mostrar exatamente 30 items (todos da Câmara)
      expect(result.current.resultsToShow).toHaveLength(30);
      result.current.resultsToShow.forEach(projeto => {
        expect(projeto.house).toBe("Câmara dos Deputados");
      });
    });
  });

  describe("Filtro por casa legislativa - Outras Casas", () => {
    test("quando selecionado 'Outras casas', deve mostrar apenas projetos do Senado", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.OTHER, MY_HOUSE)
      );

      // Deve mostrar 12 items, todos do Senado
      expect(result.current.resultsToShow).toHaveLength(12);
      
      // Verifica que TODOS são do Senado Federal (outras casas)
      result.current.resultsToShow.forEach(projeto => {
        expect(projeto.house).toBe("Senado Federal");
        expect(projeto.author).toContain("Senador");
      });
    });

    test("quando filtrado por 'Outras casas', deve excluir a Câmara dos Deputados", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      const { result } = renderHook(() =>
        useHandleVerMais(mockResults, SelectedHouse.OTHER, MY_HOUSE)
      );

      // Clica "Ver mais" para ver mais projetos
      act(() => {
        result.current.next();
      });

      // Agora mostra 24 items, todos do Senado
      expect(result.current.resultsToShow).toHaveLength(24);
      result.current.resultsToShow.forEach(projeto => {
        expect(projeto.house).not.toBe("Câmara dos Deputados");
        expect(projeto.house).toBe("Senado Federal");
      });
    });
  });

  describe("Mudança de filtro em tempo real", () => {
    test("deve atualizar os resultados quando o filtro muda de 'Todas' para 'Minha Casa'", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      // Inicia com "Todas as casas"
      const { result, rerender } = renderHook(
        ({ termToFilter }) => useHandleVerMais(mockResults, termToFilter, MY_HOUSE),
        { initialProps: { termToFilter: SelectedHouse.ALL } }
      );

      // Estado inicial: 12 items misturados
      expect(result.current.resultsToShow).toHaveLength(12);
      
      // Muda para "Minha Casa"
      rerender({ termToFilter: SelectedHouse.MY_HOUSE });

      // Agora deve mostrar apenas projetos da Câmara
      expect(result.current.resultsToShow).toHaveLength(12);
      result.current.resultsToShow.forEach(projeto => {
        expect(projeto.house).toBe("Câmara dos Deputados");
      });
    });

    test("deve atualizar os resultados quando o filtro muda de 'Minha Casa' para 'Outras casas'", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      // Inicia com "Minha Casa"
      const { result, rerender } = renderHook(
        ({ termToFilter }) => useHandleVerMais(mockResults, termToFilter, MY_HOUSE),
        { initialProps: { termToFilter: SelectedHouse.MY_HOUSE } }
      );

      // Todos devem ser da Câmara
      result.current.resultsToShow.forEach(projeto => {
        expect(projeto.house).toBe("Câmara dos Deputados");
      });
      
      // Muda para "Outras casas"
      rerender({ termToFilter: SelectedHouse.OTHER });

      // Agora todos devem ser do Senado
      expect(result.current.resultsToShow).toHaveLength(12);
      result.current.resultsToShow.forEach(projeto => {
        expect(projeto.house).toBe("Senado Federal");
      });
    });

    test("deve voltar a mostrar todos quando muda de filtro específico para 'Todas'", () => {
      const mockResults = [
        ...generateMockProjetos(30, "Câmara dos Deputados", 0),
        ...generateMockProjetos(30, "Senado Federal", 30),
      ];
      
      // Inicia com "Minha Casa"
      const { result, rerender } = renderHook(
        ({ termToFilter }) => useHandleVerMais(mockResults, termToFilter, MY_HOUSE),
        { initialProps: { termToFilter: SelectedHouse.MY_HOUSE } }
      );

      // Clica "Ver mais" uma vez
      act(() => {
        result.current.next();
      });

      // 24 items da Câmara
      expect(result.current.resultsToShow).toHaveLength(24);
      
      // Muda para "Todas as casas"
      rerender({ termToFilter: SelectedHouse.ALL });

      // Mantém o itemsPerPage (24), então mostra 24 items misturados
      expect(result.current.resultsToShow).toHaveLength(24);
      
      // Como temos 30 da Câmara primeiro, os primeiros 24 serão todos da Câmara
      // Vamos clicar "Ver mais" para ver os do Senado também
      act(() => {
        result.current.next();
      });

      // Agora mostra 36 items
      expect(result.current.resultsToShow).toHaveLength(36);
      
      const houses = result.current.resultsToShow.map(p => p.house);
      expect(houses).toContain("Câmara dos Deputados");
      expect(houses).toContain("Senado Federal");
      
      // Conta quantos de cada
      const camaraCount = houses.filter(h => h === "Câmara dos Deputados").length;
      const senadoCount = houses.filter(h => h === "Senado Federal").length;
      
      // Deve ter 30 da Câmara e 6 do Senado (total 36)
      expect(camaraCount).toBe(30);
      expect(senadoCount).toBe(6);
    });
  });

  describe("Adição de novos resultados (loadMore)", () => {
    test("deve adicionar novos resultados quando a API retorna mais dados", () => {
      const firstBatch = generateMockProjetos(60, MY_HOUSE, 0);
      
      const { result, rerender } = renderHook(
        ({ results }) => useHandleVerMais(results, SelectedHouse.ALL, MY_HOUSE),
        { initialProps: { results: firstBatch } }
      );

      // Estado inicial: 60 resultados, mostrando 12
      expect(result.current.totalResults).toBe(60);
      expect(result.current.resultsToShow).toHaveLength(12);

      // Simula carregamento de mais 60 resultados
      const secondBatch = generateMockProjetos(60, MY_HOUSE, 60);

      rerender({ results: secondBatch });

      // Agora deve ter 120 resultados no total
      // E deve estar mostrando 72 items (60 + 12 do incremento automático)
      expect(result.current.totalResults).toBe(120);
      expect(result.current.resultsToShow).toHaveLength(72);
    });

    test("deve incrementar itemsPerPage automaticamente quando novos resultados chegam", () => {
      const firstBatch = generateMockProjetos(60, MY_HOUSE, 0);
      
      const { result, rerender } = renderHook(
        ({ results }) => useHandleVerMais(results, SelectedHouse.ALL, MY_HOUSE),
        { initialProps: { results: firstBatch } }
      );

      // Clica "Ver mais" 4 vezes para mostrar todos os 60
      act(() => {
        result.current.next();
        result.current.next();
        result.current.next();
        result.current.next();
      });

      expect(result.current.resultsToShow).toHaveLength(60);

      // Simula chegada de novos resultados
      const secondBatch = generateMockProjetos(60, MY_HOUSE, 60);
      rerender({ results: secondBatch });

      // O hook automaticamente adiciona +12 ao itemsPerPage
      // Então deve mostrar 72 items (60 anteriores + 12 novos)
      expect(result.current.resultsToShow).toHaveLength(72);
      expect(result.current.totalResults).toBe(120);
    });
  });
});

