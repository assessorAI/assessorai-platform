"use client";

import { signOut, useSession } from "next-auth/react";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

const CLOCK_TOLERANCE_MS = 2 * 60 * 1000; // 2 minutos de tolerância
const WARNING_MINUTES = 3; // 3 minutos de aviso
const TIME_TO_REDIRECT = 2000; // 2 segundos antes de redirecionar para o login

export const useSessionMonitor = () => {
  const { data: session, status } = useSession();
  const hasWarning = useRef(false);
  const hasExpired = useRef(false);

  useEffect(() => {
    const checkExpiration = (): boolean => {
      const now = new Date().getTime();
      const expiresAt = new Date(session?.expiresAt as string).getTime();
      const timeLeft = expiresAt - now - CLOCK_TOLERANCE_MS;

      const minutesLeft = Math.floor(timeLeft / 1000 / 60);

      const isExpiredSession = timeLeft <= 0 && !hasExpired.current;

      if (isExpiredSession) {
        hasExpired.current = true;

        toast.error("Sessão expirada", {
          description:
            "Sua sessão expirou. Você será redirecionado para o login em alguns instantes.",
          duration: 5000, // Mostra por 5 segundos
        });

        setTimeout(() => {
          signOut({ callbackUrl: "/login" });
        }, TIME_TO_REDIRECT);

        return true;
      }

      const isWarningSession =
        minutesLeft <= WARNING_MINUTES &&
        minutesLeft > 0 &&
        !hasWarning.current;

      if (isWarningSession) {
        hasWarning.current = true;

        toast.warning("Sessão expirando em breve", {
          description: `Sua sessão expirará em ${minutesLeft} minutos. Você será redirecionado para o login.`,
          duration: 3000, // Mostra por 3 segundos
        });
      }

      return false;
    };

    const shouldStop = checkExpiration();

    if (shouldStop) {
      return;
    }

    const interval = setInterval(() => {
      const shouldStop = checkExpiration();
      if (shouldStop) {
        clearInterval(interval);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [status, session]);
};
