"use client";

import { useStep } from "@/features/auth/register/register-step.context";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import {
  perfilMandato,
  perfilMandatoSchema,
} from "@/types/schemas/perfil_mandato.schema";
import { Checkbox } from "@/components/ui/checkbox";
import { PERFIS_MANDATO, POSICIONAMENTO_MANDATO } from "@/types/mandato.types";
import styles from "./step.module.scss";
import {
  Select,
  SelectItem,
  SelectContent,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { InformationCircleIcon, ArrowLeftIcon } from "@heroicons/react/24/outline";

const posicionamentoMandatoTooltip = `
A informação do posicionamento do mandato é coletada para que nossa inteligência 
artificial consiga gerar projetos de lei e sugestões de emendas customizadas.
Essa informação é privada e não será divulgada.
`;

const perfilMandatoTooltip = `
A informação do perfil do mandato é coletada para que nossa inteligência 
artificial consiga gerar projetos de lei e sugestões de emendas customizadas.
Essa informação é privada e não será divulgada.
`;

export function PerfilMandato() {
  const { nextStep, updateData, formData, prevStep, step, totalSteps } = useStep();

  const form = useForm<perfilMandato>({
    resolver: zodResolver(perfilMandatoSchema),
    defaultValues: {
      perfil_mandato: formData.perfil_mandato || undefined,
      posicionamento_mandato: formData.posicionamento_mandato || undefined,
      primeiro_mandato: formData.primeiro_mandato || false,
    },
  });

  const onSubmit = (values: perfilMandato) => {
    updateData(values);
    nextStep();
  };

  return (
    <section className={styles.stepContainer}>
      <div className={styles.stepHeader}>
        <Button onClick={prevStep} variant="ghost">
          <ArrowLeftIcon className={styles.backIcon} />
        </Button>
        <span className={styles.stepNumber}>Passo {step} de {totalSteps}</span>
      </div>
      <h2 className={styles.title}>Perfil do mandato</h2>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className={styles.form}>
          <FormField
            control={form.control}
            name="perfil_mandato"
            render={({ field }) => (
              <FormItem className={styles.radioGroupContainer}>
                <div className={styles.tooltipContainer}>
                  <FormLabel>Perfil do mandato</FormLabel>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className={styles.tooltipTrigger}>
                        <InformationCircleIcon className={styles.tooltipTriggerIcon} />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right" className={styles.tooltipContent}>
                      <p>{perfilMandatoTooltip}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                </div>
                <FormControl>
                  <RadioGroup
                    onValueChange={field.onChange}
                    value={field.value}
                    className={styles.radioGroup}
                  >
                    {PERFIS_MANDATO.map(({ value, label, desc }) => (
                      <FormItem key={value} className={styles.radioGroupItem}>
                        <FormControl>
                          <RadioGroupItem value={value} />
                        </FormControl>
                        <div className={styles.radioGroupLabelContent}>
                          <FormLabel className={styles.radioGroupLabel}>
                            {label}
                          </FormLabel>
                          <FormDescription>{desc}</FormDescription>
                        </div>
                      </FormItem>
                    ))}
                  </RadioGroup>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="posicionamento_mandato"
            render={({ field }) => (
              <FormItem>
                <div className={styles.tooltipContainer}>
                  <FormLabel>Posicionamento do mandato</FormLabel>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className={styles.tooltipTrigger}>
                          <InformationCircleIcon className={styles.tooltipTriggerIcon} />
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="right" className={styles.tooltipContent}>
                        <p>{posicionamentoMandatoTooltip}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <FormControl>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o posicionamento do mandato" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {Object.values(POSICIONAMENTO_MANDATO).map((posicionamento) => (
                        <SelectItem key={posicionamento} value={posicionamento}>
                          {posicionamento}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="primeiro_mandato"
            render={({ field }) => (
              <FormItem className={styles.checkboxContainer}>
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={(checked) =>
                      field.onChange(checked as boolean)
                    }
                  />
                </FormControl>
                <FormLabel>Este é o primeiro mandato do parlamentar?</FormLabel>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className={styles.submit}>
            Continuar
          </Button>
        </form>
      </Form>
    </section>
  );
}
