import { Button } from '@/components/ui/button';
import { CheckCircleIcon } from '@heroicons/react/24/outline';
import styles from './step.module.scss';
import { useRouter } from 'next/navigation';
import { DialogClose } from '@/components/ui/dialog';

export function FeedbackUsuarioCriadoAdm() {
    const router = useRouter();

    const handleVoltar = () => {
        setTimeout(() => {
            router.replace('/adm/gestao-usuarios');
        }, 1000);
    };

    return (
        <section className={styles.feedbackContainer}>
            <div className={styles.feedbackIconContainer}>
                <CheckCircleIcon className={styles.feedbackIcon} />
            </div>
            <h2 className={styles.title}>Usuário criado com sucesso</h2>
            <DialogClose asChild>
                <Button 
                    variant="outline" 
                    className={styles.feedbackButton} 
                    onClick={handleVoltar}
                >
                    Voltar para gestão de usuários
                </Button>
            </DialogClose>
        </section>
    );
}