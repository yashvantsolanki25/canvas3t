import { useEffect, useState } from "react";
import { loadNativeWasm, loadFallbackWasm, NormalizedWasm } from "../wasm/bridge";

export const useWasmTools = () => {
  const [bindings, setBindings] = useState<NormalizedWasm | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const wasm = await loadNativeWasm();
        setBindings(wasm);
      } catch (err) {
        console.warn("WASM failed, using fallback", err);
        const fallback = await loadFallbackWasm();
        setBindings(fallback);
        setError("Running in fallback mode");
      }
    };
    load();
  }, []);

  return { bindings, error };
};

