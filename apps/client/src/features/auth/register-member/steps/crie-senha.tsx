import { FormDataRegister, useStep } from "../register-member-step.context";
import { crieSenha, crieSenhaSchema } from "../../../../types/schemas/crie-senha.schema";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import styles from "../../register/register.module.scss";
import { Checkbox } from "@/components/ui/checkbox";
import { LGPDTerms } from "../../register/lgpd-terms";
import { Dialog } from "@/components/ui/dialog";
import { DialogTrigger } from "@/components/ui/dialog";
import { DialogContent } from "@/components/ui/dialog";
import { DialogHeader } from "@/components/ui/dialog";
import { DialogTitle } from "@/components/ui/dialog";
import { PasswordRules } from "@/components/password-rule/password-rule";
import { registerMemberService } from "../register-member.service";
import { useState } from "react";
import { Spinner } from "@/components/ui/spinner";
import { InputPassword } from "@/components/ui/input-password";
import { useSearchParams } from "next/navigation";

export function CrieSenha() {
  const { nextStep, updateData, formData, prevStep } = useStep();
  const [isLoading, setIsLoading] = useState(false);
  const token = useSearchParams().get("token");

  const form = useForm<crieSenha>({
    resolver: zodResolver(crieSenhaSchema),
    defaultValues: {
      password: formData.password || "",
      confirm_password: formData.confirm_password || "",
      lgpd_check: formData.lgpd_check || false,
    },
  });

  const password = form.watch("password");

  const onSubmit = async (values: crieSenha) => {
    updateData(values);

    try {
      setIsLoading(true);
      const completeData: FormDataRegister = {
        token,
        ...formData,
        password: values.password,
        lgpd_check: values.lgpd_check,
      } as FormDataRegister;

      await registerMemberService.registerMember(completeData);

      nextStep();
    } catch {
      form.setError("root", { message: "Erro ao registrar usuário" });
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <section className={styles.stepContainer}>
      <div className={styles.stepHeader}>
        <Button onClick={prevStep} variant="ghost">
          <ArrowLeftIcon className={styles.backIcon} />
        </Button>
        <span className={styles.stepNumber}>Passo 2 de 2</span>
      </div>
      <h2 className={styles.title}>Crie sua senha</h2>
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
          <FormField
            control={form.control}
            name="lgpd_check"
            render={({ field }) => (
              <FormItem>
                <div className={styles.lgpdContainer}>
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={(checked) =>
                        field.onChange(checked as boolean)
                      }
                    />
                  </FormControl>
                  <FormLabel className="flex items-center gap-1">
                    Li e concordo com os
                    <Dialog>
                      <DialogTrigger asChild>
                        <span
                          className="underline cursor-pointer hover:text-brand-accent"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Termos de Uso
                        </span>
                      </DialogTrigger>
                      <DialogContent className="max-w-3xl">
                        <DialogHeader>
                          <DialogTitle>
                            Política de Privacidade, Proteção, Segurança e
                            Tratamento de Dados Pessoais
                          </DialogTitle>
                        </DialogHeader>
                        <LGPDTerms />
                      </DialogContent>
                    </Dialog>
                  </FormLabel>
                </div>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormItem>
            <FormMessage>{form.formState.errors.root?.message}</FormMessage>
          </FormItem>

          <Button type="submit" className={styles.submit} disabled={isLoading || !form.formState.isValid}>
            {isLoading && <Spinner />}
            Finalizar cadastro
          </Button>
        </form>
      </Form>
    </section>
  );
}
