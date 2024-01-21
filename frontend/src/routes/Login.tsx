import Button from '../components/Button/Button';
import { useForm, SubmitHandler } from 'react-hook-form';

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
  const onSubmit: SubmitHandler<Inputs> = (data) => {
    fetch('https://webdevcamp.fly.dev/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }).then((res) => {
      console.log(res.status);
      if (res.ok) console.log(res.json());
    });
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
          {...(register('password'),
          {
            required: true,
            minLength: 8,
          })}
          aria-invalid={errors.password ? 'true' : 'false'}
          placeholder="Password"
        />
        <Button type="submit">Login</Button>
      </form>
    </>
  );
}
