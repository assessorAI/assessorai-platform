import { NextRequest } from "next/server";
import { deleteUserFromMandatoHandler } from "@/api/mandato/mandato.handler";

export const DELETE = async (req: NextRequest, { params }: { params: Promise<{ id: string, userId: string }> }) => {
  const { id, userId } = await params;
  return deleteUserFromMandatoHandler(req, { id, userId });
}