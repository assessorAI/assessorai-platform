import { NextRequest } from "next/server";
import { getUsersHandler } from "@/api/user/user.handle";

export async function GET(req: NextRequest) {
  return getUsersHandler(req);
}