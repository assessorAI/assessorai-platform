import { PERFIS_MANDATO, POSICIONAMENTO_MANDATO } from "@/types/mandato.types";
import { z } from "zod";

export const dadosMandatoConfSchema = z.object({
    nome_parlamentar: z.string(),
    ue: z.string(),
    municipio: z.string(),
    cargo_parlamentar: z.string(),
    casa_legislativa: z.string(),
    partido: z.string(),
    perfil_parlamentar: z.enum(
        PERFIS_MANDATO.map(p => p.value) as [string, ...string[]],
        { message: "Selecione o perfil do mandato" }
      ),
      espectro_politico: z.enum(Object.values(POSICIONAMENTO_MANDATO) as [string, ...string[]],
        { message: "Selecione o posicionamento do mandato" }
      ),
  });
  
  export type dadosMandatoConf = z.infer<typeof dadosMandatoConfSchema>;