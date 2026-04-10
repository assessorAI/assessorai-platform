"use client";

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import styles from "./reset-password.module.scss";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { InputPassword } from "@/components/ui/input-password";
import { PasswordRules } from "@/components/password-rule/password-rule";
import { resetPassword, resetPasswordSchema } from "./reset-password.schema";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useState } from "react";
import { ResetPasswordSuccess } from "./reset-password-success";
import { useSearchParams } from "next/navigation";
import { resetPasswordService } from "./reset-password.service";

export function ResetPassword() {
  const searchParams = useSearchParams();
  const token: string | null = searchParams.get("token");

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const form = useForm<resetPassword>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: "",
      confirm_password: "",
    },
  });

  const password = form.watch("password");

  const onSubmit = async (values: resetPassword) => {
    try {
      setIsLoading(true);
      if (!token) {
        throw new Error("Token não encontrado");
      }

      await resetPasswordService.resetPassword(token, values.password);

      setIsSuccess(true);
    } catch {
      form.setError("root", { message: "Não foi possível redefinir a senha, o seu token de recuperação expirou ou é inválido" });
    }
    finally {
      setIsLoading(false);
    }
  }

  if (isSuccess) {
    return <ResetPasswordSuccess />;
  }

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Recuperação de senha</h2>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className={styles.form}>
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Senha</FormLabel>
                <FormControl>
                  <InputPassword {...field} />
                </FormControl>
                <PasswordRules password={password} />
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="confirm_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirmar senha</FormLabel>
                <FormControl>
                  <InputPassword {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormItem>
            <FormMessage>{form.formState.errors.root?.message}</FormMessage>
          </FormItem>

          <Button type="submit" className={styles.submit} disabled={isLoading}>
            {isLoading && <Spinner />}
            Continuar
          </Button>
        </form>
      </Form>
    </div>
  );
}
