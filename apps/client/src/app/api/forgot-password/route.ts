import { forgotPasswordHandler } from "@/api/forgot-password/forgot-password.handler";
import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
    return forgotPasswordHandler(request);
}