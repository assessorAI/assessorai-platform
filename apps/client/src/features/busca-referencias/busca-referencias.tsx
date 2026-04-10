"use client";

import { CardCollapsible } from "@/components/card-collapsible/card-collapsible";
import { useState } from "react";
import styles from "./busca-referencias.module.scss";
import { Search } from "lucide-react";

import { BuscaReferenciasSchema } from "./busca-referencias.schema";
import { useHandleBuscaReferencias } from "./useHandleBuscaReferencias";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  Form,
  FormField,
  FormItem,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useEffect } from "react";
import { BuscaReferenciasResult } from "./busca-referencias-result/busca-referencias-result";
import { GridLoading } from "@/components/grid-loading/grid-loading";

export function BuscaReferencias() {
  const { handleBuscarReferencias, referencias, isLoading, error } =
    useHandleBuscaReferencias();
  const form = useForm<z.infer<typeof BuscaReferenciasSchema>>({
    resolver: zodResolver(BuscaReferenciasSchema),
    defaultValues: {
      tema: "",
    },
  });

  const [searchedTerm, setSearchTerm] = useState("");

  const [showResults, setShowResults] = useState(false);

  const loadMore = (offset: number) => {
    handleBuscarReferencias(searchedTerm, offset)
  }

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  function onSubmit(values: z.infer<typeof BuscaReferenciasSchema>) {
    setShowResults(false);
    setSearchTerm(values.tema)
    handleBuscarReferencias(values.tema);
  }

  useEffect(() => {
    if (referencias) {
      setShowResults(true);
      form.reset();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [referencias]);

  const content = (
    <section className={styles.content}>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="tema"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <Input
                    placeholder="Escreva aqui uma palavra chave ou o tema da proposição legislativa"
                    className={styles.input}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button
            type="submit"
            className={styles.submit}
            disabled={isLoading || !form.formState.isValid}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Buscando proposições...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Buscar proposições
              </>
            )}
          </Button>
        </form>
      </Form>
    </section>
  );

  return (
    <article className={styles.container}>
      <section>
        <CardCollapsible
          title="Busca de Referências"
          description="Verifique aqui se sua casa legislativa já possui projetos de lei dentro do tema escolhido e veja projetos de outras casas que podem ser utilizados como referência para o seu mandato."
          icon={<Search />}
          content={content}
          defaultOpen={true}
        ></CardCollapsible>
      </section>

      {showResults && (
        <BuscaReferenciasResult
          key={searchedTerm}
          onReachEnd={loadMore}
          results={referencias!}
          searchedTerm={searchedTerm}
          isLoading={isLoading}
        />
      )}

      {isLoading && <GridLoading count={6} />}
    </article>
  );
}
