import { NextRequest } from 'next/server';
import { createEmendaHandler } from '@/api/emenda/emenda.handler';

export async function POST(req: NextRequest, { params }: { params: Promise<{ mandato_id: string }> }) {
  const { mandato_id } = await params;
  return createEmendaHandler(req, mandato_id);
} 