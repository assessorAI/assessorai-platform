import { CheckIcon } from "@heroicons/react/24/outline"

import styles from "./reset-password.module.scss";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export function ResetPasswordSuccess() {
  const router = useRouter();

  return (
    <section className={styles.successContainer}>
        <div className={styles.checkIconContainer}>
            <CheckIcon className={styles.checkIcon} />
        </div>
      <h2 className={styles.title}>Senha alterada com sucesso</h2>
      <Button onClick={() => router.push("/login")}>
        Fazer login
      </Button>
    </section>
  );
}