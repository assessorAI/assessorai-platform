"use client"

import { useState } from "react";

import styles from './sugestao-emendas.module.scss'
import { CircleCheck, Loader2Icon, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SugestoesEmendasProps } from "./sugestao-emendas.types";


export function SugestoesEmendasResult({ sugestoesEmendas, loading, onClickGerarEmenda, onEmendaSelecionada }: SugestoesEmendasProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  const onSugestaoEmendaSelected = (index: number) => {
    setSelectedIndex(index);
  };

  const generateEmenda = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (selectedIndex === null) return;

    onEmendaSelecionada(sugestoesEmendas[selectedIndex]);
    onClickGerarEmenda();
  };

  return (
    <section className={styles.card}>
      <form onSubmit={generateEmenda}>
        <fieldset>
          <div className={styles.cardHeader}>
            <h3 className={styles.title}>Sugestões de Emendas</h3>
            <legend className={styles.legend}>Selecione as emendas que deseja desenvolver</legend>
          </div>

          <div className={styles.cardContent}>
            {sugestoesEmendas.map((emenda, index) => (
              <label
                key={index}
                className={styles.sugestaoEmendaItem}
              >
                <div className={styles.sugestaoEmendaItemHeader}>
                  <input
                    type="radio"
                    name="opcao"
                    value={index}
                    checked={selectedIndex === index}
                    className="mt-1 hidden peer"
                    onChange={() => onSugestaoEmendaSelected(index)} />

                  <span className={styles.sugestaoEmendaItemTipo}>{emenda.tipo}</span>
                  <span>Art. {emenda.art}º</span>
                  <CircleCheck className={styles.sugestaoEmendaItemCheck} />
                </div>
                <div className={styles.sugestaoEmendaItemText}>
                  {emenda.texto}
                </div>
              </label>
            ))}
          </div>
          <Button type="submit" disabled={selectedIndex === null || loading} className={styles.button}>
            {loading ? (
              <>
                <Loader2Icon className="animate-spin" />
                Gerando emenda completa...
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                Gerar emenda completa
              </>
            )}

          </Button>
        </fieldset>
      </form>
    </section>
  );
}
