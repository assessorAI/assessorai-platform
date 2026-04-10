import { registerMemberHandler } from "@/api/register-member/register-member.handler";
import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
    return registerMemberHandler(request);
}