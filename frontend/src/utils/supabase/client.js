import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_SUPABASE_URL) ||
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_SUPABASE_URL) ||
  "https://tmjcxhkrfqwmxtspyjwo.supabase.co";

const supabaseKey =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY) ||
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY) ||
  "sb_publishable_pc8znb6TjFvk9CmVS8fJSg_Jk6wczcL";

export const createClient = () =>
  createBrowserClient(supabaseUrl, supabaseKey);

export default createClient;
