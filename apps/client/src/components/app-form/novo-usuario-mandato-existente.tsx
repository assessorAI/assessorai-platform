import { useStep } from "@/features/auth/register/register-step.context";
import { cargo } from "@/types/user.types";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";

import styles from "./step.module.scss";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { PatternFormat } from "react-number-format";
import { Spinner } from "@/components/ui/spinner";
import { AppThrowError } from "@/api/error/app-throw-error";
import { useState } from "react";
import { checkFieldsService } from "@/lib/check-fields.service";
import { novoUsuarioMandatoExistenteSchema, type NovoUsuarioMandatoExistente } from "@/types/schemas/novo-usuario-mandato-existente.schema";
import { getMandatos } from "@/lib/get-mandatos";
import { ComboboxAsync } from "@/components/combobox-async/combobox-async";
import type { Mandato } from "@/api/mandato/mandato.types";


export function NovoUsuarioMandatoExistente() {
  const { nextStep, updateData, formData, step, totalSteps } = useStep();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<NovoUsuarioMandatoExistente>({
    resolver: zodResolver(novoUsuarioMandatoExistenteSchema),
    defaultValues: {
      mandato: (formData as Partial<NovoUsuarioMandatoExistente>).mandato ?? null,
      first_name: formData.first_name || "",
      last_name: formData.last_name || "",
      email: formData.email || "",
      phone: formData.phone || "",
      role: formData.role || undefined,
    },
  });

  const onSubmit = async (values: NovoUsuarioMandatoExistente) => {

    try {
      setIsLoading(true);
      await checkFieldsService.checkEmail(values.email);
      updateData(values);
      nextStep();
    } catch (error) {
      form.setError("email", { message: (error as AppThrowError).customMessage });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className={styles.stepContainer}>
      <div className={styles.stepHeader}>
        <span className={styles.stepNumber}>Passo {step} de {totalSteps}</span>
      </div>
      <h2 className={styles.title}>Dados do usuário</h2>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
              control={form.control}
              name="mandato"
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Mandato</FormLabel>
                  <FormControl>
                  <ComboboxAsync<Mandato>
                    fetchOptions={getMandatos}
                    getOptionLabel={(m: Mandato) =>
                      `${m.nome_parlamentar}${m.partido ? ` (${m.partido})` : ""}`
                    }                    
                    getOptionValue={(m: Mandato) => String(m.id)}
                    value={field.value}
                    onValueChange={field.onChange}
                    queryKey={["mandatos"]}
                    placeholder="Selecione um mandato"
                    pageSize={20}
                  />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          <FormField
            control={form.control}
            name="first_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nome</FormLabel>
                <FormControl>
                  <Input placeholder="Seu primeiro nome" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="last_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Sobrenome</FormLabel>
                <FormControl>
                  <Input placeholder="Seu sobrenome" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="role"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Cargo</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione um cargo" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {cargo.map((cargo) => (
                      <SelectItem key={cargo} value={cargo}>{cargo}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Telefone</FormLabel>
                <FormControl>
                  <PatternFormat
                    format="(##)#####-####"
                    customInput={Input}
                    onValueChange={(values) => field.onChange(values.formattedValue)}
                    value={field.value}
                    placeholder="(011) 90000-0000"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="seu@email.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" disabled={!form.formState.isValid || isLoading} className={styles.submit}>
            {isLoading ? 
            <>
            <Spinner />
            Continuar
            </>
            : "Continuar"}
          </Button>
        </form>
      </Form>
    </section>
  );
}
