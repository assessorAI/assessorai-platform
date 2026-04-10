"use client";

import { useHandleGerarEmendaRequest } from "./useHandleGerarEmendaRequest";
import { useEffect, useState } from "react";
import { GerarEmendaProps } from "./gerar-emenda.types";
import { CreateEmendaResponse } from "@/api/emenda/emenda.types";
import { DocViewer } from "@/components/doc-viewer/doc-viewer";
import { toast } from "sonner";

export function GerarEmenda({
  sugestaoEmenda,
  file,
  onEmendaGerada,
}: GerarEmendaProps) {
  const [emenda, setEmenda] = useState<CreateEmendaResponse | null>(null);

  const onReceiveEmenda = (data: CreateEmendaResponse) => {
    setEmenda(data);
    onEmendaGerada();
  };

  const onErrorEmenda = (error: string) => {
    toast.error(error);
  };

  const { isLoading: isLoadingEmenda, handleGerarEmendaRequest } =
    useHandleGerarEmendaRequest(onReceiveEmenda, onErrorEmenda);

  useEffect(() => {
    handleGerarEmendaRequest(sugestaoEmenda, file);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sugestaoEmenda]);

  return (
    <DocViewer
      title="Emenda Processada"
      content={emenda?.full_markdown ?? ""}
      isLoading={isLoadingEmenda}
    />
  );
}
