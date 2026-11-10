import { meApiAuthMeGet } from "../api"

export const hasAuth = async (): Promise<Boolean> => {
  const response = await meApiAuthMeGet();
  return !response.error
}