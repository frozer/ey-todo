import { meApiAuthMeGet, type MeResponse } from "../api"
import { setCsrfToken } from "./csrf";

export const getCurrentUser = async (): Promise<MeResponse | undefined> => {
  const response = await meApiAuthMeGet();
  setCsrfToken(response.data?.csrf_token ?? null);
  return response.data;
}
