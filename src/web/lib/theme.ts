"use client";

import { useCallback, useEffect, useState } from "react";

export type ThemePreference = "light" | "dark" | "system";
const KEY = "frotas-tema";

function apply(preference: ThemePreference) {
  const dark = preference === "dark" || (preference === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}

export function useTheme() {
  const [preference, setPreference] = useState<ThemePreference>("system");
  useEffect(() => {
    let saved: ThemePreference = "system";
    try { saved = (localStorage.getItem(KEY) as ThemePreference) || "system"; } catch {}
    setPreference(saved); // eslint-disable-line react-hooks/set-state-in-effect
    const media = matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => { try { if ((localStorage.getItem(KEY) || "system") === "system") apply("system"); } catch { apply("system"); } };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);
  const change = useCallback((value: ThemePreference) => {
    setPreference(value);
    try { localStorage.setItem(KEY, value); } catch {}
    apply(value);
  }, []);
  return { preference, change };
}
