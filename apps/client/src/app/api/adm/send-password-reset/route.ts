import { NextRequest } from "next/server";
import { sendPasswordResetHandler } from "@/api/adm/adm.handler";

export async function POST(request: NextRequest) {
  return sendPasswordResetHandler(request);
}