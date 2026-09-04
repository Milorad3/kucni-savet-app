import { useState } from "react";
import { useRouter } from "next/router";
import { api } from "../../lib/api";

export default function NewBuilding() {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const building = await api.createBuilding({ name, address });
      // Logican sledeci korak posle kreiranja zgrade je odmah dodavanje stanova,
      // ne prazan dashboard.
      router.push(`/buildings/${building.id}/apartments`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Nova zgrada</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          {error && <div className="error">{error}</div>}
          <input placeholder="Naziv zgrade" value={name} onChange={(e) => setName(e.target.value)} required />
          <input placeholder="Adresa" value={address} onChange={(e) => setAddress(e.target.value)} required />
          <button type="submit">Kreiraj</button>
        </form>
      </div>
    </div>
  );
}
