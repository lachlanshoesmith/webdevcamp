import Button from '../components/Button/Button';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useState } from 'react';

type Inputs = {
  given_name: string;
  family_name: string;
  username: string;
  hashed_password: string;
  account_type: string;
  email: string;
  phone_number: string;
};

export default function Register() {
  const {
    register,
    formState: { errors },
    handleSubmit,
  } = useForm<Inputs>();
  const [registerErrors, setRegisterErrors] = useState('');

  const onSubmit: SubmitHandler<Inputs> = async (data) => {
    data.account_type = 'administrator';
    const res = await fetch('https://webdevcamp.fly.dev/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    const responseJSON = await res.json();

    if (!res.ok) {
      setRegisterErrors(responseJSON.detail);
    } else {
      console.log(res.json());
    }
  };
  return (
    <>
      <h1>Register new administrator</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input
          type="text"
          {...register('given_name', {
            required: true,
          })}
          aria-invalid={errors.given_name ? 'true' : 'false'}
          placeholder="Given name"
        />
        <input
          type="text"
          {...register('family_name', {
            required: true,
          })}
          aria-invalid={errors.family_name ? 'true' : 'false'}
          placeholder="Family name"
        />
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
          {...register('hashed_password', {
            required: true,
            minLength: 8,
          })}
          aria-invalid={errors.hashed_password ? 'true' : 'false'}
          placeholder="Password"
        />
        <input
          type="email"
          {...register('email', {
            required: true,
          })}
          aria-invalid={errors.email ? 'true' : 'false'}
          placeholder="Email"
        />
        <input
          type="text"
          {...register('phone_number', {
            required: false,
          })}
          aria-invalid={errors.phone_number ? 'true' : 'false'}
          placeholder="Phone number"
        />
        <Button type="submit">Register</Button>
      </form>
      {registerErrors && <p>{registerErrors}</p>}
    </>
  );
}
