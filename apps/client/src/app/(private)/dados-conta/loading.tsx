import { AppHeader } from "@/components/app-header/app-header";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function DadosContaLoading() {
  return (
    <article>
      <AppHeader 
        title="Dados da conta" 
        breadcrumb={[
          { label: "Painel", link: "/dashboard" },
          { label: "Dados da conta", link: "" }
        ]} 
      />
      
      <section>
        <Card>
          <CardHeader className="space-y-2">
            <Skeleton className="h-7 w-[280px]" />
          </CardHeader>
          
          <CardContent className="space-y-6">
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Skeleton className="h-4 w-[60px]" /> {/* Label */}
                <Skeleton className="h-10 w-full" /> {/* Input */}
              </div>
              
              <div className="space-y-2">
                <Skeleton className="h-4 w-[80px]" /> {/* Label */}
                <Skeleton className="h-10 w-full" /> {/* Input */}
              </div>
            </div>
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-[60px]" /> {/* Label */}
              <Skeleton className="h-10 w-full" /> {/* Select */}
            </div>
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-[70px]" /> {/* Label */}
              <Skeleton className="h-10 w-full" /> {/* Input */}
            </div>
            
            <div className="space-y-2">
              <Skeleton className="h-4 w-[50px]" /> {/* Label */}
              <Skeleton className="h-10 w-full" /> {/* Input */}
            </div>
            
            <Skeleton className="h-10 w-[180px]" />
            
          </CardContent>
        </Card>
      </section>
    </article>
  );
}