import { z } from "zod";

export const minhaEquipeSchema = z.object({
  email: z.email("Email inválido"),
});

export type minhaEquipe = z.infer<typeof minhaEquipeSchema>;