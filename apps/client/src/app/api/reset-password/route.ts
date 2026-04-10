import { resetPasswordHandler } from "@/api/reset-password/reset-password.handler";
import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  return resetPasswordHandler(request);
}