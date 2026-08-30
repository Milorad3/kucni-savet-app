import { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api, saveToken } from "../lib/api";

export default function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.register({ full_name: fullName, email, password });
      const res = await api.login({ email, password });
      saveToken(res.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Registracija</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          {error && <div className="error">{error}</div>}
          <input
            placeholder="Ime i prezime"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Lozinka (min. 8 karaktera)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <button type="submit">Registruj se</button>
        </form>
      </div>
      <p>
        Već imate nalog? <Link href="/login">Prijavite se</Link>
      </p>
    </div>
  );
}
