import {
  BuscaReferenciasResultProps,
  SelectedHouse,
} from "./busca-referencias-result.types";
import { Button } from "@/components/ui/button";

import styles from "./busca-referencias-result.module.scss";
import {
  ProjetoReferencia,
  useProjetosReferencias,
} from "@/context/projetos-referencias.context";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";
import { useSession } from "next-auth/react";
import { BuscaReferenciaResultForm } from "./busca-referencias-result-form";
import { CardItem } from "@/components/card-item/card-item";
import { BuscaReferenciasResultDetail } from "./busca-referencias-result-detail";
import { scrollToBottom } from "@/lib/scroll";
import { useHandleVerMais } from "./useHandleVerMais";

export function BuscaReferenciasResult({
  results,
  searchedTerm,
  onReachEnd,
  isLoading
}: BuscaReferenciasResultProps) {
  const { data: session } = useSession();
  const myHouse = session?.user?.casa_legislativa;
  const [selectedHouse, setSelectedHouse] = useState<string>(SelectedHouse.ALL);
  const [isSelectableReferences, setIsSelectableReferences] =
    useState<boolean>(false);
  const { selectedProjetos } = useProjetosReferencias();

  const { next, resultsToShow, totalResults, shouldFetchMore } =
    useHandleVerMais(results, selectedHouse, myHouse!);

  const handleVerMais = () => {
    if (shouldFetchMore) {
      onReachEnd(totalResults);
    }

    next();

    setTimeout(() => {
      scrollToBottom();
    }, 100);
  };

  const houseSelectNode = (
    <Select
      onValueChange={(value) => setSelectedHouse(value)}
      defaultValue={SelectedHouse.ALL}
    >
      <SelectTrigger className={styles.selectHouse}>
        <SelectValue placeholder="Casa legislativa" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={SelectedHouse.ALL}>
          Todas as casas legislativas
        </SelectItem>
        <SelectItem value={SelectedHouse.MY_HOUSE}>
          Minha Casa legislativa
        </SelectItem>
        <SelectItem value={SelectedHouse.OTHER}>Outras casas</SelectItem>
      </SelectContent>
    </Select>
  );

  function detailNode(projetoReferencia: ProjetoReferencia) {
    return (
      <BuscaReferenciasResultDetail
        title={projetoReferencia.title}
        footer={projetoReferencia.house}
        author={projetoReferencia.author}
        subject={projetoReferencia.subject}
        chunkText={projetoReferencia.chunk_text}
        url={projetoReferencia.url}
      />
    );
  }

  const referencesList = (
    <section className={styles.container}>
      <section className={styles.actions}>
        {houseSelectNode}
        {resultsToShow.length > 0 && (
          <Button
            onClick={() => setIsSelectableReferences(!isSelectableReferences)}
          >
            Selecionar referências
          </Button>
        )}
      </section>
      <section className={styles.form}>
        {resultsToShow.map((projeto, index) => (
          <CardItem
            key={index}
            title={<>{projeto.title}</>}
            description={projeto.subject}
            footer={projeto.house}
            author={projeto.author}
            detail={detailNode(projeto)}
            chunkDescription={projeto.chunk_text}
          />
        ))}
      </section>
    </section>
  );

  const noResults = <p className={styles.noResults}>Filtro sem resultados.</p>;

  return (
    <section className={styles.container}>
      {resultsToShow?.length > 0 && !selectedProjetos?.length && (
        <p className={styles.quantityReferences}>
          {totalResults} referências encontradas para &apos;{searchedTerm}
          &apos;
        </p>
      )}

      {!isSelectableReferences && referencesList}

      {isSelectableReferences && (
        <BuscaReferenciaResultForm
          options={resultsToShow}
          filteredResults={resultsToShow}
          houseSelectNode={houseSelectNode}
          handleSelectableReferences={setIsSelectableReferences}
        />
      )}

      {resultsToShow.length === 0 && noResults}


      {selectedProjetos.length === 0 && !isLoading && resultsToShow.length > 0 && (
        <Button
          className={styles.verMaisButton}
          variant="outline"
          onClick={handleVerMais}
        >
          {shouldFetchMore ? "Carregar mais resultados" : "Ver mais"}
        </Button>
      )}
    </section>
  );
}
