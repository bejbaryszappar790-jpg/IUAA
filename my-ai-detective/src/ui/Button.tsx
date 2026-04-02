import { Loader2 } from "lucide-react";

export const Button = ({ children, loading, ...props }: any) => (
  <button 
    {...props}
    disabled={loading}
    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black py-5 rounded-2xl transition-all shadow-[0_0_20px_rgba(37,99,235,0.15)] disabled:opacity-50 flex items-center justify-center gap-3 uppercase text-xs tracking-widest"
  >
    {loading ? <Loader2 className="animate-spin" size={18} /> : children}
  </button>
);