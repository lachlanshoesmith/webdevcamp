import { useRouteError } from 'react-router-dom';
import '../index.css';

function ErrorPage() {
  const error: any = useRouteError();
  console.error(error);

  return (
    <div id="errorPage">
      <h1>There was an error.</h1>
      <p>{error.statusText || error.message}</p>
    </div>
  );
}

export default ErrorPage;
