import { NextRequest } from 'next/server';
import { analiseConstitucionalidadeHandler } from '@/api/analise-constitucionalidade/analise-constitucionalidade.handler';

export async function POST(req: NextRequest, { params }: { params: Promise<{ mandato_id: string }> }) {
  const { mandato_id } = await params;
  return analiseConstitucionalidadeHandler(req, mandato_id);
} 