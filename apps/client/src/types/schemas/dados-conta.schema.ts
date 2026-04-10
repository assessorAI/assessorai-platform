import z from "zod";

export const dadosContaSchema = z.object({
  email: z.email("Digite um e-mail válido"),
  phone: z.string().min(1, "O telefone é obrigatório"),
  first_name: z.string().min(1, "O nome é obrigatório"),
  last_name: z.string().min(1, "O sobrenome é obrigatório"),
  role: z.string().min(1, "O cargo é obrigatório"),
});

export type DadosContaSchema = z.infer<typeof dadosContaSchema>;