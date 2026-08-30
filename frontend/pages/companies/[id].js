import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api } from "../../lib/api";

export default function CompanyDashboard() {
  const router = useRouter();
  const { id } = router.query;
  const [buildings, setBuildings] = useState([]);
  const [error, setError] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");

  useEffect(() => {
    if (!id) return;
    load();
  }, [id]);

  async function load() {
    try {
      const list = await api.listCompanyBuildings(id);
      setBuildings(list);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAddBuilding(e) {
    e.preventDefault();
    setError("");
    try {
      await api.addCompanyBuilding(id, { name, address });
      setName("");
      setAddress("");
      setShowAddForm(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Sve zgrade</h1>
      <p>Pregled svih zgrada koje vaša firma upravlja — jedno mesto za sve sastanke i glasanja.</p>
      {error && <div className="error">{error}</div>}

      {buildings.map((b) => (
        <div key={b.id} className="card">
          <h3>{b.name}</h3>
          <p>{b.address}</p>
          <p style={{ fontSize: 13, color: "#666" }}>
            {b.apartment_count} stanova · {b.upcoming_meeting_count} otvorenih/zakazanih sastanaka
          </p>
          <Link href={`/meetings/new?building_id=${b.id}`}>
            <button>+ Novi sastanak za ovu zgradu</button>
          </Link>
        </div>
      ))}

      {buildings.length === 0 && !showAddForm && <p>Još nemate dodatih zgrada.</p>}

      {showAddForm ? (
        <div className="card">
          <form onSubmit={handleAddBuilding}>
            <input placeholder="Naziv zgrade" value={name} onChange={(e) => setName(e.target.value)} required />
            <input placeholder="Adresa" value={address} onChange={(e) => setAddress(e.target.value)} required />
            <button type="submit">Dodaj zgradu</button>
          </form>
        </div>
      ) : (
        <button onClick={() => setShowAddForm(true)}>+ Dodaj novu zgradu</button>
      )}
    </div>
  );
}
