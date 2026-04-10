"use client";

import {
  Form,
  FormControl,
  FormLabel,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import styles from "./forgot-password.module.scss";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ForgotPassword, forgotPasswordSchema } from "./forgot-password.schema";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import { Spinner } from "@/components/ui/spinner";
import { forgotPasswordService } from "./forgot-password.service";
import { toast } from "sonner";
import { AppThrowError } from "@/api/error/app-throw-error";

export function ForgotPasswordForm() {
  const form = useForm<ForgotPassword>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = async (values: ForgotPassword) => {
    try {
      await forgotPasswordService.forgotPassword(values.email);
      form.reset();
      toast.success("Email de recuperação enviado com sucesso", {
        description: "Verifique sua caixa de entrada para redefinir sua senha",
      });
    } catch (error) {
      const errorMessage = error as AppThrowError;
      toast.error(errorMessage.customMessage!);
    }
  };
  return (
    <section className={styles.container}>
      <Button variant="ghost" asChild className={styles.backButton}>
        <Link href="/login">
          <ArrowLeftIcon className={styles.icon} />
        </Link>
      </Button>
      <header className={styles.header}>
        <h2 className={styles.title}>Esqueci minha senha</h2>
        <p>Digite seu e-mail para receber um link de recuperação</p>
      </header>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-5">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="Email" className={styles.input} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit" disabled={form.formState.isSubmitting || !form.formState.isValid} className={styles.button}>
          {form.formState.isSubmitting && <Spinner />}
            Enviar email de recuperação
            </Button>
        </form>
      </Form>
    </section>
  );
}
