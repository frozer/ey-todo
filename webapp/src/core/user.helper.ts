import { meApiAuthMeGet, type MeResponse } from "../api"

export const getCurrentUser = async (): Promise<MeResponse | undefined> => {
  const response = await meApiAuthMeGet();
  return response.data;
}