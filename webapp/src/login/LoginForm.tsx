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
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      {serverError !== null && <span className="error-message">{serverError}</span>}

      <label className="field">
        <span>Username</span>
        <input className="input" autoComplete="username" {...register("username")}/>
        {errors?.username && <span className="field-error">{errors.username?.message}</span>}
      </label>

      <label className="field">
        <span>Password</span>
        <input className="input" type="password" autoComplete="current-password" {...register("password")} />
        {errors?.password && <span className="field-error">{errors.password?.message}</span>}
      </label>

      <button type="submit" className="btn btn-primary w-full" disabled={isSubmitting}>Submit</button>
    </form>
  )
}