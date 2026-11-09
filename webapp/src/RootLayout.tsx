import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './RootLayout.css';
import { Outlet } from 'react-router-dom';

const queryClient = new QueryClient()

/**
 * Day 2 — the SettingsProvider wraps the whole app, so anything underneath can
 * `useSettings()`. The header's <FeedStatus> and the Marketwatch tiles are
 * cousins reading the same context from different subtrees — the case Context
 * is built for.
 */
function RootLayout() {
 
  return (
    <QueryClientProvider client={queryClient}>     
        <div className="app">
          <header className="app__bar">
            <span className="app__brand">EY Todo</span>
          </header>
          <main className="app__main">
            <Outlet />
          </main>
        </div>
    </QueryClientProvider>
  );
}

export default RootLayout;
