import { createBrowserRouter, redirect } from "react-router-dom";
import RootLayout from "./RootLayout";
import { getCurrentUser } from "./core/user.helper";
import { LoginPage } from "./login/page";
import { TodosPage } from "./todos/todos.page";
import { TodoPage } from "./todos/todo.page";

export const router = createBrowserRouter([
  {
    id: 'root',
    path: '/',
    element: <RootLayout />,
    loader: async () => {
      const user = await getCurrentUser();
      if (!user) throw redirect('/login');

      return {
        user
      }
    },
    children: [
      { index: true, element: <TodosPage /> },
      { path: 'todo', element: <TodoPage /> }
    ]
  },
  { path: 'login', element: <LoginPage /> }
]);