import { Card, CardContent, CardHeader } from "@/components/ui/card";
import styles from "./dados-mandato.module.scss";
import {
  dadosMandatoConf,
  dadosMandatoConfSchema,
} from "./dados-mandato.schema";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Form } from "@/components/ui/form";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Button } from "@/components/ui/button";
import { PERFIS_MANDATO, POSICIONAMENTO_MANDATO } from "@/types/mandato.types";
import { useEffect, useState } from "react";
import { dadosMandatoService } from "./dados-mandato.service";
import { toast } from "sonner";
import { Spinner } from "@/components/ui/spinner";
import { Mandato } from "@/api/mandato/mandato.types";
import { useRouter } from "next/navigation";
import { AppThrowError } from "@/api/error/app-throw-error";
import { useSession } from "next-auth/react";
import { PermissionLevel } from "@/types/user.types";
import { hasPermission } from "@/lib/check-permissions";
import { partidosPoliticosTSE } from "@/types/partidos-politicos.const";
import { Combobox } from "@/components/combobox/combobox";

export function DadosMandato({ mandato }: { mandato: Mandato }) {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { data: session } = useSession();
  const permissionLevel = session?.user?.permission_level;

  const form = useForm<dadosMandatoConf>({
    resolver: zodResolver(dadosMandatoConfSchema),
    defaultValues: {
      nome_parlamentar: mandato?.nome_parlamentar || "",
      ue: mandato?.ue || "",
      municipio: mandato?.municipio || "",
      cargo_parlamentar: mandato?.cargo_parlamentar || "",
      casa_legislativa: mandato?.casa_legislativa || "",
      partido: mandato?.partido || "",
      perfil_parlamentar: mandato?.perfil_parlamentar || undefined,
      espectro_politico:
        (mandato?.espectro_politico as keyof typeof POSICIONAMENTO_MANDATO) ||
        undefined,
    },
  });

  useEffect(() => {
    if (mandato) {
      form.reset({
        nome_parlamentar: mandato.nome_parlamentar || "",
        ue: mandato.ue || "",
        municipio: mandato.municipio || "",
        cargo_parlamentar: mandato.cargo_parlamentar || "",
        casa_legislativa: mandato.casa_legislativa || "",
        partido: mandato.partido || "",
        perfil_parlamentar: mandato.perfil_parlamentar || undefined,
        espectro_politico:
          (mandato.espectro_politico as keyof typeof POSICIONAMENTO_MANDATO) ||
          undefined,
      });
    }
  }, [mandato, form]);

  const canEditInput = (input: string) => {
    return hasPermission(permissionLevel as PermissionLevel, `mandato:${input}:edit`);
  }

  const canEditMandato = hasPermission(permissionLevel as PermissionLevel, "mandato:edit"); 

  const onSubmit = async (data: dadosMandatoConf) => {
    try {
      setIsLoading(true);
      const mandatoUpdated = { ...mandato, ...data };

      await dadosMandatoService.updateDadosMandato(mandatoUpdated as Mandato);

      router.refresh();
      toast.success("Dados do mandato atualizados com sucesso");
    } catch (error) {
      const errorMessage = error as AppThrowError;
      toast.error(errorMessage.customMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className={styles.header}>
        <h2 className={styles.title}>Dados do Mandato</h2>
      </CardHeader>
      <CardContent className={styles.content}>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className={styles.form}>
            <FormField
              control={form.control}
              name="nome_parlamentar"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome do Parlamentar</FormLabel>
                  <FormControl>
                    <Input {...field} readOnly={!canEditInput("nome_parlamentar")} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className={styles.ufMunicipioContainer}>
              <FormField
                control={form.control}
                name="ue"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>UF</FormLabel>
                    <FormControl>
                      <Input {...field} readOnly={!canEditInput("ue")} />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="municipio"
                render={({ field }) => (
                  <FormItem className={styles.municipioItem}>
                    <FormLabel>Município</FormLabel>
                    <FormControl>
                      <Input {...field} readOnly={!canEditInput("municipio")} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="cargo_parlamentar"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Cargo do Parlamentar</FormLabel>
                  <FormControl>
                    <Input {...field} readOnly={!canEditInput("cargo_parlamentar")} />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="casa_legislativa"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome da Casa Legislativa</FormLabel>
                  <FormControl>
                    <Input {...field} readOnly={!canEditInput("casa_legislativa")} />
                  </FormControl>
                </FormItem>
              )}
            />

<FormField
            control={form.control}
            name="partido"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Partido político</FormLabel>
                <FormControl>
                  <Combobox
                    items={partidosPoliticosTSE.map((partido) => ({
                      value: partido.sigla,
                      label: `${partido.nome} (${partido.sigla})`,
                    }))}
                    value={field.value}
                    disabled={!canEditInput("partido")}
                    onChange={field.onChange}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

            <FormField
              control={form.control}
              name="perfil_parlamentar"
              render={({ field }) => (
                <FormItem className={styles.radioGroupContainer} >
                  <div className={styles.tooltipContainer}>
                    <FormLabel>Perfil do mandato</FormLabel>
                  </div>
                  <FormControl>
                    <RadioGroup
                      onValueChange={field.onChange}
                      value={field.value}
                      className={styles.radioGroup}
                      disabled={!canEditInput("perfil_parlamentar")}
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
              name="espectro_politico"
              render={({ field }) => (
                <FormItem>
                  <div className={styles.tooltipContainer}>
                    <FormLabel>Posicionamento do mandato</FormLabel>
                  </div>
                  <FormControl>
                    <Select onValueChange={field.onChange} value={field.value} disabled={!canEditInput("espectro_politico")}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione o posicionamento do mandato" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.values(POSICIONAMENTO_MANDATO).map((posicionamento) => (
                          <SelectItem
                            key={posicionamento}
                            value={posicionamento}
                          >
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

            <Button
              type="submit"
              className={styles.submitButton}
              disabled={isLoading || !canEditMandato}
            >
              {isLoading && <Spinner />} Salvar alterações
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
