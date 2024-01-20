import Button from '../Button/Button';
import './App.module.css';

function App() {
  return (
    <>
      <header>
        <h1>webdevcamp</h1>
      </header>
      <main>
        <p>Welcome! Please log in.</p>
        <Button>Log in</Button>
        <Button>Register</Button>
      </main>
      <footer>
        <a href="https://github.com/lachlanshoesmith/webdevcamp">GitHub</a>
        <p>
          By <a href="https://github.com/lachlanshoesmith">Lachlan Shoesmith</a>
        </p>
      </footer>
    </>
  );
}

export default App;
