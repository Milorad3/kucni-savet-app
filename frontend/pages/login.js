import { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api, saveToken } from "../lib/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const res = await api.login({ email, password });
      saveToken(res.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Kućni Savet</h1>
      <p>Prijavite se na svoj nalog</p>
      <div className="card">
        <form onSubmit={handleSubmit}>
          {error && <div className="error">{error}</div>}
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Lozinka"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Prijavi se</button>
        </form>
      </div>
      <p>
        Nemate nalog? <Link href="/register">Registrujte se</Link>
      </p>
    </div>
  );
}
