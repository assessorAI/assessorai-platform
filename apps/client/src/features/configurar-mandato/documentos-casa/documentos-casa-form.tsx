import { useForm } from "react-hook-form";
import {
  documentosCasaSchema,
  DocumentosCasa as DocumentosCasaFormType,
} from "./documentos-casa.schema";
import { zodResolver } from "@hookform/resolvers/zod";
import { Form } from "@/components/ui/form";
import { FormField } from "@/components/ui/form";
import { FormItem } from "@/components/ui/form";
import { FormLabel } from "@/components/ui/form";
import { FormControl } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { SelectTrigger, SelectValue, SelectItem } from "@/components/ui/select";
import { SelectContent } from "@/components/ui/select";
import { AppThrowError } from "@/api/error/app-throw-error";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useState } from "react";
import styles from "./documentos-casa.module.scss";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { DocumentosCasaFileType } from "@/types/documentos-casa.types";

const documentosCasaTypes = [
  {
    label: DocumentosCasaFileType.CONSTITUICAO,
    value: DocumentosCasaFileType.CONSTITUICAO,
  },
  {
    label: DocumentosCasaFileType.REGIMENTO_INTERNO,
    value: DocumentosCasaFileType.REGIMENTO_INTERNO,
  },
  {
    label: DocumentosCasaFileType.OUTRO,
    value: DocumentosCasaFileType.OUTRO,
  },
];

export function DocumentosCasaForm({ mandatoId }: { mandatoId: string }) {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const form = useForm<DocumentosCasaFormType>({
    resolver: zodResolver(documentosCasaSchema),
    defaultValues: {
      file: undefined,
      file_type: undefined,
    },
  });

  const onSubmit = async (data: DocumentosCasaFormType) => {
    const params = new URLSearchParams({
      mandato_id: mandatoId,
      file_type: data.file_type,
    });
    const formData = new FormData();
    formData.append("file", data.file);

    try {
      setIsLoading(true);
      const response = await fetch(
        `/api/documentos-casa?${params.toString()}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(
          `Erro ao salvar documento: ${response.status} ${response.statusText}`
        );
      }

      toast.success("Documento salvo com sucesso");
      form.reset();
      router.refresh();
    } catch (error) {
      const errorMessage = error as AppThrowError;
      toast.error(errorMessage.customMessage!);
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className={styles.form}>
        <div className={styles.formItems}>
          <div className={styles.formItemFirstRow}>
            <FormField
              control={form.control}
              name="file"
              render={({ field }) => (
                <FormItem className={styles.formItem}>
                  <FormLabel>Documento</FormLabel>
                  <FormControl>
                    <Input
                      type="file"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        field.onChange(file);
                      }}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="file_type"
              render={({ field }) => (
                <FormItem className={styles.formItem}>
                  <FormLabel>Tipo de documento</FormLabel>
                  <FormControl>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o tipo de arquivo" />
                      </SelectTrigger>
                      <SelectContent>
                        {documentosCasaTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                </FormItem>
              )}
            />
          </div>
        </div>

        <Button type="submit" className={styles.button} disabled={isLoading}>
          {isLoading && <Spinner />}
          Salvar documento
        </Button>
      </form>
    </Form>
  );
}
