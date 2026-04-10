import { NextRequest } from 'next/server';
import { buscaReferenciasHandler } from '@/api/busca-referencias/busca-referencias.handler';

export async function GET(req: NextRequest) {
  return buscaReferenciasHandler(req);
} 