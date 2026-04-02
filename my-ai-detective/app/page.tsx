"use client";

import { useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, User, Search, Brain, Activity, FileUp } from "lucide-react";

// Твои новые компоненты
import { Card } from "../src/ui/Card";
import { Input } from "../src/ui/Input";
import { Button } from "../src/ui/Button";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return alert("Бейбарыс, прикрепи файл!");

    setLoading(true);
    const data = new FormData();
    data.append("candidate_name", name);
    data.append("file", file);

    try {
      // Запрос к твоему FastAPI бэкенду
      const res = await axios.post("http://127.0.0.1:8000/analyze", data);
      setResult(res.data);
    } catch (err) {
      alert("Ошибка: Бэкенд не запущен или CORS заблокирован.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#030406] text-slate-300 p-6 md:p-12 selection:bg-blue-500/30">
      {/* Эффект свечения на фоне */}
      <div className="fixed top-0 right-0 w-[60%] h-[60%] bg-blue-600/5 blur-[140px] rounded-full -z-10" />

      <div className="max-w-6xl mx-auto">
        <header className="flex flex-col items-center mb-20 text-center">
          <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="p-3 bg-blue-600/10 border border-blue-500/20 rounded-2xl mb-6">
            <ShieldCheck className="text-blue-500" size={32} />
          </motion.div>
          <h1 className="text-7xl font-black text-white tracking-tighter mb-4">
            InVision <span className="text-blue-600">U</span>
          </h1>
          <p className="text-slate-500 uppercase tracking-[0.3em] text-[10px] font-bold">AI Verification Protocol v1.0</p>
        </header>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* СЕКЦИЯ ВВОДА */}
          <motion.div initial={{ x: -30, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
            <Card title="Параметры объекта" icon={Search}>
              <form onSubmit={handleStartAnalysis} className="space-y-8">
                <Input label="ФИО Кандидата" icon={User} placeholder="Напр: Арманулы Бейбарыс" value={name} onChange={(e:any) => setName(e.target.value)} required />
                
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1 flex items-center gap-2">
                    <FileUp size={12} className="text-blue-500" /> Цифровой оттиск (PDF)
                  </label>
                  <div className="relative group border-2 border-dashed border-slate-800 rounded-3xl p-10 text-center hover:border-blue-500/40 transition-all bg-slate-950/20">
                    <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                    <p className="text-sm font-bold text-slate-400 group-hover:text-blue-400">
                      {file ? file.name : "ПЕРЕТАЩИТЕ ФАЙЛ СЮДА"}
                    </p>
                  </div>
                </div>

                <Button loading={loading}>Запустить анализ</Button>
              </form>
            </Card>
          </motion.div>

          {/* СЕКЦИЯ РЕЗУЛЬТАТОВ */}
          <motion.div initial={{ x: 30, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
            <AnimatePresence mode="wait">
              {result ? (
                <Card title="Результат сканирования" icon={Brain}>
                  <div className="space-y-8">
                    <div className="bg-blue-600/5 border-l-2 border-blue-600 p-6 rounded-r-2xl italic text-sm leading-relaxed text-blue-100/80">
                      "{result.ai_report}"
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      {Object.entries(result.ai_extracted_scores || {}).map(([key, val]: any) => (
                        <div key={key} className="bg-slate-900/60 border border-slate-800 p-5 rounded-3xl text-center">
                          <p className="text-[9px] text-slate-500 font-black uppercase tracking-tighter mb-1">{key}</p>
                          <p className="text-3xl font-black text-white">{val}<span className="text-xs text-slate-600">/10</span></p>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              ) : (
                <div className="h-[480px] border-2 border-dashed border-slate-900 rounded-[2.5rem] flex flex-col items-center justify-center p-12 text-slate-800 bg-slate-900/5">
                  <Activity size={64} className="mb-6 opacity-20 animate-pulse" />
                  <p className="text-[10px] font-black uppercase tracking-[0.4em]">Система в режиме ожидания</p>
                </div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </main>
  );
}