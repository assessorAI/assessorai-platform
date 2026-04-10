import { addDocumentToMandatoHandler, deleteDocumentFromMandatoHandler } from "@/api/mandato/mandato.handler";
import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  return addDocumentToMandatoHandler(request);
}

export async function DELETE(request: NextRequest) {
  return deleteDocumentFromMandatoHandler(request);
}