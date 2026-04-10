import { NextRequest } from "next/server";
import { createUserHandler } from "@/api/user/user.handle";

export async function POST(req: NextRequest) {
  return await createUserHandler(req);
}