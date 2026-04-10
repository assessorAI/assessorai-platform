"use client";

import { z } from "zod";

export const ACCEPTED_TYPES: string[] = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];
export const ACCEPTED_EXTS: string[] = [".pdf", ".doc", ".docx", ".txt"];
export const MAX_FILE_MB = 10;

const fileSchema =
  typeof File === "undefined"
    ? z.any()
    : z
        .instanceof(File, { message: "Arquivo inválido" })
        .refine(
          (f) => f.size <= MAX_FILE_MB * 1024 * 1024,
          `Arquivo deve ter no máximo ${MAX_FILE_MB}MB`
        )
        .refine(
          (f) =>
            ACCEPTED_TYPES.includes(f.type) ||
            ACCEPTED_EXTS.some((ext) => f.name.toLowerCase().endsWith(ext)),
          "Apenas arquivos PDF, DOC, DOCX e TXT são permitidos"
        );

export const formSchema = z.object({
  text: z.string().min(1, { message: "O campo de descrição do requerimento/indicação deve ser preenchido." }),
  files: z.array(fileSchema).optional().nullable(),
});