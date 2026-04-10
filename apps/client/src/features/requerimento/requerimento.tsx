"use client";

import { CardCollapsible } from "@/components/card-collapsible/card-collapsible";
import { DocumentMagnifyingGlassIcon } from "@heroicons/react/24/outline";
import {
  Form,
  FormField,
  FormItem,
  FormMessage,
  FormLabel,
  FormControl,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useCardCollapsible } from "@/components/card-collapsible/useCardCollapsible";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  formSchema,
  ACCEPTED_TYPES,
  ACCEPTED_EXTS,
  MAX_FILE_MB,
} from "./requerimento.schema";
import { SparklesIcon } from "@heroicons/react/24/outline";
import { Spinner } from "@/components/ui/spinner";
import { DragDrop } from "@/components/ui/drag-drop";
import styles from "./requerimento.module.scss";
import { useHandleRequerimento } from "./useHandleRequerimento";
import { CardCollapsibleColor } from "@/components/card-collapsible/card-collapsible.types";
import { CardPlaceholder } from "@/components/card-placeholder/card-placeholder";
import { DocViewer } from "@/components/doc-viewer/doc-viewer";
import { useEffect } from "react";
import { toast } from "sonner";
import { DocViewerColor } from "@/components/doc-viewer/doc-viewer.types";

export function Requerimento() {
  const { accordionValue, onClickAccordion, closeAccordion } =
    useCardCollapsible(true);

  const { handleRequerimento, requerimento, isLoading, error } =
    useHandleRequerimento();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { text: "", files: null },
    mode: "onChange",
  });

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  useEffect(() => {
    if (!isLoading && requerimento) {
      closeAccordion();
    }
  }, [requerimento, closeAccordion, isLoading]);

  function onSubmit(values: z.infer<typeof formSchema>) {
    const { text, files } = values;
    handleRequerimento(text, files ?? undefined);
  }

  return (
    <section className={styles.requerimentoPage}>
      <CardCollapsible
        defaultOpen
        value={accordionValue}
        onValueChange={onClickAccordion}
        title="Dados do Requerimento ou Indicação"
        description="Gere requerimentos formais com estrutura e linguagem adequadas e adicione documentos de referência em anexo."
        icon={<DocumentMagnifyingGlassIcon />}
        color={CardCollapsibleColor.SECONDARY}
        content={
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="text"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Descrição</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Descreva aqui o que você gostaria que estivesse contido nesse requerimento/indicação."
                        rows={5}
                        {...field}
                      />
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
                  <Spinner />
                ) : (
                  <>
                    <SparklesIcon className="w-4 h-4" />
                  </>
                )}
                Criar com IA
              </Button>
            </form>
          </Form>
        }
      />

      <section>
        {!requerimento && !isLoading && (
          <CardPlaceholder text="Seu requerimento será exibido aqui" />
        )}

        {(isLoading || requerimento) && (
          <DocViewer
            title="Documento gerado"
            content={requerimento?.response ?? ""}
            isLoading={isLoading}
            color={DocViewerColor.SECONDARY}
          />
        )}  
      </section>
    </section>
  );
}
