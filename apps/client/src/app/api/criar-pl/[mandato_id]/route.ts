import { NextRequest } from "next/server";
import { criarPLHandler } from "@/api/criar-pl/criar-pl-handler";

export async function POST(req: NextRequest, { params }: { params: Promise<{ mandato_id: string }> }) {
  const { mandato_id } = await params;
  return criarPLHandler(req, mandato_id);
}