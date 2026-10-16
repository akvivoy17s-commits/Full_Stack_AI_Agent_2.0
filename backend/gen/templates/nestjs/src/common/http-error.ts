// The one error type the API throws on purpose. The exception filter turns it into { error: { code, message, details? } }.
export class HttpError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: Record<string, string>,
  ) {
    super(message);
  }
}
