import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabaseClient";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const date = searchParams.get("date") || new Date().toISOString().slice(0, 10);

  const { data, error } = await supabase
    .from("appointments")
    .select("*")
    .eq("appointment_date", date)
    .order("appointment_date", { ascending: true });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ appointments: data ?? [] });
}
