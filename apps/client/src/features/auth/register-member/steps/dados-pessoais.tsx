import { useStep } from "../register-member-step.context";
import {
  dadosPessoais,
  dadosPessoaisSchema,
} from "../../../../types/schemas/dados-pessoais.schema";

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

import styles from "../../register/register.module.scss";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { PatternFormat } from "react-number-format";
import { cargo } from "@/types/user.types";

const cargoEnum = cargo.map((cargoItem) => ({
  value: cargoItem,
  label: cargoItem,
}));

export function DadosPessoais() {
  const { nextStep, updateData, formData, userData } = useStep();

  const form = useForm<dadosPessoais>({
    resolver: zodResolver(dadosPessoaisSchema),
    defaultValues: {
      first_name: formData.first_name || "",
      last_name: formData.last_name || "",
      email: userData.email || "",
      phone: formData.phone || "",
      role: formData.role || undefined,
    },
  });

  const onSubmit = (values: dadosPessoais) => {
    updateData(values);
    nextStep();
  };

  return (
    <section className={styles.stepContainer}>
      <div className={styles.stepHeader}>
        <span className={styles.stepNumber}>Passo 1 de 2</span>
      </div>
      <h2 className={styles.title}>Dados Pessoais</h2>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input {...field} disabled />
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
                    {cargoEnum.map((cargo) => (
                      <SelectItem key={cargo.value} value={cargo.value}>
                        {cargo.label}
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

          <Button
            type="submit"
            disabled={!form.formState.isValid}
            className={styles.submit}
          >
            Continuar
          </Button>
        </form>
      </Form>
    </section>
  );
}
