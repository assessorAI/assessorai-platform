import { z } from "zod";
import { cargo } from "@/types/user.types";

export const dadosPessoaisSchema = z.object({
  first_name: z.string().min(2, "O nome deve ter pelo menos 2 caracteres"),
  last_name: z.string().min(2, "O sobrenome deve ter pelo menos 2 caracteres"),
  role: z.enum(cargo, {
    message: "Selecione um cargo"
  }),
  email: z.email("Digite um e-mail válido"),
  phone: z
  .string()
  .min(1, "O telefone é obrigatório")
  .regex(
    /^\(\d{2}\)\d{5}-\d{4}$/,
    "O telefone deve estar no formato (XX)XXXXX-XXXX"
  ),
});

export type dadosPessoais = z.infer<typeof dadosPessoaisSchema>;