import { NextRequest } from "next/server";
import { addUserToMandatoHandler } from "@/api/mandato/mandato.handler";

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return addUserToMandatoHandler(req, { id });
}