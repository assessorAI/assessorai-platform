import styles from "./card-placeholder.module.scss";

export function CardPlaceholder({ text }: { text: string }) {
  return (
    <div className={styles.cardPlaceholder}>
      <span className={styles.cardPlaceholderText}>{text}</span>
    </div>
  );
}
