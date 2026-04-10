import { CardSelectable } from "@/components/card-selectable/card-selectable";
import {
  CardSelectableSchema,
  CardSelectableSchemaType,
} from "@/components/card-selectable/card-selectable.schema";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import styles from "./busca-referencias-result.module.scss";
import { ProjetoReferencia, useProjetosReferencias } from "@/context/projetos-referencias.context";
import { useRouter } from "next/navigation";
import { BuscaReferenciasResultDetail } from "./busca-referencias-result-detail";

interface BuscaReferenciaResultFormProps {
  options: ProjetoReferencia[];
  filteredResults: ProjetoReferencia[];
  houseSelectNode: React.ReactNode;
  handleSelectableReferences: (value: boolean) => void;
}

export function BuscaReferenciaResultForm({
  options,
  filteredResults,
  houseSelectNode,
  handleSelectableReferences
}: BuscaReferenciaResultFormProps) {
  const { selectedProjetos, setSelectedProjetos } = useProjetosReferencias();
  const router = useRouter();

  const form = useForm<CardSelectableSchemaType>({
    resolver: zodResolver(CardSelectableSchema),
    defaultValues: { options: [] },
  });

  function cancelSelectReferences() {
    handleSelectableReferences(false);
    form.reset();
  }

  function onSubmit(data: CardSelectableSchemaType) {
    const selectedProjeto = options.reduce<ProjetoReferencia[]>(
      (projetos, item) => {
        if (data.options.includes(item.id)) {
          return [...projetos, { ...item }];
        }
        return projetos;
      },
      []
    );

    setSelectedProjetos(selectedProjeto);
  }
  const handleNavigateToCriarPl = () => {
    router.push("/producao-legislativa/criar-pl");
  };

  const referencesArea = (
    <section className={styles.referencesArea}>
      <h3>Referências anexadas</h3>
      <p>
        As proposições selecionadas foram anexadas à área de Criação de Projeto de Lei.
        Clique abaixo para ser redirecionado e crie um projeto de lei com a ajuda da nossa
        inteligência artificial.
      </p>
      <Button onClick={handleNavigateToCriarPl}>Ir para Criação de Projeto de Lei</Button>
    </section>
  );

  function detailNode(projetoReferencia: ProjetoReferencia) {
    return (<BuscaReferenciasResultDetail
      title={projetoReferencia.title}
      footer={projetoReferencia.house}
      author={projetoReferencia.author}
      url={projetoReferencia.url}
      subject={projetoReferencia.subject}
      chunkText={projetoReferencia.chunk_text}
    />)
  }

  return (
    <>
      { !selectedProjetos.length && (
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className={styles.container}
        >
          <section className={styles.actions}>
            {houseSelectNode}
            <div className={styles.actionsButtons}>
              <Button variant="outline" onClick={cancelSelectReferences}>
                Cancelar
              </Button>
              <Button type="submit" disabled={!form.formState.isValid}>
                Anexar à criação de PL
              </Button>
            </div>
          </section>
          <section className={styles.form}>
            {filteredResults.map((item) => (
              <CardSelectable
                key={item.id}
                id={item.id}
                title={item.title}
                description={item.subject}
                footer={item.house}
                author={item.author}
                control={form.control}
                detail={detailNode(item)}
                chunkDescription={item.chunk_text}
              />
            ))}
          </section>
        </form>
      </Form>
      )}
      
      {selectedProjetos.length > 0 && referencesArea}
    </>
  );
}
