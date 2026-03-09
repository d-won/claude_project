import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

const styles = {
  header: {
    background: 'var(--bg-secondary)',
    borderBottom: '1px solid var(--border)',
    padding: '0 24px',
    height: 60,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'sticky' as const,
    top: 0,
    zIndex: 100,
  },
  logo: {
    fontSize: 18,
    fontWeight: 700,
    color: 'var(--accent-blue)',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  nav: {
    display: 'flex',
    gap: 24,
  },
  navLink: {
    color: 'var(--text-secondary)',
    fontSize: 14,
    fontWeight: 500,
    padding: '8px 0',
    borderBottom: '2px solid transparent',
    transition: 'all 0.2s',
  },
  main: {
    maxWidth: 1400,
    margin: '0 auto',
    padding: '24px',
    minHeight: 'calc(100vh - 60px)',
  },
};

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div>
      <header style={styles.header}>
        <Link to="/" style={styles.logo}>
          Financial Analysis Platform
        </Link>
        <nav style={styles.nav}>
          <Link
            to="/"
            style={{
              ...styles.navLink,
              color: isHome ? 'var(--accent-blue)' : undefined,
              borderBottomColor: isHome ? 'var(--accent-blue)' : undefined,
            }}
          >
            Search
          </Link>
        </nav>
      </header>
      <main style={styles.main}>{children}</main>
    </div>
  );
}
