import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import type { RegisterBody } from '../api';
import { zRegisterBody } from '../api/zod.gen';
import { useState } from 'react';

export function LoginForm({action}: {
  action : (data: RegisterBody) => Promise<{ error: string } | null>
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterBody>({
    resolver: zodResolver(zRegisterBody),
    defaultValues: { username: "", password: "" },
  });

  const [serverError, setServerError] = useState<string | null>(null);

  async function onSubmit(values: RegisterBody) {
    setServerError(null);
    const result = await action(values);
    if (result) setServerError(result.error);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {serverError !== null && <span className="error-message">{serverError}</span>}
      
      <label>
        <span>Username</span>
        <input {...register("username")}/>
        {errors?.username && <span>{errors.username?.message}</span>}
      </label>
      
      <label>
        <span>Password</span>
        <input type="password" {...register("password")} />
        {errors?.password && <span>{errors.password?.message}</span>}
      </label>
      
      <button type="submit" disabled={isSubmitting}>Submit</button>
    </form>
  )
}