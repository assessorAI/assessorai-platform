"use client";

import { Button } from "@/components/ui/button";
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";

import { Form } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { minhaEquipe, minhaEquipeSchema } from "../minha-equipe.schema";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo, useState } from "react";
import styles from "./minha-equipe-form.module.scss";
import { hasPermission } from "@/lib/check-permissions";
import { PermissionLevel } from "@/types/user.types";
import { useSession } from "next-auth/react";
import { toast } from "sonner";
import { useParams, useRouter } from "next/navigation";
import { Spinner } from "@/components/ui/spinner";
import { UserResponse } from "@/api/user/user.types";
import { restClient } from "@/lib/rest-client";
import { AppThrowError } from "@/api/error/app-throw-error";

export function MinhaEquipeForm({ users }: { users: UserResponse[] }) {
    const [isLoading, setIsLoading] = useState(false);
    const { id: mandatoId } = useParams();
    const router = useRouter();
    const { data: session } = useSession();
    const permissionLevel = session?.user?.permission_level;

    const canAddMember = hasPermission(permissionLevel as PermissionLevel, "member:add");

    const hasThreeMembers = useMemo(() => permissionLevel === PermissionLevel.Manager && users.filter((user) => user.permission_level !== PermissionLevel.Manager).length >= 3, [users, permissionLevel]);

    const form = useForm<minhaEquipe>({
        resolver: zodResolver(minhaEquipeSchema),
        defaultValues: {
          email: "",
        },
      });

    const onSubmit = async (values: minhaEquipe) => {
      try {
        setIsLoading(true);
        await restClient(`/api/mandato/${mandatoId}/users`, {
          method: 'POST',
          body: JSON.stringify(values)
        });

        toast.success('Convite enviado com sucesso'); 
        form.reset();
        router.refresh();
      } catch (error: unknown) {
        const errorMessage = error as AppThrowError;
        toast.error(errorMessage.customMessage!);
      }
      finally {
        setIsLoading(false);
      }
    };

    if (!canAddMember) {
        return null;
    }

    return (
        <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className={styles.form}>
            
        <FormField control={form.control} name="email" render={({ field }) => (
          <FormItem className={styles.formItem}>
            <FormLabel>Email</FormLabel>
            <FormControl>
              <Input type="email" value={field.value} disabled={hasThreeMembers} placeholder="Insira o e-mail do convidado" onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )} />
          <Button type="submit" disabled={isLoading || hasThreeMembers}>
            {isLoading && <Spinner />} Enviar convite</Button>
        </form>
      </Form>
    )
}