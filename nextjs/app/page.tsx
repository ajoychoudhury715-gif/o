import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
      <h1>The Dental Bond (Next.js)</h1>
      <p>
        This is a starter migration from the original Streamlit app to Next.js.
      </p>
      <ul>
        <li>
          <Link href="/scheduling">Scheduling overview</Link>
        </li>
      </ul>
      <small>
        Use environment variables <code>NEXT_PUBLIC_SUPABASE_URL</code> and
        <code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code>.
      </small>
    </main>
  );
}
