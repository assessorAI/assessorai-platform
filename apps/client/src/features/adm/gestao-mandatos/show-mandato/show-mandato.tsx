import { useForm } from "react-hook-form";
import { showMandatoSchema, ShowMandatoSchema } from "./show-mandato.schema";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { PencilSquareIcon } from "@heroicons/react/24/outline";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Combobox } from "@/components/combobox/combobox";
import { Spinner } from "@/components/ui/spinner";
import styles from "./show-mandato.module.scss";
import { Mandato } from "@/api/mandato/mandato.types";
import { useEffect, useMemo, useState } from "react";
import { cargoParlamentarEnum } from "@/types/mandato.types";
import { partidosPoliticosTSE } from "@/types/partidos-politicos.const";
import { POSICIONAMENTO_MANDATO } from "@/types/mandato.types";
import { PERFIS_MANDATO } from "@/types/mandato.types";
import { useHandleBuscaCampos } from "@/hooks/useHandleGetFields";
import { SalvarAlteracoesDialog } from "@/components/dialogs";
import { DescartarAlteracoesDialog } from "@/components/dialogs";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { restClient } from "@/lib/rest-client";
import { toast } from "sonner";
import { AppThrowError } from "@/api/error/app-throw-error";
import { useQueryClient } from "@tanstack/react-query";

export function ShowMandato({ mandato }: { mandato: Mandato }) {
  const [editMode, setEditMode] = useState(false);
  const [showSalvarAlteracoesDialog, setShowSalvarAlteracoesDialog] =
    useState(false);
  const [showDescartarAlteracoesDialog, setShowDescartarAlteracoesDialog] =
    useState(false);
  const [isSavingChanges, setIsSavingChanges] = useState(false);

  const queryClient = useQueryClient();

  const {
    ufList,
    municipioList,
    getCasaLegislativa,
    handleBuscaUF,
    handleBuscaMunicipios,
  } = useHandleBuscaCampos();

  const form = useForm<ShowMandatoSchema>({
    resolver: zodResolver(showMandatoSchema),
    mode: "onChange",
    defaultValues: {
      nome_gerente: mandato?.gerente?.[0]?.nome ?? "",
      nome_parlamentar: mandato.nome_parlamentar ?? "",
      cargo_parlamentar: mandato.cargo_parlamentar ?? "",
      casa_legislativa: mandato.casa_legislativa ?? "",
      partido: mandato.partido ?? "",
      ue: mandato.ue ?? "",
      municipio: mandato.municipio ?? "",
      espectro_politico: mandato.espectro_politico ?? "",
      perfil_parlamentar: mandato.perfil_parlamentar ?? "",
    },
  });

  const watchUf = form.watch("ue");
  const watchMunicipio = form.watch("municipio");
  const watchCargo = form.watch("cargo_parlamentar");

  // 1. Carrega a lista de UFs apenas uma vez quando o componente é montado
  useEffect(() => {
    handleBuscaUF();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 2. Carrega municípios quando a UF é selecionada E quando ufList está pronto
  useEffect(() => {
    if (watchUf && ufList.length > 0) {
      // Encontra o objeto UF completo baseado na sigla
      const uf = ufList.find((uf) => uf.sigla === watchUf);
      if (uf) {
        // Busca municípios usando o ID da UF
        handleBuscaMunicipios(uf.id.toString());
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchUf, ufList.length]);

  const handleUfChange = (value: string) => {
    form.setValue("ue", value);

    // Se tinha um município selecionado e a lista de municípios já carregou
    const municipioAtual = form.getValues("municipio");

    if (municipioAtual && municipioList.length > 0) {
      // Limpa o município porque mudou o estado
      form.setValue("municipio", "");
    }
  };

  // 3. Calcula a casa legislativa automaticamente baseado em cargo, UF e município
  const casaLegislativaCalculada = useMemo(() => {
    if (!watchCargo || !watchUf) return "";

    const municipio = municipioList.find((m) => m.nome === watchMunicipio);
    const uf = ufList.find((uf) => uf.sigla === watchUf);

    if (!uf) return "";

    return getCasaLegislativa(watchCargo, uf.nome, municipio?.nome ?? "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchCargo, watchUf, watchMunicipio, municipioList, ufList]);

  // 4. Atualiza o campo casa_legislativa sempre que o valor calculado mudar
  useEffect(() => {
    if (casaLegislativaCalculada) {
      form.setValue("casa_legislativa", casaLegislativaCalculada);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [casaLegislativaCalculada]);

  const onSubmit = () => {
    setShowSalvarAlteracoesDialog(true);
  };

  const handleSubmit = async () => {
    const mandatoUpdated = {
      // nome_gerente: form.getValues().nome_gerente,
      nome_parlamentar: form.getValues().nome_parlamentar,
      cargo_parlamentar: form.getValues().cargo_parlamentar,
      casa_legislativa: form.getValues().casa_legislativa,
      partido: form.getValues().partido,
      ue: form.getValues().ue,
      municipio: form.getValues().municipio,
      espectro_politico: form.getValues().espectro_politico,
      perfil_parlamentar: form.getValues().perfil_parlamentar,
    };
    try {
      setIsSavingChanges(true);
      await restClient(`/api/mandato/${mandato.id}`, {
        method: "PUT",
        body: JSON.stringify(mandatoUpdated),
      });
      
      // atualiza a lista de mandatos
      await queryClient.invalidateQueries({ queryKey: ["mandatos"] });

      toast.success("Mandato atualizado com sucesso");
      setEditMode(false);
    } catch (error) {
      const errorMessage = error as AppThrowError;
      toast.error(errorMessage.customMessage!);
    } finally {
      setIsSavingChanges(false);
    }
  };

  const handleCancelChanges = () => {
    if (form.formState.isDirty) {
      setShowDescartarAlteracoesDialog(true);
    } else {
      setEditMode(false);
    }
  };

  const handleConfirmDiscard = () => {
    form.reset();
    setEditMode(false);
    setShowDescartarAlteracoesDialog(false);
  };

  const handleToggleEditMode = () => {
    if (editMode) {
      form.reset();
      setEditMode(false);
    } else {
      setEditMode(true);
    }
  };

  return (
    <>
      <SheetHeader className={styles.sheetHeader}>
        <SheetTitle>Detalhes do mandato</SheetTitle>
        <Button
          variant="outline"
          className={styles.editButton}
          onClick={handleToggleEditMode}
        >
          <PencilSquareIcon className="size-4" />
        </Button>
        <SheetDescription></SheetDescription>
      </SheetHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className={styles.form}>
          <FormField
            control={form.control}
            name="nome_gerente"
            disabled
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nome do Gerente</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="nome_parlamentar"
            disabled={!editMode}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nome do Mandato/Parlamentar</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="cargo_parlamentar"
            disabled={!editMode}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Cargo do Parlamentar</FormLabel>
                <FormControl>
                  <Select
                    disabled={!editMode}
                    onValueChange={(value) => {
                      form.setValue("cargo_parlamentar", value, {
                        shouldDirty: true,
                        shouldValidate: true,
                      });
                    }}
                    value={field.value}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione um cargo" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.values(cargoParlamentarEnum).map((cargo) => (
                        <SelectItem key={cargo} value={cargo}>
                          {cargo}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className={styles.formGroup}>
            <FormField
              control={form.control}
              name="ue"
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>UF</FormLabel>
                  <FormControl>
                    <Combobox
                      disabled={!editMode}
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
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Município</FormLabel>
                  <FormControl>
                    <Combobox
                      disabled={!editMode || !watchUf}
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
            disabled={!editMode}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nome da Casa Legislativa</FormLabel>
                <FormControl>
                  <Input {...field} disabled />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="partido"
            disabled={!editMode}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Partido Político</FormLabel>
                <FormControl>
                  <Combobox
                    items={partidosPoliticosTSE.map((partido) => ({
                      value: partido.sigla,
                      label: partido.nome,
                    }))}
                    disabled={!editMode}
                    value={field.value}
                    onChange={(value) => {
                      form.setValue("partido", value, {
                        shouldDirty: true,
                        shouldValidate: true,
                      });
                    }}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className={styles.formGroup}>
            <FormField
              control={form.control}
              name="espectro_politico"
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Posicionamento</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      disabled={!editMode}
                      onValueChange={(value) => {
                        form.setValue("espectro_politico", value, {
                          shouldDirty: true,
                          shouldValidate: true,
                        });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione um posicionamento" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.values(POSICIONAMENTO_MANDATO).map(
                          (posicionamento: string) => (
                            <SelectItem
                              key={posicionamento}
                              value={posicionamento}
                            >
                              {posicionamento}
                            </SelectItem>
                          )
                        )}
                      </SelectContent>
                    </Select>
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="perfil_parlamentar"
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Perfil</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      disabled={!editMode}
                      onValueChange={(value) => {
                        form.setValue("perfil_parlamentar", value, {
                          shouldDirty: true,
                          shouldValidate: true,
                        });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione um perfil" />
                      </SelectTrigger>
                      <SelectContent>
                        {PERFIS_MANDATO.map((perfil) => (
                          <SelectItem key={perfil.value} value={perfil.value}>
                            {perfil.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                </FormItem>
              )}
            />
          </div>

          {editMode && (
            <SheetFooter className={styles.sheetFooter}>
              <Button
                type="submit"
                disabled={!form.formState.isDirty || !form.formState.isValid}
                className={styles.submit}
              >
                {isSavingChanges && <Spinner />}
                Salvar alterações
              </Button>
              <Button
                type="button"
                variant="destructiveOutline"
                onClick={handleCancelChanges}
              >
                Cancelar
              </Button>
            </SheetFooter>
          )}
        </form>
      </Form>

      {/* AlertDialog de Salvar Alterações */}
      <AlertDialog
        open={showSalvarAlteracoesDialog}
        onOpenChange={setShowSalvarAlteracoesDialog}
      >
        <SalvarAlteracoesDialog
          onConfirm={handleSubmit}
          onCancel={() => {
            setShowSalvarAlteracoesDialog(false);
          }}
        />
      </AlertDialog>

      {/* AlertDialog de Descartar Alterações */}
      <AlertDialog
        open={showDescartarAlteracoesDialog}
        onOpenChange={setShowDescartarAlteracoesDialog}
      >
        <DescartarAlteracoesDialog
          onConfirm={handleConfirmDiscard}
          onCancel={() => setShowDescartarAlteracoesDialog(false)}
        />
      </AlertDialog>
    </>
  );
}
