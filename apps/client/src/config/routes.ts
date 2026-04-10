// Configuração centralizada de rotas da aplicação

export const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
] as const;

export const PROTECTED_ROUTES = [
  '/',
  '/dashboard',
  '/producao-legislativa',
  '/mandato',
  '/requerimentos',
  '/adm',
] as const;

// Função helper para verificar se a rota é pública
export const isPublicRoute = (pathname: string): boolean => {
  return PUBLIC_ROUTES.some(route => route === pathname);
};

// Função helper para verificar se a rota é protegida
export const isProtectedRoute = (pathname: string): boolean => {
  return PROTECTED_ROUTES.some(route => pathname.startsWith(route));
};
