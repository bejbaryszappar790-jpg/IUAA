export const Input = ({ label, icon: Icon, ...props }: any) => (
  <div className="space-y-3 w-full">
    <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1 flex items-center gap-2">
      {Icon && <Icon size={12} className="text-blue-500" />} {label}
    </label>
    <input 
      {...props}
      className="w-full bg-slate-950/50 border border-slate-800 rounded-2xl p-4 text-white placeholder:text-slate-700 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/50 transition-all font-medium"
    />
  </div>
);