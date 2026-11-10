import { Outlet } from 'react-router-dom';
import { useCurrentUser } from './core/useCurrentUser';

function RootLayout() {
  const {user, logoutFn} = useCurrentUser();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between gap-4 border-b border-line bg-surface px-4 py-3 sm:px-5">
        <span className="font-bold tracking-wide">EY Todo</span>
        {user && (
        <div className="flex items-center gap-3 text-sm">
          <span className="hidden text-muted sm:inline">{user.username}</span>
          <button type="button" className="btn" onClick={logoutFn}>Log out</button>
        </div>
        )}
      </header>
      <main className="flex flex-1 justify-center px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export default RootLayout;
