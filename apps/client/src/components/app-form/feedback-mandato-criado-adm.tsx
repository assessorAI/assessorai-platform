import { Button } from '@/components/ui/button';
import { CheckCircleIcon } from '@heroicons/react/24/outline';
import styles from './step.module.scss';
import { usePathname, useRouter } from 'next/navigation';
import { DialogClose } from '@/components/ui/dialog';

export function FeedbackMandatoCriadoAdm() {
    const router = useRouter();
    const pathname = usePathname();


    const getBackUrl = () => {
        if (pathname.includes('gestao-mandatos')) {
            return { url: '/adm/gestao-mandatos', label: 'Voltar para gestão de mandatos' };
        }

        return { url: '/adm/gestao-usuarios', label: 'Voltar para gestão de usuários' };
    };

    const handleVoltar = () => {
        setTimeout(() => {
            router.replace(getBackUrl().url);
        }, 1000);
    };

    return (
        <section className={styles.feedbackContainer}>
            <div className={styles.feedbackIconContainer}>
                <CheckCircleIcon className={styles.feedbackIcon} />
            </div>
            <h2 className={styles.title}>Mandato criado com sucesso</h2>
            <DialogClose asChild>
                <Button 
                    variant="outline" 
                    className={styles.feedbackButton} 
                    onClick={handleVoltar}
                >
                    {getBackUrl().label}
                </Button>
            </DialogClose>
        </section>
    );
}