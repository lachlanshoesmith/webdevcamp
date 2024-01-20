import { Form } from 'react-router-dom';
import Button from '../components/Button/Button';

function login() {
  return (
    <>
      <h1>Login Page</h1>
      <Form method="get">
        <Button type="submit">Login</Button>
      </Form>
    </>
  );
}

export default login;
