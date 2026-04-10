"use client";

import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { FilePlusIcon, Loader2, SparklesIcon } from "lucide-react";
import { useHandleCriarPL } from "./useHandleCriarPL";

import styles from "./criar-pl.module.scss";
import { CardCollapsible } from "@/components/card-collapsible/card-collapsible";
import { DragDrop } from "@/components/ui/drag-drop";
import { toast } from "sonner";
import { useEffect } from "react";
import { DocViewer } from "@/components/doc-viewer/doc-viewer";
import { CardPlaceholder } from "@/components/card-placeholder/card-placeholder";
import {
  formSchema,
  ACCEPTED_TYPES,
  ACCEPTED_EXTS,
  MAX_FILE_MB,
} from "./criar-pl.schema";
import { useCardCollapsible } from "@/components/card-collapsible/useCardCollapsible";
import { useProjetosReferencias } from "@/context/projetos-referencias.context";

export function CriarPl() {
  const { selectedProjetos, clearSelectedProjetos } = useProjetosReferencias();
  const { handleCriarPL, projetoLei, isLoading, error } = useHandleCriarPL();
  const { accordionValue, onClickAccordion, closeAccordion } =
    useCardCollapsible(true);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { text: "", files: null },
    mode: "onChange",

  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    const { text, files } = values;

    handleCriarPL(text, files ?? undefined);
  }

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  useEffect(() => {
    if (!isLoading && projetoLei) {
      closeAccordion();
    }
  }, [projetoLei, closeAccordion, isLoading]);

  useEffect(() => {
    if (selectedProjetos.length) {
      const fileProjects = selectedProjetos.map((projeto) => {
        const conteudo = `Título: ${projeto.title}
          Casa: ${projeto.house}
          Autores: ${projeto.author}
          Assunto: ${projeto.subject}`;

        return new File([conteudo], `${projeto.title}.txt`, {
          type: "text/plain",
        });
      });

      form.setValue("files", fileProjects);
    } 
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProjetos]);

  useEffect(() => {
    return () => {
      clearSelectedProjetos();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <article className={styles.criarPlPage}>
      <section className={styles.cardCollapsible}>
        <CardCollapsible
          defaultOpen
          value={accordionValue}
          onValueChange={onClickAccordion}
          title="Criar Projeto de Lei"
          tooltip="Sua descrição ou arquivo será lido pela IA para propor título, ementa e estrutura inicial do PL. Nenhum conteúdo será publicado sem sua confirmação."
          description=" Insira abaixo uma descrição do tema do projeto de lei e adicione arquivos que possam servir como referência de conteúdo."
          icon={<FilePlusIcon />}
          content={
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="text"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Descreva o tema ou a ideia principal do projeto de lei
                      </FormLabel>
                      <FormControl>
                        <Textarea rows={5} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="files"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Documentos de referência (opcional)</FormLabel>
                      <FormControl>
                        <DragDrop
                          value={field.value ?? null}
                          onChange={field.onChange}
                          multiple
                          accept={
                            [
                              ...ACCEPTED_TYPES,
                              ...ACCEPTED_EXTS,
                            ] as unknown as string[]
                          }
                          maxSizeMb={MAX_FILE_MB}
                          error={
                            form.formState.errors.files?.message as
                              | string
                              | undefined
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="submit"
                  className={styles.button}
                  disabled={isLoading || !form.formState.isValid}
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <SparklesIcon className="w-4 h-4" />
                    </>
                  )}
                  Criar projeto com IA
                </Button>
              </form>
            </Form>
          }
        />
      </section>
      <section>
        {!projetoLei && !isLoading && (
          <CardPlaceholder text="Seu projeto será exibido aqui" />
        )}

        {(isLoading || projetoLei) && (
          <DocViewer
            title="Projeto de Lei gerado"
            content={projetoLei?.full_markdown ?? ""}
            isLoading={isLoading}
          />
        )}
      </section>
    </article>
  );
}
