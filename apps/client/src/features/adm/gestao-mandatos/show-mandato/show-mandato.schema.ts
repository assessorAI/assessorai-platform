import { z } from "zod";

export const showMandatoSchema = z.object({
  nome_gerente: z.string(),
  nome_parlamentar: z.string(),
  ue: z.string(),
  municipio: z.string(),
  cargo_parlamentar: z.string(),
  casa_legislativa: z.string(),
  partido: z.string(),
  perfil_parlamentar: z.string(),
  espectro_politico: z.string(),
});

export type ShowMandatoSchema = z.infer<typeof showMandatoSchema>;