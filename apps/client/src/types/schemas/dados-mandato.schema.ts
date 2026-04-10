import { partidosPoliticosTSE } from "@/types/partidos-politicos.const";
import { z } from "zod";
import { cargoParlamentarEnum } from "@/types/mandato.types";

export const dadosMandatoSchema = z.object({
  nome_parlamentar: z.string().min(2, "O nome deve ter pelo menos 2 caracteres"),
  uf: z.string().min(2, "O sobrenome deve ter pelo menos 2 caracteres"),
  municipio: z.string().min(2, "O municipio deve ter pelo menos 2 caracteres"),
  cargo_parlamentar: z.enum(Object.values(cargoParlamentarEnum) as [string, ...string[]], {
    message: "Selecione o cargo do parlamentar"
  }),
  casa_legislativa: z.string("Campo obrigatório"),
  partido: z.enum(partidosPoliticosTSE.map(partido => partido.sigla) as [string, ...string[]], {
    message: "Selecione o partido político"
  })
});

export type dadosMandato = z.infer<typeof dadosMandatoSchema>;