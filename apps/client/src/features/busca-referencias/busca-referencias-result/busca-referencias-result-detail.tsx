import { DialogHeader, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import styles from "./busca-referencias-result-detail.module.scss";

interface BuscaReferenciasResultDetailProps {
    title: string;
    footer: string;
    author: string;
    subject: string;
    chunkText: string;
    url: string;
}

export function BuscaReferenciasResultDetail({ 
    title, 
    footer, 
    author, 
    subject, 
    chunkText,
    url } : BuscaReferenciasResultDetailProps) {
  return (
    <DialogContent className={styles.dialogContent}>
    <DialogHeader className={styles.dialogHeader}>
      <DialogTitle>
        <div className={styles.dialogTitleContainer}>{title}</div>
        <p className={styles.subTitle}>{footer}</p>
      </DialogTitle>
      <DialogDescription asChild>
        <section className={styles.dialogDescription}>
          <section className={styles.footerDialog}>
            <h3 className={styles.dialogSubTitle}>Autores</h3>
            <p>{author}</p>
          </section>
          <h3 className={styles.dialogSubTitle}>Resumo</h3>
          <section className={styles.summaryDialog}>
            {subject}
          </section>
          <h3 className={styles.dialogSubTitle}>Texto completo</h3>
          <section className={styles.chunkDescriptionDialog}>
            {chunkText}
          </section>
          <p>
           Acesse o documento completo no <a href={url} className={styles.link} target="_blank">
            site oficial.
          </a>
          </p>
        </section>
        </DialogDescription>
      </DialogHeader>
    </DialogContent>
  );
}