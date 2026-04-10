import { NextRequest, NextResponse } from "next/server";
import htmlToDocx from "html-to-docx";

export async function POST(req: NextRequest) {
  const { html, filename } = await req.json();
  
  const arrayBuffer = await htmlToDocx(html);
  
  return new NextResponse(arrayBuffer, {
    headers: {
      "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "Content-Disposition": `attachment; filename="${filename || "document.docx"}"`,
    },
  });
}