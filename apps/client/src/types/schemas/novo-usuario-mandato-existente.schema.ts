import { z } from "zod";
import { dadosPessoaisSchema } from "./dados-pessoais.schema";
import { Mandato } from "@/api/mandato/mandato.types";

const mandatoSchema = z.custom<Mandato | null>()

export const novoUsuarioMandatoExistenteSchema = dadosPessoaisSchema
  .extend({
    mandato: mandatoSchema,
  })
  .refine((data) => data.mandato !== null, {
    message: "Selecione um mandato",
    path: ["mandato"],
  });

export type NovoUsuarioMandatoExistente = z.infer<typeof novoUsuarioMandatoExistenteSchema>;