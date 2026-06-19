import { Link, useLocation } from "react-router-dom";
import SearchBar from "./SearchBar";
import AuthPanel from "./AuthPanel";

type Props = {
  children: React.ReactNode;
};

const AppShell = ({ children }: Props) => {
  const location = useLocation();
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <div className="app-shell__brand-row">
          <Link to="/gallery" className="brand">
            Canvas3T
          </Link>
          <nav className="app-shell__nav">
            <Link
              to="/gallery"
              className={location.pathname.startsWith("/gallery") ? "active" : ""}
            >
              Gallery
            </Link>
            <Link
              to="/editor"
              className={location.pathname.startsWith("/editor") ? "active" : ""}
            >
              Editor
            </Link>
          </nav>
        </div>
        <div className="app-shell__tools">
          <SearchBar />
          <AuthPanel />
        </div>
      </header>
      <main className="app-shell__main">{children}</main>
    </div>
  );
};

export default AppShell;

