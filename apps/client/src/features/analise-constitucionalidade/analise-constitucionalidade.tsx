"use client";

import { useEffect, useState } from "react";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AnaliseConstitucionalidadeResult } from "./analise-constitucionalidade-result";
import { useHandleAnaliseConstitucionalidadeRequest } from "./useHandleAnaliseConstitucionalidadeRequest";
import { CardLoading } from "@/components/card-loading/card-loading";
import { CardCollapsible } from "@/components/card-collapsible/card-collapsible";
import { DocumentMagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { CardPlaceholder } from "@/components/card-placeholder/card-placeholder";
import { SparklesIcon } from "@heroicons/react/24/solid";
import { DragDrop } from "@/components/ui/drag-drop";
import { Button } from "@/components/ui/button";

import styles from "./analise-constitucionalidade.module.scss";
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

export function AnaliseConstitucionalidade() {
  const [file, setFile] = useState<File | null>(null);
  const { accordionValue, onClickAccordion, closeAccordion } =
    useCardCollapsible(true);

  const uploadForm = useForm<z.infer<typeof uploadFormSchema>>({
    resolver: zodResolver(uploadFormSchema),
    shouldUnregister: false,
  });

  const uploadFile = uploadForm.watch("file");

  const {
    isLoading: isLoadingAnaliseConstitucionalidade,
    handleAnaliseConstitucionalidadeRequest,
    analiseConstitucionalidade,
    errorAnaliseConstitucionalidade,
  } = useHandleAnaliseConstitucionalidadeRequest();


  useEffect(() => {
    if (file) {
      handleAnaliseConstitucionalidadeRequest(file);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  useEffect(() => {
    if (analiseConstitucionalidade) {
      closeAccordion();
    }
  }, [analiseConstitucionalidade, closeAccordion]);

  useEffect(() => {
    if (errorAnaliseConstitucionalidade) {
      toast.error(errorAnaliseConstitucionalidade);

      uploadForm.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [errorAnaliseConstitucionalidade]);

  return (
    <div className={styles.analisarPlExistentePage}>
      {/* Upload */}
      <CardCollapsible
        title="Analisar Constitucionalidade"
        description="Arraste e solte o arquivo ou clique para selecionar (PDF, DOC, DOCX até 10MB)"
        tooltip="Seu arquivo será lido pela IA para analisar a constitucionalidade e sugerir emendas. Nenhum conteúdo será publicado sem sua confirmação."
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
                isLoadingAnaliseConstitucionalidade ||
                !uploadForm.formState.isValid
              }
              onClick={() => uploadFile && setFile(uploadFile)}
            >
              {isLoadingAnaliseConstitucionalidade ? <Spinner /> : <SparklesIcon />}
              Analisar com IA
            </Button>
          </section>
        }
      />

      {!file &&
        !isLoadingAnaliseConstitucionalidade && (
          <CardPlaceholder text="Sua análise será exibida aqui" />
        )}

      {file && (
        <>
          {isLoadingAnaliseConstitucionalidade && <CardLoading />}

          {analiseConstitucionalidade && (
            <AnaliseConstitucionalidadeResult
              resultadoAnalise={analiseConstitucionalidade}
            />
          )}
        </>
      )}
    </div>
  );
}
