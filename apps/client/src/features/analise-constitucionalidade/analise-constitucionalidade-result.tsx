"use client"

import styles from "./analise-constitucionalidade-result.module.scss"
import type {
  AnaliseConstitucionalidadeProps,
} from "./analise-constitucionalidade.types"
import { AnaliseConstitucionalidadeParecer } from "./analise-constitucionalidade.types"
import { Card, CardContent, CardHeader } from "@/components/ui/card"

export const AnaliseConstitucionalidadeResult = ({ resultadoAnalise }: AnaliseConstitucionalidadeProps) => {
  const getParecerClass = (parecer: string) => {
    switch (parecer) {
      case AnaliseConstitucionalidadeParecer.FAVORAVEL:
        return styles.resultFavoravel
      case AnaliseConstitucionalidadeParecer.CONTRARIO:
        return styles.resultContrario
      case AnaliseConstitucionalidadeParecer.FAVORAVEL_COM_RESSALVAS:
        return styles.resultFavoravelComRessalvas
    }
  }

  return (
    <section>
      {resultadoAnalise && (
        <Card>
          <CardHeader>
          <h3 className={styles.title}>Análise de constitucionalidade</h3>
          <p className={styles.description}>Relatório detalhado da análise constitucional do projeto</p>

          </CardHeader>
          <CardContent className={styles.cardContent}>
              <div className={styles.content}>
              
                <div className={styles.result + " " + getParecerClass(resultadoAnalise.parecer)}>
                  <p><span className={styles.resultProp}>Parecer:</span> {resultadoAnalise.parecer}</p>
                  {resultadoAnalise.gravidade && (
                    <p><span className={styles.resultProp}>Gravidade:</span> {resultadoAnalise.gravidade}</p>
                  )}
                </div>
              </div>

              <div className={styles.contentResult}>
                {resultadoAnalise.justificativa}
              </div>


              {resultadoAnalise.sugestao && (
                <section>
                <h4 className={styles.sugestaoTitle}>Sugestão</h4>
                <div className={styles.contentResult}>
                  {resultadoAnalise.sugestao}
                </div>
                </section>
              )}
              </CardContent>
        </Card>
      )}

    </section>
  )
}
