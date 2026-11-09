import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import type { Todo, TodoCreate } from "../../api";
import { zTodoCreate } from "../../api/zod.gen";
import type { ReactNode } from "react";

export function TodoForm({onSubmit, children, item}: {
  onSubmit : (data: TodoCreate) => void
  children: ReactNode,
  item?: Todo | null
}) {
  const { label = '', status = '', text = '' } = item || {};
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TodoCreate>({
    resolver: zodResolver(zTodoCreate),
    defaultValues: { label, status, text },
  });


  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("label")} placeholder="Add title"/>
      {errors?.label ? <span>{errors.label?.message}</span> : null}
      
      <label>
        <span>Description</span>
        <textarea {...register("text")} />
      </label>

      {children}
    </form>
  )
}