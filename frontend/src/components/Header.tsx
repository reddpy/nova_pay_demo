"use client";

import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";

export function Header() {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const check = async () => {
      const healthy = await checkHealth();
      setIsConnected(healthy);
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold text-gray-900">
          NovaPay Docs Portal
        </h1>
        <span className="px-2 py-0.5 text-xs font-medium text-nova-700 bg-nova-50 rounded-full border border-nova-200">
          Internal Engineering Knowledge Base
        </span>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? "bg-emerald-500" : "bg-red-400"
            }`}
          />
          <span>{isConnected ? "Connected" : "Disconnected"}</span>
        </div>
        <span className="text-xs text-gray-400">
          Powered by LangChain
        </span>
      </div>
    </header>
  );
}
