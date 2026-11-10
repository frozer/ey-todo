import { useNavigate, useRouteLoaderData } from 'react-router-dom';
import { logoutApiAuthLogoutPost, type MeResponse } from '../api';

type RootLoaderData = {
  user: MeResponse;
};

export function useCurrentUser(): {user: MeResponse, logoutFn: () => void} {
  const navigate = useNavigate();
  const data = useRouteLoaderData('root') as RootLoaderData | undefined;

  const logoutFn = async () => {
    await logoutApiAuthLogoutPost();
    navigate('/login', { replace: true });
  };

  if (!data) {
    throw new Error('Root route loader data is unavailable');
  }

  return {user: data.user, logoutFn};
}