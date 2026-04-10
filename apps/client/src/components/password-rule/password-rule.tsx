import { cn } from "@/lib/utils";
import { CheckIcon, XMarkIcon } from "@heroicons/react/24/outline";
import styles from "./password-rule.module.scss";

export function PasswordRules({ password }: { password: string }) {
  const rules = {
    length: password.length >= 8,
    number: /\d/.test(password),
    letter: /[A-Za-z]/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };

  return (
    <div className={styles.passwordRules}>
      <PasswordRule label="Mínimo de 8 caracteres" valid={rules.length} />
      <PasswordRule label="Pelo menos um número" valid={rules.number} />
      <PasswordRule label="Pelo menos uma letra" valid={rules.letter} />
      <PasswordRule
        label="Pelo menos um caractere especial (ex: @ ! +)"
        valid={rules.special}
      />
    </div>
  );
}

export function PasswordRule({ label, valid }: { label: string; valid: boolean }) {
  const Icon = valid ? CheckIcon : XMarkIcon;
  return (
    <div
      className={styles.passwordRule}
    >
      <Icon className={cn(styles.passwordRuleIcon, valid ? styles.passwordRuleIconValid : styles.passwordRuleIconInvalid)} />
      <span>{label}</span>
    </div>
  );
}
