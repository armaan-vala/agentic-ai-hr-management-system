import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

// A single shared client. Auth session is persisted in localStorage by default.
export const supabase = createClient(url ?? "", anonKey ?? "");
