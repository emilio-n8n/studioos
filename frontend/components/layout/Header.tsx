"use client";

interface Props {
  title?: string;
}

export default function Header({ title }: Props) {
  return (
    <header className="border-b border-zinc-200 bg-white px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-zinc-900">StudioOS</h1>
          {title && (
            <>
              <span className="text-zinc-300">/</span>
              <span className="text-sm text-zinc-500">{title}</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
