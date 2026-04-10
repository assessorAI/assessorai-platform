"use client";

import {
  ExclamationTriangleIcon,
} from "@heroicons/react/24/solid";
import AuthTemplate from "@/components/templates/auth/auth";

export default function Error() {
    const description = (
        <p className="text-2.5xl font-sora font-semibold text-gray-900 leading-[3rem] tracking-[-0.576px]">
          A <span className="text-purple-600">inteligência</span> que<br />
          transforma seu mandato.
        </p>
      )
  return (
    <AuthTemplate description={description}>
      <div className="flex flex-col items-center text-center gap-2">
        <ExclamationTriangleIcon className="w-10 h-10 text-brand-secondary" />
        <h2>Ocorreu um erro!</h2>
        <p className="text-muted-foreground">
          Por favor, tente novamente mais tarde.
        </p>
      </div>
    </AuthTemplate>
  );
}
