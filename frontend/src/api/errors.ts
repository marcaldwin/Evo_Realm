export class ApiRequestError extends Error {
  readonly status: number

  constructor(
    message: string,
    status: number,
  ) {
    super(message)
    this.status = status
  }
}

export async function createApiRequestError(
  response: Response,
  fallbackMessage: string,
): Promise<ApiRequestError> {
  let message = fallbackMessage

  try {
    const body = await response.json() as {
      detail?: unknown
    }

    if (typeof body.detail === 'string') {
      message = body.detail
    }
  } catch {
    message = fallbackMessage
  }

  return new ApiRequestError(message, response.status)
}
