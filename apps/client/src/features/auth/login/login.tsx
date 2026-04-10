"use client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Login, loginSchema } from "./login.schema";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormMessage,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import styles from "./login.module.scss";
import { CustomLink } from "@/components/link";

export function LoginForm() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const form = useForm<Login>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  async function onSubmit(values: Login) {
    setIsLoading(true);

    try {
      const result = await signIn("credentials", {
        email: values.email,
        password: values.password,
        redirect: false,
      });

      if (result?.error) {
        form.setError("root", { message: "Email ou senha incorretos" });
      } else {
        router.push("/dashboard");
      }
    } catch {
      form.setError("root", { message: "Erro de conexão" });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <>
      <div className="text-center mb-8">
        <h1 className="mb-3">
          Conecte-se
        </h1>
        <p className="text-base text-gray-600 leading-relaxed">
          Entre para consultar a AssessorAI, criada pela <b>Legisla Brasil</b>{" "}
          para ajudar seu gabinete a produzir mais e melhor no dia-a-dia
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nome</FormLabel>
                <FormControl>
                  <Input placeholder="Email" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Senha</FormLabel>
                <FormControl>
                  <Input type="password" placeholder="Senha" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className={styles.forgotPasswordLink}>
            <CustomLink href="/forgot-password">Esqueceu sua senha?</CustomLink>
          </div>

          {form.formState.errors.root && (
            <div className="text-red-600 text-sm text-center p-2 bg-red-50 rounded">
              {form.formState.errors.root.message}
            </div>
          )}

          <Button
            type="submit"
            disabled={isLoading}
            className={styles.submit}
          >
            {isLoading ? "Entrando..." : "Continue"}
          </Button>
        </form>
      </Form>

      <div className="text-center text-sm pt-4 border-gray-100">
        <span className="text-gray-600">Não tem conta? </span>
        <CustomLink href="/register">Cadastre um mandato</CustomLink>
      </div>
    </>
  );
}
