import { NextRequest } from "next/server";
import { requerimentoHandler } from "@/api/requerimento/requerimento.handler";

export async function POST(req: NextRequest, { params }: { params: Promise<{ mandato_id: string }> }) {
  const { mandato_id } = await params;
  return requerimentoHandler(req, mandato_id);
}