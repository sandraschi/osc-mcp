import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export function useKeyboard() {
  const navigate = useNavigate();
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "l") { e.preventDefault(); navigate("/logs"); }
      if (e.ctrlKey && e.key === "h") { e.preventDefault(); navigate("/help"); }
      if (e.ctrlKey && e.key === "k") { e.preventDefault(); navigate("/tools"); }
      if (e.ctrlKey && e.key === "0") {
        e.preventDefault();
        localStorage.setItem("tauri-zoom", "1.0");
        document.documentElement.style.zoom = "1.0";
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate]);
}
