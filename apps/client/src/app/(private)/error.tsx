'use client'

import { Button } from '@/components/ui/button'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { ExclamationCircleIcon } from '@heroicons/react/24/solid'

export default function Error({
  error,
}: {
  error: Error & { digest?: string }
}) {

  return (
    <article className="flex flex-col items-center justify-center min-h-[60vh] p-6 max-w-md mx-auto">
        <Alert variant="default">
            <AlertTitle className="text-lg font-semibold pb-2 flex items-center gap-2">
                <ExclamationCircleIcon className="w-10 h-10 text-brand-alert flex-shrink-0 mt-0.5" />
                Ocorreu um erro!
            </AlertTitle>
            <AlertDescription className="flex flex-col gap-4">
                {error.message || 'Ocorreu um erro ao carregar a página!'}
                <Button 
                onClick={() => window.location.reload()}
                variant="default"
              >
                Tentar novamente
              </Button>
            </AlertDescription>
        </Alert>
    </article>
  )
}