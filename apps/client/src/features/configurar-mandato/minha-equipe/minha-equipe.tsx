import { Card, CardContent, CardHeader } from "@/components/ui/card";
import styles from "./minha-equipe.module.scss";
import { MinhaEquipeTable } from "./minha-equipe-table/minha-equipe-table";
import { MinhaEquipeForm } from "./minha-equipe-form/minha-equipe-form";
import { UserResponse } from "@/api/user/user.types";
import { hasPermission } from "@/lib/check-permissions";
import { useSession } from "next-auth/react";
import { PermissionLevel } from "@/types/user.types";

export function MinhaEquipe({ users }: { users: UserResponse[] }) {
  const { data: session } = useSession();
  const permissionLevel = session?.user?.permission_level;

  const canAddMember = hasPermission(permissionLevel as PermissionLevel, "member:add");

    return (
    <section className={styles.container}>
      <Card>
        <CardHeader className={styles.header}>
          <h2 className={styles.title}>Minha equipe</h2>
          {canAddMember ? <p className={styles.description}>Envie convite para até três membros da sua equipe digitando o email do convidado abaixo.</p> : null}
        </CardHeader>
        <CardContent className={styles.cardContent}>
          {canAddMember ? <MinhaEquipeForm users={users}/> : null}
          <MinhaEquipeTable users={users} />
        </CardContent>
      </Card>
    </section>
  );
}