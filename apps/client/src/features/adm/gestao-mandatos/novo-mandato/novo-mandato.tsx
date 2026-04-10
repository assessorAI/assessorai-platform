"use client";

import {
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { DialogHeader } from "@/components/ui/dialog";
import { NovoMandatoStep } from "./novo-mandato-step";
import { VisuallyHidden } from "@/components/ui/visually-hidden";
import styles from "./novo-mandato.module.scss";
export function NovoMandato() {
  return (
    <DialogContent className={styles.dialogContent}>
      <DialogHeader>
        {/* Visualmente escondido, mas acessível para leitores de tela */}
        <VisuallyHidden>
          <DialogTitle>Novo Mandato</DialogTitle>
        </VisuallyHidden>
      </DialogHeader>
      <NovoMandatoStep />
    </DialogContent>
  );
}
