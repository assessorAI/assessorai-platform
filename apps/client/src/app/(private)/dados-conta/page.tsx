import { auth, signOut } from "@/api/auth/index";
import { userService } from "@/api/user/user.service";
import { AppHeader } from "@/components/app-header/app-header";
import { ConfigurarConta } from "@/features/configurar-conta/configurar-conta";
import { UserResponse } from "@/api/user/user.types";

export default async function DadosContaPage() {
  const session = await auth();

  if (!session || session.user === null) {
    signOut({ redirect: false });
    return null;  
  }

  const user: UserResponse = await userService.getUser(Number(session.user.id));

  return (
    <article>
      <AppHeader
        title="Dados da conta"
        breadcrumb={[
          { label: "Painel", link: "/dashboard" },
          { label: "Dados da conta", link: "/dados-conta" },
        ]}
      />
      <ConfigurarConta user={user} />
    </article>
  );
}