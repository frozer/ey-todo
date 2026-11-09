import { createBrowserRouter, redirect } from "react-router-dom";
import RootLayout from "./RootLayout";
import { hasAuth } from "./shared/hasAuth";
import { LoginPage } from "./login/page";

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    loader: async () => {
      const x = await hasAuth();
      if (!x) throw redirect('/login');
    }
  },
  { path: 'login', element: <LoginPage /> }
]);