import { z } from "zod";
import { PERFIS_MANDATO, POSICIONAMENTO_MANDATO as POSICIONAMENTO_MANDATO_ENUM } from "@/types/mandato.types";

const POSICIONAMENTO_MANDATO_ARRAY = Object.values(POSICIONAMENTO_MANDATO_ENUM);

export const perfilMandatoSchema = z.object({
  perfil_mandato: z.enum(
    PERFIS_MANDATO.map(p => p.value) as [string, ...string[]],
    { message: "Selecione o perfil do mandato" }
  ),
  posicionamento_mandato: z.enum(POSICIONAMENTO_MANDATO_ARRAY as [string, ...string[]],
    { message: "Selecione o posicionamento do mandato" }
  ),
  primeiro_mandato: z.boolean()
});

export type perfilMandato = z.infer<typeof perfilMandatoSchema>;