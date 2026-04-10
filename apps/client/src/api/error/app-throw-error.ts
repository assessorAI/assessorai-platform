import { errorMap, friendlyErrorMessage } from "./error-map";

export class AppThrowError extends Error {
  public status: number;
  public customMessage?: string;

  constructor(
    status: number,
    origin: "internal" | "external",
    customMessage?: string
  ) {
    super(customMessage || "");
    this.name = "AppThrowError: " + origin;
    this.status = status;
    this.customMessage = customMessage;
    this.sendToLogger();
  }

  sendToLogger() {
    // TODO: Implementar envio para logger
    console.error(this.metadata());
  }

  static async fromFetchResponse(
    response: Response,
    origin: "internal" | "external" = "external"
  ) {
    const status = response.status;
    let customMessage: string | undefined;

    try {
      if (status in errorMap) {
        customMessage = errorMap[response.status as keyof typeof errorMap];
      } else {
        const data = await response.json();
        customMessage = data.details;
      }
    } catch {
      customMessage = friendlyErrorMessage.ERRO_DESCONHECIDO;
    }

    return new AppThrowError(status, origin, customMessage);
  }

  metadata() {
    return {
      name: this.name,
      status: this.status,
      customMessage: this.customMessage,
    };
  }
}

export class AppThrowErrorSpecific extends Error {
  constructor(specificMessage: string) {
    super("");
    this.message = specificMessage;
  }

  metadata() {
    return {
      friendlyMessage: this.message,
    };
  }
}