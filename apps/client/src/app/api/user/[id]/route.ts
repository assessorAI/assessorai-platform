import { NextRequest } from "next/server";
import { deleteUserHandler, updateUserHandler } from "@/api/user/user.handle";

export const PUT = async (req: NextRequest, { params }: { params: Promise<{ id: string }> }) => {
  const { id } = await params;
  return updateUserHandler(req, { id });
};

export const DELETE = async (req: NextRequest, { params }: { params: Promise<{ id: string }> }) => {
  const { id } = await params;
  return deleteUserHandler({ id });
};