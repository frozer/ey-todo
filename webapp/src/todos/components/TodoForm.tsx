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
    <form className="flex flex-col gap-4 rounded-lg border border-line bg-surface p-4 sm:p-6" onSubmit={handleSubmit(onSubmit)}>
      <div className="field">
        <input className="input text-base font-medium" {...register("label")} placeholder="Add title"/>
        {errors?.label && <span className="field-error">{errors.label?.message}</span>}
      </div>

      <label className="field">
        <span>Description</span>
        <textarea className="input min-h-32 resize-y" {...register("text")} />
      </label>

      {children}
    </form>
  )
}