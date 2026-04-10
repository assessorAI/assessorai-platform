import { DocumentosCasaFileType } from "@/types/documentos-casa.types";
import z from "zod";

export const documentosCasaSchema = z.object({
  file: z.instanceof(File, { message: "Arquivo inválido" }),
  file_type: z.enum(Object.values(DocumentosCasaFileType)),
});

export type DocumentosCasa = z.infer<typeof documentosCasaSchema>;