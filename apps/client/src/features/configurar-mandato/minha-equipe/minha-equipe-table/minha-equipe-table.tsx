"use client";

import styles from "./minha-equipe-table.module.scss";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { UserStatus } from "@/types/user-status.type";
import { Badge } from "@/components/ui/badge";

import { RemoveMember } from "./remove-member";
import { UserResponse } from "@/api/user/user.types";
import { useEffect, useState } from "react";
import { PermissionLevel } from "@/types/user.types";
import { Link } from "react-transition-progress/next";
import { WHATSAPP_URL } from "@/types/whatsap.const";
import { hasPermission } from "@/lib/check-permissions";
import { useSession } from "next-auth/react";

interface MyTeam {
  id: string;
  nome: string;
  email: string;
  status: UserStatus;
}


export function MinhaEquipeTable({ users }: { users: UserResponse[] }) {
  const [myTeam, setMyTeam] = useState<MyTeam[]>([]);
  const { data: session } = useSession();
  const permissionLevel = session?.user?.permission_level;

  const canRemoveMember = hasPermission(permissionLevel as PermissionLevel, "member:remove");

  const getUserStatus = (permissionLevel: PermissionLevel): UserStatus => {
    if (permissionLevel === PermissionLevel.Invited) {
      return UserStatus.INVITED;
    }
    return UserStatus.ACTIVE;
  }

  const getUserName = (user: UserResponse): string => {
    if (user?.first_name && user?.last_name) {
      return user.first_name + " " + user.last_name;
    }
    return "Nome não informado";
  }

  useEffect(() => {
    const myTeamNormalized: MyTeam[] = users
    .filter((user) => user.id.toString() !== session?.user?.id)
    .map((user) => (
      {
      id: user.id.toString(),
      nome: getUserName(user),
      email: user.email,
      status: getUserStatus(user.permission_level),
    })
  );
  
    setMyTeam(myTeamNormalized);
  }, [users, session?.user?.id]);

  const hasThreeMembersNode = (
    <p className={styles.hasThreeMembersNode}>
      Você atingiu o limite de três convites para o seu mandato. Precisa de mais
      membros na equipe? <Link className={styles.helpLink} href={WHATSAPP_URL} target="_black" >Entre em contato com o nosso time</Link>.
    </p>
  );

  if (myTeam.length === 0) {
    return null;
  }

  return (
    <>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {myTeam.map((user) => (
          <TableRow key={user.id}>
            <TableCell>{user.nome}</TableCell>
            <TableCell>{user.email}</TableCell>
            <TableCell>
              <Badge
                variant={
                  user.status === UserStatus.ACTIVE ? "success" : "notice"
                }
              >
                {user.status}
              </Badge>
            </TableCell>
            {canRemoveMember ? <RemoveMember id={Number(user.id)} email={user.email} /> : null}
          </TableRow>
        ))}
      </TableBody>
    </Table>

    { permissionLevel === PermissionLevel.Manager && myTeam.length >= 3 && hasThreeMembersNode}
    </>
  );
}
