import { ReactNode } from "react";

export const Card = ({ children, title, icon: Icon }: { children: ReactNode; title?: string; icon?: any }) => (
  <div className="relative bg-slate-900/40 backdrop-blur-xl border border-slate-800 p-8 rounded-[2.5rem] shadow-2xl transition-all hover:border-blue-500/30">
    {title && (
      <div className="flex items-center gap-4 mb-8">
        {Icon && (
          <div className="p-3 bg-blue-600/10 rounded-2xl text-blue-500">
            <Icon size={24} />
          </div>
        )}
        <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
      </div>
    )}
    {children}
  </div>
);