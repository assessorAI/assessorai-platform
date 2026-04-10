import { Card, CardContent } from "@/components/ui/card";
import styles from "./gestao-usuarios.module.scss";
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  UsersIcon,
} from "@heroicons/react/24/outline";
import { Badge } from "@/components/ui/badge";

export function IndicadoresUsuarios({ activeUsersCount, inactiveUsersCount, totalUsersCount }: { activeUsersCount: number, inactiveUsersCount: number, totalUsersCount: number }) {
  const activeUsersPercentage = (activeUsersCount / totalUsersCount) * 100;
  const inactiveUsersPercentage = (inactiveUsersCount / totalUsersCount) * 100;

  return (
    <section className={styles.indicadoresContainer}>
      <Card className={styles.indicadorCard}>
        <CardContent className={styles.indicadorCardContent}>
          <div className={styles.indicadorCardIcon}>
            <UsersIcon className={styles.indicadorCardIconIcon} />
          </div>
          <div className={styles.indicadorCardContentText}>
            <p className={styles.indicadorCardContentTextTitle}>
              Total de usuários
            </p>
            <p className={styles.indicadorCardContentTextValue}>{totalUsersCount}</p>
          </div>
        </CardContent>
      </Card>
      <Card className={styles.indicadorCard}>
        <CardContent className={styles.indicadorCardContent}>
          <div
            className={
              styles.indicadorCardIcon + " " + styles.indicadorCardIconSuccess
            }
          >
            <CheckCircleIcon className={styles.indicadorCardIconIcon} />
          </div>
          <div className={styles.indicadorCardContentText}>
            <p className={styles.indicadorCardContentTextTitle}>
              Usuários ativos
            </p>
            <div className={styles.indicadorCardContentTextNumber}>
              <p className={styles.indicadorCardContentTextValue}>{activeUsersCount}</p>
              <Badge variant="success" className={styles.percentageBadge}>
                {activeUsersPercentage.toFixed(2)}%
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className={styles.indicadorCard}>
        <CardContent className={styles.indicadorCardContent}>
          <div
            className={
              styles.indicadorCardIcon + " " + styles.indicadorCardIconWarning
            }
          >
            <ExclamationCircleIcon className={styles.indicadorCardIconIcon} />
          </div>
          <div className={styles.indicadorCardContentText}>
            <p className={styles.indicadorCardContentTextTitle}>
              Usuários inativos
            </p>
            <div className={styles.indicadorCardContentTextNumber}>
              <p className={styles.indicadorCardContentTextValue}>{inactiveUsersCount}</p>
              <Badge variant="notice" className={styles.percentageBadge}>
                {inactiveUsersPercentage.toFixed(2)}%
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
