import { NextRequest } from 'next/server';
import { sugestaoEmendasHandler } from '@/api/sugestao-emendas/sugestao-emendas.handler';

export async function POST(req: NextRequest, { params }: { params: Promise<{ mandato_id: string }> }) {
  const { mandato_id } = await params;
  return sugestaoEmendasHandler(req, mandato_id);
} 