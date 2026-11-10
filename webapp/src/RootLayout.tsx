import './RootLayout.css';
import { Outlet } from 'react-router-dom';
import { useCurrentUser } from './core/useCurrentUser';

function RootLayout() {
  const {user, logoutFn} = useCurrentUser();

  return (
    <div className="app">
      <header className="app__bar">
        <span className="app__brand">EY Todo</span>        
        {user && (
        <div>
          <span>{user.username}</span>
          <button onClick={logoutFn}>Log out</button>
        </div>
        )}
      </header>
      <main className="app__main">
        <Outlet />
      </main>
    </div>
  );
}

export default RootLayout;
