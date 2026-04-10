import { Button } from '@/components/ui/button';
import { CheckCircleIcon } from '@heroicons/react/24/outline';
import styles from './step.module.scss';
import { useRouter } from 'next/navigation';


export function FeedbackCadastroEnviado() {
    const router = useRouter();

    return (
        <section className={styles.feedbackContainer}>
            <div className={styles.feedbackIconContainer}>
            <CheckCircleIcon className={styles.feedbackIcon} />
            </div>
            <h2 className={styles.title}>Seu cadastro foi concluído com sucesso</h2>
            <p className={styles.feedbackDescription}>Agora você pode acessar a plataforma com o e-mail e senha cadastrados</p>
            <Button variant="outline" className={styles.feedbackButton} onClick={() => router.push('/login')}>Entrar</Button>
        </section>
    );
}