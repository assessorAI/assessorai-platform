import { fileToBase64, readFileAsText } from "./file-to-base64";

export async function convertFileToContentJson(
  file: File
): Promise<{ content: string; type: string }> {
  const isPlainText = file.type === "text/plain";

  if (isPlainText) {
    return {
      content: await readFileAsText(file),
      type: "text",
    };
  }

  return {
    content: await fileToBase64(file),
    type: "file",
  };
}
