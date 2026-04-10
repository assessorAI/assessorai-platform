import { Sparkles, CopyIcon, MoveDown } from "lucide-react";

import styles from "./doc-viewer.module.scss";
import { DocViewerColor, DocViewerProps } from "./doc-viewer.types";
import { Button } from "../ui/button";

import { markdownToSafeHtml } from "@/lib/markdown/markdown.client";
import { HtmlViewer } from "../html-viwer/html-viwer";
import { downloadHtmlAsDoc } from "@/lib/download-doc";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { CardLoading } from "../card-loading/card-loading";
import { scrollToBottom } from "@/lib/scroll";

export function DocViewer({
  title,
  content,
  isLoading = false,
  color = DocViewerColor.ACCENT,
}: DocViewerProps) {
  const [html, setHtml] = useState<string>("");

  useEffect(() => {
    if (content) {
      setHtml(markdownToSafeHtml(content));
      
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    }
  }, [content]);

  const onCopyText = async () => {
    const plainText =
      new DOMParser().parseFromString(html, "text/html").body.textContent || "";

    const data = [
      new ClipboardItem({
        "text/html": new Blob([html], { type: "text/html" }),
        "text/plain": new Blob([plainText], { type: "text/plain" }),
      }),
    ];

    await navigator.clipboard.write(data);
    toast.success("Texto copiado para a área de transferência");
  };

  return (
    <article className={styles.container}>
      <header className={`${styles.header} ${styles[`header-${color}`]}`}>
        <div className={styles.titleContainer}>
          <h2 className={styles.title}>{title}</h2>
          <span className={styles.tag}>
            <Sparkles className={styles.sparkles} /> Gerada por IA
          </span>
        </div>
        <div className={styles.actions}>
          <Button disabled={isLoading} variant="ghost" onClick={onCopyText}>
            <CopyIcon />
            Copiar texto
          </Button>
          <Button
            disabled={isLoading}
            variant={color === DocViewerColor.ACCENT ? "default" : "secondary"}
            onClick={() => downloadHtmlAsDoc(html, `${title}.doc`)}
          >
            <MoveDown />
            Baixar DOC
          </Button>
        </div>
      </header>

      <section className={styles.content}>
        {isLoading ? <CardLoading noBorder /> : <HtmlViewer html={html} />}
      </section>
    </article>
  );
}
