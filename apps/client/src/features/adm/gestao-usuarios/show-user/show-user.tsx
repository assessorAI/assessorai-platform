"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { UserResponse } from "@/api/user/user.types";
import { PencilSquareIcon } from "@heroicons/react/24/outline";
import {
  Form,
  FormLabel,
  FormControl,
  FormItem,
  FormMessage,
  FormField,
} from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Select } from "@/components/ui/select";
import { SelectTrigger } from "@/components/ui/select";
import { SelectValue } from "@/components/ui/select";
import { SelectContent } from "@/components/ui/select";
import { SelectItem } from "@/components/ui/select";
import { PatternFormat } from "react-number-format";
import styles from "./show-user.module.scss";
import {
  cargo,
  PermissionLevel,
  PermissionLevelOptions,
  UserStatus,
} from "@/types/user.types";
import { useState } from "react";
import { showUserSchema, ShowUserSchema } from "./show-user.schema";
import { AlertDialog } from "@/components/ui/alert-dialog";
import {
  AdmAlertDialog,
  DescartarAlteracoesDialog,
  SalvarAlteracoesDialog,
} from "../../../../components/dialogs";
import { toast } from "sonner";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";
import { Spinner } from "@/components/ui/spinner";
import { useQueryClient } from "@tanstack/react-query";
import { ComboboxAsync } from "@/components/combobox-async/combobox-async";
import { getMandatos } from "@/lib/get-mandatos";
import { Mandato } from "@/api/mandato/mandato.types";

export function ShowUser({ user }: { user: UserResponse }) {
  const [editMode, setEditMode] = useState(false);
  const [showAdmAlertDialog, setShowAdmAlertDialog] = useState(false);
  const [showSalvarAlteracoesDialog, setShowSalvarAlteracoesDialog] =
    useState(false);
  const [showDescartarAlteracoesDialog, setShowDescartarAlteracoesDialog] =
    useState(false);
  const [isSavingChanges, setIsSavingChanges] = useState(false);
  const queryClient = useQueryClient();

  const form = useForm<ShowUserSchema>({
    resolver: zodResolver(showUserSchema),
    mode: "onChange",
    defaultValues: {
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      phone: user.phone,
      role: user.role,
      password: "",
      confirm_password: "",
      status: user.is_active ? UserStatus.ACTIVE : UserStatus.INACTIVE,
      permission_level: user.permission_level,
      mandato: user.mandato[0] || null,
    },
  });

  const isChangingToAdmin = (values: ShowUserSchema) => {
    return (
      values.permission_level === PermissionLevel.Admin &&
      user.permission_level !== PermissionLevel.Admin
    );
  };

  const onSubmit = (values: ShowUserSchema) => {
    if (isChangingToAdmin(values)) {
      setShowAdmAlertDialog(true);
    } else {
      setShowSalvarAlteracoesDialog(true);
    }
  };

  const handleSubmit = async () => {
    const userUpdated = {
      first_name: form.getValues().first_name,
      last_name: form.getValues().last_name,
      email: form.getValues().email,
      phone: form.getValues().phone,
      role: form.getValues().role,
      is_active: form.getValues().status === UserStatus.ACTIVE,
      ...(form.getValues().password !== "" && {
        password: form.getValues().password,
      }),
      permission_level: form.getValues().permission_level,
      ...(form.getValues().mandato?.id && {
        mandato: [{ id: form.getValues().mandato!.id! }],
      }),
    };

    try {
      setIsSavingChanges(true);
      await restClient(`/api/user/${user.id}`, {
        method: "PUT",
        body: JSON.stringify(userUpdated),
      });

      // atualiza a lista de usuários
      await queryClient.invalidateQueries({ queryKey: ["users"] });

      toast.success("Usuário atualizado com sucesso");
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
        <SheetTitle>Detalhes do usuário</SheetTitle>
        <Button
          variant="outline"
          className={styles.editButton}
          onClick={handleToggleEditMode}
          aria-label="Editar usuário"
        >
          <PencilSquareIcon className="size-4" />
        </Button>
        <SheetDescription></SheetDescription>
      </SheetHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className={styles.form}>
          <div className={styles.formGroup}>
            <FormField
              control={form.control}
              name="first_name"
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
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
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Sobrenome</FormLabel>
                  <FormControl>
                    <Input placeholder="Seu sobrenome" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <FormField
            control={form.control}
            name="email"
            disabled={!editMode}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="seu@email.com" {...field} />
                </FormControl>
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
                    disabled={!editMode}
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

          <div className={styles.formGroup}>
            <FormField
              control={form.control}
              name="role"
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Cargo</FormLabel>
                  <FormControl>
                    <Select
                      disabled={!editMode}
                      onValueChange={(value) => {
                        form.setValue("role", value, {
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
                        {cargo.map((cargo) => (
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

            <FormField
              control={form.control}
              name="mandato"
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Mandato</FormLabel>
                  <FormControl>
                  <ComboboxAsync<Mandato>
                    disabled={!editMode}
                    fetchOptions={getMandatos}
                    getOptionLabel={(m: Mandato) =>
                      `${m.nome_parlamentar}${m.partido ? ` (${m.partido})` : ""}`
                    }  
                    getOptionValue={(m) => String(m.id)}
                    value={field.value}
                    onValueChange={(value) => {
                      field.onChange(value);
                      // Força o form a detectar mudança
                      form.trigger("mandato");
                    }}
                    queryKey={["mandatos"]}
                    placeholder="Selecione um mandato"
                    pageSize={20}
                  />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className={styles.formGroup}>
            <FormField
              control={form.control}
              name="permission_level"
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Tipo de acesso</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      disabled={!editMode}
                      onValueChange={(value) => {
                        form.setValue("permission_level", value, {
                          shouldDirty: true,
                          shouldValidate: true,
                        });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione um tipo de acesso" />
                      </SelectTrigger>
                      <SelectContent>
                        {PermissionLevelOptions.map((permissionLevel) => (
                          <SelectItem
                            key={permissionLevel.value}
                            value={permissionLevel.value}
                          >
                            {permissionLevel.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="status"
              disabled={!editMode}
              render={({ field }) => (
                <FormItem className={styles.formGroupItem}>
                  <FormLabel>Status</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      disabled={!editMode}
                      onValueChange={(value) => {
                        form.setValue("status", value as UserStatus, {
                          shouldDirty: true,
                          shouldValidate: true,
                        });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione um status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">Ativo</SelectItem>
                        <SelectItem value="inactive">Inativo</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormControl>
                </FormItem>
              )}
            />
          </div>

          <FormField
            control={form.control}
            name="password"
            disabled={!editMode}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Senha</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="confirm_password"
            disabled={!editMode}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirmar senha</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

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

      {/* AlertDialog de Alterar para Admin */}
      <AlertDialog
        open={showAdmAlertDialog}
        onOpenChange={setShowAdmAlertDialog}
      >
        <AdmAlertDialog
          name={`${user.first_name} ${user.last_name}`}
          onConfirm={handleSubmit}
          onCancel={() => {
            setShowAdmAlertDialog(false);
          }}
        />
      </AlertDialog>

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
