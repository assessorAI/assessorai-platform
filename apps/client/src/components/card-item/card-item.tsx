import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";
import {
  Dialog,
  DialogTrigger,
} from "../ui/dialog";
import styles from "./card-item.module.scss";

interface CardItemProps {
  title: React.ReactNode;
  description: string;
  footer: string;
  chunkDescription: string;
  author: string;
  detail: React.ReactNode;
}

export function CardItem({
  title,
  description,
  footer,
  detail,
}: CardItemProps) {

  return (
    <Card className={styles.card}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className={styles.description}>{description}</p>
        <Dialog>
          <DialogTrigger className={styles.verCompleto}>
              Ver completo
            </DialogTrigger>
            {detail}
          </Dialog>
      </CardContent>
      <CardFooter>
        <p className={styles.footer}>{footer}</p>
      </CardFooter>
    </Card>
  );
}
