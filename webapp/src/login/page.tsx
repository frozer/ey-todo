import { useNavigate, useSearchParams } from "react-router-dom";
import { loginApiAuthLoginPost, registerApiAuthRegisterPost, type RegisterBody, type HttpValidationError  } from "../api"
import { LoginForm } from "./LoginForm";
import { useState } from "react";
import { isHttpValidationError } from "../core/error.guard";

export function LoginPage(options: {
  redirectTo?: string
}) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [mode, setMode] = useState<'LOGIN'|'REGISTER'>('LOGIN');

  const loginAction = async (body: RegisterBody) => {
      
        const redirectTo = options.redirectTo ?? params.get('from') ?? '/';
        
        const result = mode === 'LOGIN' 
          ? await loginApiAuthLoginPost({body})
          : await registerApiAuthRegisterPost({body})
        
        if (isHttpValidationError(result.error)) {
          return {error: result.error.detail?.map(({msg}) => msg).join() || 'Unknown error'};
        }

        navigate(redirectTo, { replace: true});

        return null;
  }

  return (
    <main>
      <h1>{mode === 'LOGIN' ? 'Log in' : 'Register' }</h1>
      <LoginForm action={loginAction} />
      <button onClick={() => setMode(mode => mode === 'LOGIN' ? 'REGISTER' : 'LOGIN')}>{mode === 'LOGIN' ? 'No account? Sign up!' : 'Already have one? Log in!' }</button>
    </main>
  )
}