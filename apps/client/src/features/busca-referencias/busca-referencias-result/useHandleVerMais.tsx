import { ProjetoReferencia } from "@/context/projetos-referencias.context";
import { useEffect, useState, useMemo } from "react";
import { SelectedHouse } from "./busca-referencias-result.types";

export const useHandleVerMais = (
  results: ProjetoReferencia[],
  termToFilter: string,
  myHouse: string
) => {
  const [originalResults, setOriginalResults] = useState<ProjetoReferencia[]>(
    []
  );
  const multipleItemsPerPage = 12;
  const [itemsPerPage, setItemsPerPage] = useState(multipleItemsPerPage);

  useEffect(() => {
    if (results && results.length > 0) {
      const previousCount = originalResults.length;
      const newResults = [...originalResults, ...results];
      setOriginalResults(newResults);

      if (previousCount > 0) {
        setItemsPerPage(previousCount + multipleItemsPerPage);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [results]);

  const filteredResults = useMemo(() => {
    return filterOptionsForHouse(myHouse, termToFilter, originalResults);
  }, [myHouse, termToFilter, originalResults]);

  const hasMoreResults = useMemo(() => {
    return filteredResults.length > itemsPerPage;
  }, [filteredResults, itemsPerPage]);

  const shouldFetchMore = useMemo(() => {
    const showingAllOriginal = itemsPerPage >= originalResults.length;
    const nearEndOfFiltered =
      filteredResults.length > 0 && itemsPerPage >= filteredResults.length - 3;

    return showingAllOriginal || nearEndOfFiltered;
  }, [itemsPerPage, originalResults.length, filteredResults.length]);

  const next = () => {
    setItemsPerPage((prev) => prev + multipleItemsPerPage);
  };

  const resultsToShow = useMemo(() => {
    return filterOptionsForHouse(myHouse, termToFilter, originalResults).slice(
      0,
      itemsPerPage
    );
  }, [originalResults, termToFilter, itemsPerPage, myHouse]);

  return {
    next,
    resultsToShow,
    hasMoreResults,
    totalResults: originalResults.length,
    shouldFetchMore,
  };
};

function filterOptionsForHouse(
  myHouse: string,
  termToFilter: string,
  originalResults: ProjetoReferencia[]
) {
  if (!termToFilter || termToFilter === SelectedHouse.ALL) {
    return originalResults;
  } else if (termToFilter === SelectedHouse.OTHER) {
    return originalResults.filter((item) => item.house !== myHouse);
  } else {
    return originalResults.filter((item) => item.house === myHouse);
  }
}
