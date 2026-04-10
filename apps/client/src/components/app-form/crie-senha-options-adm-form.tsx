import { CrieSenhaAdmForm, crieSenhaAdmSchema } from "@/types/schemas/crie-senha.schema";
import { Button } from "../ui/button";
import styles from "./step.module.scss";
import { FormDataRegister, useStep } from "@/features/auth/register/register-step.context";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Form, FormField, FormItem, FormControl, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { SendPasswordResetRequest } from "@/api/adm/adm.types";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";
import { Spinner } from "../ui/spinner";

type CrieSenhaOptionsAdmFormProps = {
  onRegisterCallback: (values: FormDataRegister) => Promise<void>;
}

export function CrieSenhaOptionsAdmForm({ onRegisterCallback }: CrieSenhaOptionsAdmFormProps) {
  const { nextStep, updateData, formData, prevStep, step, totalSteps } = useStep();
  const [selectedOption, setSelectedOption] = useState<"email" | "manual">("email");
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<CrieSenhaAdmForm>({
    resolver: zodResolver(crieSenhaAdmSchema),
    defaultValues: {
      option: "email",
      password: "",
      confirm_password: "",
    },
  });

  const onSubmit = async (values: CrieSenhaAdmForm) => {
    updateData(values);

    try {
      setIsLoading(true);
      const completeData: FormDataRegister = {
        ...formData,
        ...values,
      } as FormDataRegister;

      await onRegisterCallback(completeData);

      if (values.option === "email") {
        const sendPasswordResetRequest: SendPasswordResetRequest = {
          emails: [completeData.email],
        };
        await restClient(`/api/adm/send-password-reset`, {
          method: 'POST',
          body: JSON.stringify(sendPasswordResetRequest),
        });
      }

      nextStep();
    } catch (error: unknown) {
      const errorMessage = error as AppThrowError;
      form.setError("root", { message: errorMessage.customMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOptionChange = (value: string) => {
    const option = value as "email" | "manual";
    setSelectedOption(option);
    form.setValue("option", option);
  };

  return (
    <section className={styles.stepContainer}>
      <div className={styles.stepHeader}>
        <Button onClick={prevStep} variant="ghost">
          <ArrowLeftIcon className={styles.backIcon} />
        </Button>
        <span className={styles.stepNumber}>Passo {step} de {totalSteps}</span>
      </div>
      <h2 className={styles.title}>Senha do gerente do mandato</h2>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3">
          <FormField
            control={form.control}
            name="option"
            render={() => (
              <FormItem>
                <FormControl>
                  <RadioGroup
                    value={selectedOption}
                    onValueChange={handleOptionChange}
                  >
                    <div className="flex items-center gap-2 p-2">
                      <RadioGroupItem value="email" id="email-option" />
                      <Label htmlFor="email-option" className="cursor-pointer flex-1">
                        Enviar email automático para o usuário criar a senha
                      </Label>
                    </div>
                    <div className="flex items-center gap-2 p-2">
                      <RadioGroupItem value="manual" id="manual-option" />
                      <Label htmlFor="manual-option" className="cursor-pointer flex-1">
                        Criar senha temporária manualmente
                      </Label>
                    </div>
                  </RadioGroup>
                </FormControl>
              </FormItem>
            )}
          />

          {/* Campos de senha - aparecem apenas se "manual" estiver selecionado */}
          {selectedOption === "manual" && (
            <div className="space-y-4 pl-2 animate-in fade-in duration-300">
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Senha temporária</FormLabel>
                    <FormControl>
                      <Input 
                        type="password" 
                        placeholder="Digite a senha temporária" 
                        {...field} 
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="confirm_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirme a senha</FormLabel>
                    <FormControl>
                      <Input 
                        type="password" 
                        placeholder="Confirme a senha temporária" 
                        {...field} 
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          )}

          <Button 
            type="submit" 
            className={styles.submit}
            disabled={!form.formState.isValid}
          >
           { isLoading && <Spinner />}
            Finalizar criação do mandato
          </Button>
        </form>
      </Form>
    </section>
  );
}