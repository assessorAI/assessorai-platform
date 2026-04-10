import { z } from "zod";
import type { Mandato } from "@/api/mandato/mandato.types";

const mandatoSchema = z.custom<Mandato | null>();

export const showUserSchema = z
  .object({
    first_name: z
      .string()
      .min(2, "Nome deve ter no mínimo 2 caracteres"),
    last_name: z.string().min(2, "Sobrenome deve ter no mínimo 2 caracteres"),
    email: z.string().email("Email inválido"),
    phone: z.string().min(10, "Telefone inválido").max(15, "Telefone inválido"),
    status: z.enum(["active", "inactive"]),
    role: z
      .string()
      .min(1, "Cargo é obrigatório"),
    mandato: mandatoSchema,
    permission_level: z
      .string()
      .min(1, "Tipo de acesso é obrigatório"),
    password: z
      .string()
      .refine(
        (val) => val === "" || val.length >= 6,
        { message: "Senha deve ter no mínimo 6 caracteres" }
      ),
    confirm_password: z
      .string()
  })
  .refine((data) => data.mandato !== null, {
    message: "Mandato é obrigatório",
    path: ["mandato"],
  })
  .refine(
    (data) => {
      if (!data.password || data.password === "") {
        return true;
      }
      return data.password === data.confirm_password;
    },
    {
      message: "As senhas não conferem",
      path: ["confirm_password"],
    }
  );

export type ShowUserSchema = z.infer<typeof showUserSchema>;