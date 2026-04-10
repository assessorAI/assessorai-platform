import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function RootNotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-gray-50">
      <div className="max-w-md mx-auto text-center space-y-6">
        <h1 className="text-6xl font-bold text-brand-primary">404</h1>
        <h2 className="text-2xl font-semibold text-gray-800">
          Página não encontrada
        </h2>
        <p className="text-gray-600">
          A página que você está procurando não existe.
        </p>
        <div className="flex gap-4 justify-center">
          <Button asChild variant="default">
            <Link href="/dashboard">
              Ir para o painel
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/login">
              Fazer login
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}