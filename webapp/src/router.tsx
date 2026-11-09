import { createBrowserRouter, redirect } from "react-router-dom";
import RootLayout from "./RootLayout";
import { hasAuth } from "./shared/hasAuth";
import { LoginPage } from "./login/page";
import { TodosPage } from "./todos/todos.page";
import { TodoPage } from "./todos/todo.page";

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    loader: async () => {
      const x = await hasAuth();
      if (!x) throw redirect('/login');
    },
    children: [
      { index: true, element: <TodosPage /> },
      { path: 'todo', element: <TodoPage /> }
    ]
  },
  { path: 'login', element: <LoginPage /> }
]);