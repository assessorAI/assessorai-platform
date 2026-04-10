import { AppHeader } from "@/components/app-header/app-header";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function ConfigurarLoading() {
  return (
    <article>
      <AppHeader 
        title="Configurar seu mandato" 
        breadcrumb={[
          { label: "Painel", link: "/dashboard" },
          { label: "Configurar seu mandato", link: "" }
        ]} 
      />

      <section className="space-y-4">
        
        <Card>
          <CardHeader className="space-y-2">
            <Skeleton className="h-7 w-[200px]" /> {/* Título */}
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex gap-4 items-end">
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-[90px]" />
                <Skeleton className="h-10 w-full" />
              </div>
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-[130px]" /> {/* Label "Tipo de documento" */}
                <Skeleton className="h-10 w-full" /> {/* Select */}
              </div>
            </div>
            
            <Skeleton className="h-10 w-[160px]" />
            
            <div className="space-y-3 mt-6">
              <Skeleton className="h-10 w-full" /> {/* Header da tabela */}
              <Skeleton className="h-12 w-full" /> {/* Linha 1 */}
              <Skeleton className="h-12 w-full" /> {/* Linha 2 */}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="space-y-2">
            <Skeleton className="h-7 w-[180px]" /> {/* Título */}
          </CardHeader>
          <CardContent className="space-y-6">
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-[160px]" />
              <Skeleton className="h-10 w-full" />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Skeleton className="h-4 w-[30px]" /> {/* Label "UF" */}
                <Skeleton className="h-10 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-[80px]" /> {/* Label "Município" */}
                <Skeleton className="h-10 w-full" />
              </div>
            </div>
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-[170px]" />
              <Skeleton className="h-10 w-full" />
            </div>
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-[200px]" />
              <Skeleton className="h-10 w-full" />
            </div>
            
            <div className="space-y-4">
              <Skeleton className="h-4 w-[140px]" /> {/* Label */}
              <div className="space-y-3">
                <Skeleton className="h-16 w-full" /> {/* Radio option 1 */}
                <Skeleton className="h-16 w-full" /> {/* Radio option 2 */}
                <Skeleton className="h-16 w-full" /> {/* Radio option 3 */}
              </div>
            </div>
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-[190px]" />
              <Skeleton className="h-10 w-full" />
            </div>
            
            <Skeleton className="h-10 w-[170px]" />
            
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="space-y-3">
            <Skeleton className="h-7 w-[150px]" /> {/* Título */}
            <Skeleton className="h-4 w-full max-w-2xl" /> {/* Descrição linha 1 */}
            <Skeleton className="h-4 w-[280px]" /> {/* Descrição linha 2 */}
          </CardHeader>
          <CardContent className="space-y-6">
            
            <div className="flex gap-4 items-end">
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-[100px]" /> {/* Label */}
                <Skeleton className="h-10 w-full" /> {/* Input email */}
              </div>
              <Skeleton className="h-10 w-[140px]" /> {/* Botão Enviar */}
            </div>
            
            <div className="space-y-3 mt-6">
              <Skeleton className="h-10 w-full" /> {/* Header da tabela */}
              <Skeleton className="h-16 w-full" /> {/* Linha 1 */}
              <Skeleton className="h-16 w-full" /> {/* Linha 2 */}
              <Skeleton className="h-16 w-full" /> {/* Linha 3 */}
            </div>
            
          </CardContent>
        </Card>

      </section>
    </article>
  );
}