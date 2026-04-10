"use client";

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import styles from "./configurar-conta.module.scss";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { cargo } from "@/types/user.types";
import { PatternFormat } from "react-number-format";
import { Spinner } from "@/components/ui/spinner";
import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { UserResponse } from "@/api/user/user.types";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";
import { dadosContaSchema, DadosContaSchema } from "@/types/schemas/dados-conta.schema";

export function ConfigurarConta({ user }: { user: UserResponse }) {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { update } = useSession();
  
  const form = useForm<DadosContaSchema>({
    resolver: zodResolver(dadosContaSchema),
    defaultValues: {
      email: user.email,
      phone: user.phone,
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
    },
  });

  const onSubmit = async (values: DadosContaSchema) => {
    try {
      setIsLoading(true);
      const response = await restClient(`/api/user/${user.id}`, {
        method: "PUT",
        body: JSON.stringify(values),
      });

      const updatedUser = await response.json();

      // Atualiza a sessão Auth.js com os novos dados
      await update({
        user: {
          ...user,
          ...updatedUser,
        },
      });

      toast.success("Dados da conta atualizados com sucesso");
      router.refresh();
    } catch (error) {
      const errorMessage = error as AppThrowError;
      toast.error(errorMessage.customMessage!);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section>
      <Card>
        <CardHeader className={styles.header}>
          <h2 className={styles.title}>Verifique ou altere seus dados</h2>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className={styles.form}
            >
              <div className={styles.formGroup}>
                <FormField
                  control={form.control}
                  name="first_name"
                  render={({ field }) => (
                    <FormItem className={styles.formGroupItem}>
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
                    <FormItem className={styles.formGroupItem}>
                      <FormLabel>Sobrenome</FormLabel>
                      <FormControl>
                        <Input placeholder="Seu sobrenome" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

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
                          <SelectItem key={cargo} value={cargo}>
                            {cargo}
                          </SelectItem>
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
                        onValueChange={(values) =>
                          field.onChange(values.formattedValue)
                        }
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
                      <Input placeholder="seu@email.com" {...field} disabled/>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                type="submit"
                disabled={!form.formState.isValid || isLoading}
                className={styles.submit}
              >
                {isLoading && <Spinner />}
                Salvar alterações
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </section>
  );
}
