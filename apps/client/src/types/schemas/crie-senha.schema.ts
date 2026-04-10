import { z } from "zod";

export const crieSenhaSchema = z.object({
  password: z.string()
  .refine((val) => {
    const hasMinLength = val.length >= 8;
    const hasLowercase = /[a-z]/.test(val);
    const hasNumber = /[0-9]/.test(val);
    const hasSymbol = /[^A-Za-z0-9]/.test(val);
    
    return hasMinLength && hasLowercase && hasNumber && hasSymbol;
  }, {
    message: "A senha escolhida não cumpre todos os requisitos."
  }),
  confirm_password: z.string(),
  lgpd_check: z.boolean().refine((val) => val === true, {
    message: "Você deve aceitar os termos da LGPD"
  })
}).refine((data) => data.password === data.confirm_password, {
  path: ["confirm_password"],
  message: "As senhas digitadas não são iguais.",
});

export type crieSenha = z.infer<typeof crieSenhaSchema>;

// Schema para criar senha do gerente do mandato - sem validações mais complexas
export const crieSenhaAdmSchema = z.object({
  option: z.enum(["email", "manual"]),
  password: z.string().optional(),
  confirm_password: z.string().optional(),
}).refine((data) => {
  if (data.option === "manual") {
    return data.password && data.password.length >= 6;
  }
  return true;
}, {
  message: "A senha deve ter no mínimo 6 caracteres",
  path: ["password"]
}).refine((data) => {
  if (data.option === "manual") {
    return data.password === data.confirm_password;
  }
  return true;
}, {
  message: "As senhas não são iguais",
  path: ["confirm_password"]
});

export type CrieSenhaAdmForm = z.infer<typeof crieSenhaAdmSchema>;
