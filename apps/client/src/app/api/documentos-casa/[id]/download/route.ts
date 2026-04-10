import { downloadDocumentHandler } from "@/api/mandato/mandato.handler";
import { NextRequest } from "next/server";

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return downloadDocumentHandler(req, { id });
}