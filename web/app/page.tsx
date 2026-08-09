"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_FLOWPROOF_API || "https://flowproof.specvista.com";

type Key = { id: number; label: string; prefix: string; created_at: number };

export default function Dashboard() {
  const [session, setSession] = useState<string | null>(null);
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [keys, setKeys] = useState<Key[]>([]);
  const [label, setLabel] = useState("");
  const [freshKey, setFreshKey] = useState("");

  useEffect(() => {
    const s = typeof window !== "undefined" ? localStorage.getItem("fp_session") : null;
    if (s) setSession(s);
  }, []);

  const loadKeys = useCallback(async (token: string) => {
    const res = await fetch(`${API}/auth/keys`, {
      headers: { authorization: `Bearer ${token}` },
    });
    if (res.ok) setKeys((await res.json()).keys);
  }, []);

  useEffect(() => {
    if (session) loadKeys(session);
  }, [session, loadKeys]);

  async function submitAuth(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const res = await fetch(`${API}/auth/${mode}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "Something went wrong");
      return;
    }
    localStorage.setItem("fp_session", data.session);
    setSession(data.session);
  }

  async function createKey(e: React.FormEvent) {
    e.preventDefault();
    setFreshKey("");
    const res = await fetch(`${API}/auth/keys`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${session}` },
      body: JSON.stringify({ label: label || "key" }),
    });
    const data = await res.json();
    if (res.ok) {
      setFreshKey(data.key);
      setLabel("");
      loadKeys(session!);
    }
  }

  async function revoke(id: number) {
    await fetch(`${API}/auth/keys/${id}`, {
      method: "DELETE",
      headers: { authorization: `Bearer ${session}` },
    });
    loadKeys(session!);
  }

  function signOut() {
    localStorage.removeItem("fp_session");
    setSession(null);
    setKeys([]);
  }

  if (!session) {
    return (
      <div className="wrap">
        <div className="brand">FlowProof</div>
        <div className="tag">Reproducible bioinformatics pipelines, run from your AI assistant.</div>
        <div className="panel">
          <h2>{mode === "login" ? "Sign in" : "Create account"}</h2>
          <form onSubmit={submitAuth}>
            <label>Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
            <label>Password</label>
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
            <button type="submit">{mode === "login" ? "Sign in" : "Sign up"}</button>
          </form>
          {error && <div className="error">{error}</div>}
          <div style={{ marginTop: 16 }}>
            <button
              className="link"
              onClick={() => setMode(mode === "login" ? "signup" : "login")}
            >
              {mode === "login" ? "Need an account? Sign up" : "Have an account? Sign in"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="wrap">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div className="brand">FlowProof</div>
          <div className="tag">Your access keys</div>
        </div>
        <button className="ghost" onClick={signOut}>
          Sign out
        </button>
      </div>

      <div className="panel">
        <h2>Create a key</h2>
        <form onSubmit={createKey}>
          <label>Label (e.g. laptop, ci)</label>
          <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="laptop" />
          <button type="submit">Generate key</button>
        </form>
        {freshKey && (
          <>
            <div className="tag" style={{ marginTop: 16 }}>
              Copy this now, it is shown only once:
            </div>
            <div className="token mono">{freshKey}</div>
          </>
        )}
      </div>

      <div className="panel">
        <h2>Active keys</h2>
        {keys.length === 0 && <div className="tag">No keys yet.</div>}
        {keys.map((k) => (
          <div className="key-row" key={k.id}>
            <span>
              <span className="mono">{k.prefix}…</span> · {k.label}
            </span>
            <button className="revoke" onClick={() => revoke(k.id)}>
              Revoke
            </button>
          </div>
        ))}
      </div>

      <div className="panel">
        <h2>Connect your AI client</h2>
        <div className="tag">Add this to your MCP client config, using a key above:</div>
        <pre>{`{
  "mcpServers": {
    "flowproof": {
      "url": "${API}/mcp/",
      "headers": { "Authorization": "Bearer YOUR_KEY" }
    }
  }
}`}</pre>
      </div>
    </div>
  );
}
