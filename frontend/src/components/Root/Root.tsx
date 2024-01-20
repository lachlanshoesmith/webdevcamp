import { Outlet, Link } from 'react-router-dom';
import classes from './Root.module.css';

function Root() {
  return (
    <>
      <nav>
        <h1>webdevcamp</h1>
        <ul className={classes.navItems}>
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/login">Login</Link>
          </li>
          <li>
            <Link to="/register">Register</Link>
          </li>
        </ul>
      </nav>
      <Outlet />
      <footer>
        <a href="https://github.com/lachlanshoesmith/webdevcamp">GitHub</a>
        <p>
          By <a href="https://github.com/lachlanshoesmith">Lachlan Shoesmith</a>
        </p>
      </footer>
    </>
  );
}

export default Root;
