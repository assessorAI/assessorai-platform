import { useStep } from "@/features/auth/register/register-step.context";

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

import { useEffect, useMemo, useState } from "react";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import {
  Select,
  SelectContent,
  SelectValue,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { useHandleBuscaCampos } from "@/hooks/useHandleGetFields";
import { Combobox } from "@/components/combobox/combobox";
import { Spinner } from "@/components/ui/spinner";
import { partidosPoliticosTSE } from "@/types/partidos-politicos.const";
import { AppThrowError } from "@/api/error/app-throw-error";
import { dadosMandato, dadosMandatoSchema } from "@/types/schemas/dados-mandato.schema";
import { checkFieldsService } from "@/lib/check-fields.service";

export function DadosMandato() {
  const [isLoading, setIsLoading] = useState(false);
  const { nextStep, updateData, formData, prevStep, step, totalSteps } = useStep();
  const {
    ufList,
    handleBuscaUF,
    handleBuscaMunicipios,
    municipioList,
    getCasaLegislativa,
  } = useHandleBuscaCampos();

  const form = useForm<dadosMandato>({
    resolver: zodResolver(dadosMandatoSchema),
    defaultValues: {
      nome_parlamentar: formData.nome_parlamentar || "",
      uf: formData.uf || "",
      municipio: formData.municipio || "",
      cargo_parlamentar: formData.cargo_parlamentar || undefined,
      casa_legislativa: formData.casa_legislativa || "",
      partido: formData.partido || "",
    },
  });

  const watchUf = form.watch("uf");
  const watchMunicipio = form.watch("municipio");
  const watchCargo = form.watch("cargo_parlamentar");

  // 1. Carrega UFs apenas uma vez ao montar
  useEffect(() => {
    handleBuscaUF();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 2. Carrega municípios quando UF é selecionada E quando ufList está pronto
  useEffect(() => {
    if (watchUf && ufList.length > 0) {
      const uf = ufList.find((uf) => uf.sigla === watchUf);
      if (uf) {
        handleBuscaMunicipios(uf.id.toString());
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchUf, ufList.length]); 

  // 3. Calcula a casa legislativa de forma derivada
  const casaLegislativaCalculada = useMemo(() => {
    if (!watchCargo || !watchUf) return "";

    const municipio = municipioList.find((m) => m.nome === watchMunicipio);
    const uf = ufList.find((uf) => uf.sigla === watchUf);

    if (!uf) return "";

    return getCasaLegislativa(
      watchCargo,
      uf.nome,
      municipio?.nome ?? ""
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchCargo, watchUf, watchMunicipio, municipioList, ufList]);

  // 4. Sincroniza o valor calculado com o form
  useEffect(() => {
    if (casaLegislativaCalculada) {
      form.setValue("casa_legislativa", casaLegislativaCalculada);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [casaLegislativaCalculada]);


  const handleUfChange = (value: string) => {
    form.setValue("uf", value);

    const municipioAtual = form.getValues("municipio");

    if (municipioAtual && municipioList.length > 0) {
      form.setValue("municipio", "");
    }
  };

  const onSubmit = async (values: dadosMandato) => {
    try {
      setIsLoading(true);
      await checkFieldsService.checkMandato({
        nome: values.nome_parlamentar,
        casa_legislativa: values.casa_legislativa,
        partido: values.partido,
        cidade: values.municipio,
        uf: values.uf,
      });

      updateData(values);
      nextStep();

    } catch (error) {
      form.setError("partido", { message: (error as AppThrowError).customMessage });
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
        <span className={styles.stepNumber}>Passo {step} de {totalSteps}</span>
      </div>
      <h2 className={styles.title}>Dados do mandato</h2>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="nome_parlamentar"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nome do Mandato/Parlamentar</FormLabel>
                <FormControl>
                  <Input placeholder="Ex: Vereador João Silva" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="cargo_parlamentar"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Cargo do Parlamentar</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o cargo do parlamentar" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="Vereador">Vereador</SelectItem>
                    <SelectItem value="Deputado Estadual">
                      Deputado Estadual
                    </SelectItem>
                    <SelectItem value="Deputado Federal">
                      Deputado Federal
                    </SelectItem>
                    <SelectItem value="Senador">Senador</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className={styles.ufMunicipioContainer}>
            <FormField
              control={form.control}
              name="uf"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>UF</FormLabel>
                  <FormControl>
                    <Combobox
                      items={ufList.map((uf) => ({
                        value: uf.sigla,
                        label: uf.nome,
                      }))}
                      value={field.value}
                      onChange={handleUfChange}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="municipio"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Município</FormLabel>
                  <FormControl>
                    <Combobox
                      disabled={!watchUf}
                      items={municipioList.map((municipio) => ({
                        value: municipio.nome,
                        label: municipio.nome,
                      }))}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <FormField
            control={form.control}
            name="casa_legislativa"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nome da Casa Legislativa</FormLabel>
                <FormControl>
                  <Input placeholder="(Preenchimento automático)" disabled {...field} />
                </FormControl>
                <FormMessage />
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
                    onChange={field.onChange}
                  />
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
