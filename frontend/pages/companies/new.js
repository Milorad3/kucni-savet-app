import { useState } from "react";
import { useRouter } from "next/router";
import { api } from "../../lib/api";

export default function NewCompany() {
  const [name, setName] = useState("");
  const [pib, setPib] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const company = await api.createCompany({ name, pib });
      router.push(`/companies/${company.id}`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Registracija firme</h1>
      <p>Za firme koje upravljaju sa više zgrada.</p>
      <div className="card">
        <form onSubmit={handleSubmit}>
          {error && <div className="error">{error}</div>}
          <input placeholder="Naziv firme" value={name} onChange={(e) => setName(e.target.value)} required />
          <input placeholder="PIB (opciono)" value={pib} onChange={(e) => setPib(e.target.value)} />
          <button type="submit">Registruj firmu</button>
        </form>
      </div>
    </div>
  );
}
