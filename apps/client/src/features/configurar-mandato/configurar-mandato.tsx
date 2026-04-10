"use client";

import styles from "./configurar-mandato.module.scss";
import { DocumentosCasa } from "./documentos-casa/documentos-casa";
import { DadosMandato } from "./dados-mandato/dados-mandato";
import { MinhaEquipe } from "./minha-equipe/minha-equipe";
import { Mandato } from "@/api/mandato/mandato.types";
import { UserResponse } from "@/api/user/user.types";
import { DocumentosCasa as DocumentosCasaType } from "@/types/documentos-casa.types";

export function ConfigurarMandato({ mandato, users, documents }: 
  { mandato: Mandato, users: UserResponse[], documents: DocumentosCasaType[] }) {
  return (
    <section className={styles.container}>
      <DocumentosCasa mandatoId={mandato.id.toString()} documents={documents} />
      <DadosMandato mandato={mandato} />
      <MinhaEquipe users={users} />
    </section>
  );
}