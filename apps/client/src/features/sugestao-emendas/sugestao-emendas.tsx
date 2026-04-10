"use client";

import { useEffect, useState } from "react";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SugestoesEmendasResult } from "./sugestao-emendas-result";
import { GerarEmenda } from "../gerar-emenda/gerar-emenda";
import { CardLoading } from "@/components/card-loading/card-loading";
import { useHandleSugestaoEmendaRequest } from "../sugestao-emendas/useHandleSugestaoEmendaRequest";
import { Emenda } from "@/api/emenda/emenda.types";
import { CardCollapsible } from "@/components/card-collapsible/card-collapsible";
import { DocumentMagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { SparklesIcon } from "@heroicons/react/24/solid";
import { CardPlaceholder } from "@/components/card-placeholder/card-placeholder";
import { DragDrop } from "@/components/ui/drag-drop";
import { Button } from "@/components/ui/button";

import styles from "./sugestao-emendas.module.scss";

import { z } from "zod";
import {
  uploadFormSchema,
  ACCEPTED_TYPES,
  ACCEPTED_EXTS,
  MAX_FILE_MB,
} from "../../types/upload.schema";
import { useCardCollapsible } from "@/components/card-collapsible/useCardCollapsible";
import { toast } from "sonner";
import { Spinner } from "@/components/ui/spinner";

export function SugestaoEmendas() {
  const [file, setFile] = useState<File | null>(null);
  const [isLoadingEmenda, setIsLoadingEmenda] = useState(false);
  const { accordionValue, onClickAccordion, closeAccordion } =
    useCardCollapsible(true);

  const uploadForm = useForm<z.infer<typeof uploadFormSchema>>({
    resolver: zodResolver(uploadFormSchema),
    shouldUnregister: false,
  });

  const uploadFile = uploadForm.watch("file");

  const {
    isLoading,
    handleSugestaoEmendaRequest,
    sugestoesEmendas,
    errorSugestaoEmenda,
  } = useHandleSugestaoEmendaRequest();

  const [emendaSelecionada, setEmendaSelecionada] = useState<Emenda | null>(
    null
  );

  const handleEmendaSelecionada = async (emendaSelecionada: Emenda) => {
    setEmendaSelecionada(emendaSelecionada);
  };

  useEffect(() => {
    if (file) {
      handleSugestaoEmendaRequest(file);
      setEmendaSelecionada(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  useEffect(() => {
    if (sugestoesEmendas && sugestoesEmendas.emendas?.length > 0) {
      closeAccordion();
    }
  }, [sugestoesEmendas, closeAccordion]);

  useEffect(() => {
    if (errorSugestaoEmenda) {
      toast.error(errorSugestaoEmenda);
    }
  }, [errorSugestaoEmenda]);

  return (
    <div className={styles.sugestaoEmendasPage}>
      {/* Upload */}
      <CardCollapsible
        title="Sugestão de emendas"
        description="Arraste e solte o arquivo ou clique para selecionar (PDF, DOC, DOCX até 10MB)"
        tooltip="Seu arquivo será lido pela IA para sugerir emendas. Nenhum conteúdo será publicado sem sua confirmação."
        value={accordionValue}
        onValueChange={onClickAccordion}
        icon={<DocumentMagnifyingGlassIcon />}
        content={
          <section>
            <DragDrop
              value={uploadFile ?? null}
              onChange={(f) =>
                uploadForm.setValue("file", f as File, { shouldValidate: true })
              }
              accept={[...ACCEPTED_TYPES, ...ACCEPTED_EXTS]}
              maxSizeMb={MAX_FILE_MB}
              error={
                uploadForm.formState.errors.file?.message as string | undefined
              }
            />

            <Button
              className={styles.button}
              disabled={
                !uploadFile ||
                isLoading ||
                !uploadForm.formState.isValid
              }
              onClick={() => uploadFile && setFile(uploadFile)}
            >
              {isLoading ? <Spinner /> : <SparklesIcon />}
              Criar com IA
            </Button>
          </section>
        }
      />

      {!file && !isLoading && (
        <CardPlaceholder text="As sugestões de emendas serão exibidas aqui" />
      )}

      {file && (
        <>
          {isLoading && <CardLoading />}

          {sugestoesEmendas && sugestoesEmendas.emendas?.length > 0 && (
            <SugestoesEmendasResult
              sugestoesEmendas={sugestoesEmendas.emendas}
              onClickGerarEmenda={() => setIsLoadingEmenda(true)}
              loading={isLoadingEmenda}
              onEmendaSelecionada={handleEmendaSelecionada}
            />
          )}

          {emendaSelecionada && (
            <GerarEmenda
              sugestaoEmenda={emendaSelecionada}
              file={file}
              onEmendaGerada={() => setIsLoadingEmenda(false)}
            />
          )}
        </>
      )}
    </div>
  );
}
