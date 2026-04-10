import { getMandatosHandler } from "@/api/mandato/mandato.handler";
import { NextRequest } from "next/server";

export async function GET(req: NextRequest) {
  return await getMandatosHandler(req);
}