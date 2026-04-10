'use client'

import { Button } from '@/components/ui/button'
import { signOut } from 'next-auth/react'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { ExclamationCircleIcon } from '@heroicons/react/24/solid'
import { AppThrowError } from '@/api/error/app-throw-error'

export default function Error({
  error,
}: {
  error: AppThrowError & { digest?: string }
}) {

  return (
    <article className="flex flex-col items-center justify-center min-h-[60vh] p-6 max-w-md mx-auto">
        <Alert variant="default">
            <AlertTitle className="text-lg font-semibold pb-2 flex items-center gap-2">
                <ExclamationCircleIcon className="w-10 h-10 text-brand-alert flex-shrink-0 mt-0.5" />
                Ocorreu um erro ao carregar as informações do mandato
            </AlertTitle>
            <AlertDescription className="flex flex-col gap-4">
                {error.message || 'Ocorreu um erro ao carregar as informações do mandato'}
                <Button 
                onClick={() => signOut({ callbackUrl: '/login' })}
                variant="default"
              >
                Tente fazer login novamente
              </Button>
            </AlertDescription>
        </Alert>
    </article>
  )
}