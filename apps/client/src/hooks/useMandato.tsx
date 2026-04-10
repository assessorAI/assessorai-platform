import { useSession } from "next-auth/react";

export const useMandato = () => {
  const { data: session } = useSession();

  if (!session?.user.mandato) {
    return null;
  }

  const mandato = session?.user.mandato[0];

  return mandato;
};
