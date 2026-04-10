import { z } from "zod";

export const CardSelectableSchema = z.object({
  options: z.array(z.string()).min(1, "Selecione pelo menos uma opção"),
});

export type CardSelectableSchemaType = z.infer<typeof CardSelectableSchema>;
