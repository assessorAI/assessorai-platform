import z from "zod";

export const BuscaReferenciasSchema = z.object({
  tema: z.string().min(1, { message: "O campo de tema deve ser preenchido." }),
});