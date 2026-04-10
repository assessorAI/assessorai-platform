import { UsersDataTable } from "./data-table/usuarios-data-table";
import { IndicadoresUsuarios } from "./indicadores";
import styles from "./gestao-usuarios.module.scss";

export function GestaoUsuarios({ activeUsersCount, inactiveUsersCount, totalUsersCount }: { activeUsersCount: number, inactiveUsersCount: number, totalUsersCount: number }) {
  return (
    <section className={styles.container}>
      <IndicadoresUsuarios activeUsersCount={activeUsersCount} inactiveUsersCount={inactiveUsersCount} totalUsersCount={totalUsersCount} />
      <UsersDataTable  />
    </section>
  );
}