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
    const formData = new FormData();
    formData.set("username", values.username);
    formData.set("password", values.password);

    const result = await action(values);
    if (result && result.error) setServerError(result.error);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {serverError !== null ? <span>{serverError}</span> : null}
      
      <label>
        <span>Username</span>
        <input {...register("username")}/>
        {errors?.username ? <span>{errors.username?.message}</span> : null}
      </label>
      
      <label>
        <span>Password</span>
        <input type="password" {...register("password")} />
        {errors?.password ? <span>{errors.password?.message}</span> : null}
      </label>
      
      <button type="submit" disabled={isSubmitting}>Submit</button>
    </form>
  )
}