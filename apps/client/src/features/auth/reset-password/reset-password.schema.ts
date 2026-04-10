import { z } from "zod";

export const resetPasswordSchema = z.object({
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
}).refine((data) => data.password === data.confirm_password, {
  path: ["confirm_password"],
  message: "As senhas digitadas não são iguais.",
});

export type resetPassword = z.infer<typeof resetPasswordSchema>;