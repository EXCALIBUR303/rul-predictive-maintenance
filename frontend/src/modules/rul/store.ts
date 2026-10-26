import { create } from "zustand";
export type View =
  "Fleet overview" | "Engine detail" | "Model arena" | "Dataset explorer";
type State = {
  view: View;
  engine: number;
  cycle: number;
  playing: boolean;
  speed: number;
  theme: "dark" | "light";
  navigate: (view: View) => void;
  select: (engine: number, cycle: number) => void;
  setCycle: (cycle: number) => void;
  setPlaying: (playing: boolean) => void;
  setSpeed: (speed: number) => void;
  toggleTheme: () => void;
};
export const useRul = create<State>((set) => ({
  view: "Fleet overview",
  engine: 1,
  cycle: 120,
  playing: false,
  speed: 1,
  theme: "dark",
  navigate: (view) => set({ view, playing: false }),
  select: (engine, cycle) =>
    set({ engine, cycle, view: "Engine detail", playing: false }),
  setCycle: (cycle) => set({ cycle }),
  setPlaying: (playing) => set({ playing }),
  setSpeed: (speed) => set({ speed }),
  toggleTheme: () =>
    set((s) => ({ theme: s.theme === "dark" ? "light" : "dark" })),
}));
