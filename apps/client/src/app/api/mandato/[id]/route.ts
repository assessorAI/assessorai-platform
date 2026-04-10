import { deleteMandatoHandler, updateMandatoHandler } from "@/api/mandato/mandato.handler";
import { NextRequest } from "next/server";

export async function PUT(req: NextRequest,  { params }: { params: Promise<{ id: string }> } ) {
    const { id } = await params;

    return updateMandatoHandler(req, { id });
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    return await deleteMandatoHandler({ id });
}