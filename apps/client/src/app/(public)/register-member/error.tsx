"use client";

import {
  ExclamationTriangleIcon,
} from "@heroicons/react/24/solid";
import AuthTemplate from "@/components/templates/auth/auth";

export default function Error() {
  const description = (
    <header className="space-y-5">
      <h1>Cadastre seu usuário</h1>

      <p className="text-gray-500 text-lg max-w-sm">
        Você recebeu um convite para fazer parte de uma equipe de um mandato.
        Cadastre seus dados para utilizar a plataforma.
      </p>
    </header>
  );
  return (
    <AuthTemplate description={description}>
      <div className="flex flex-col items-center text-center gap-2">
        <ExclamationTriangleIcon className="w-10 h-10 text-brand-secondary" />
        <h2>Convite inválido ou expirado!</h2>
        <p className="text-muted-foreground">
          Por favor, solicite um novo convite para ativar sua conta.
        </p>
      </div>
    </AuthTemplate>
  );
}
