import Button from '../components/Button/Button';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useState } from 'react';

type Inputs = {
  username: string;
  password: string;
};

export default function Login() {
  const {
    register,
    formState: { errors },
    handleSubmit,
  } = useForm<Inputs>();
  const [loginErrors, setLoginErrors] = useState('');

  const onSubmit: SubmitHandler<Inputs> = async (data) => {
    const res = await fetch('https://webdevcamp.fly.dev/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    const responseJSON = await res.json();
    const responseDetail: string = responseJSON.detail;

    if (!res.ok) {
      setLoginErrors(responseDetail);
    } else {
      console.log(responseDetail);
    }
  };
  return (
    <>
      <h1>Login Page</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input
          type="text"
          {...register('username', {
            required: true,
            minLength: 3,
            maxLength: 20,
          })}
          aria-invalid={errors.username ? 'true' : 'false'}
          placeholder="Username"
        />
        <input
          type="password"
          {...register('password', {
            required: true,
            minLength: 8,
          })}
          aria-invalid={errors.password ? 'true' : 'false'}
          placeholder="Password"
        />
        <Button type="submit">Login</Button>
      </form>
      {loginErrors && <p>{loginErrors}</p>}
    </>
  );
}
