import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api, isLoggedIn } from "../../../lib/api";

export default function BuildingApartments() {
  const router = useRouter();
  const { id } = router.query;

  const [building, setBuilding] = useState(null);
  const [apartments, setApartments] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [apartmentNumber, setApartmentNumber] = useState("");
  const [ownershipPercentage, setOwnershipPercentage] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    if (!id) return;
    load();
  }, [id]);

  async function load() {
    try {
      const [b, apts] = await Promise.all([api.getBuilding(id), api.listApartments(id)]);
      setBuilding(b);
      setApartments(apts);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAddApartment(e) {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      await api.addApartment(id, {
        apartment_number: apartmentNumber,
        ownership_percentage: parseFloat(ownershipPercentage),
        owner_email: ownerEmail || undefined,
      });
      setSuccess(
        ownerEmail
          ? `Stan ${apartmentNumber} dodat, povezan sa ${ownerEmail}.`
          : `Stan ${apartmentNumber} dodat (bez vlasnika za sada).`
      );
      setApartmentNumber("");
      setOwnershipPercentage("");
      setOwnerEmail("");
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  const totalOwnership = apartments.reduce((sum, a) => sum + a.ownership_percentage, 0);

  return (
    <div className="container">
      <h1>Stanovi{building ? ` — ${building.name}` : ""}</h1>
      <p>
        Ovde dodajete stanove i njihove vlasnike. Vlasnik MORA prethodno da se registruje u aplikaciji
        (svojim email-om) da bi mogao da mu se dodeli stan i pravo glasa.
      </p>

      {error && <div className="error">{error}</div>}
      {success && (
        <div style={{ color: "#065f46", background: "#d1fae5", padding: "8px 12px", borderRadius: 8, marginBottom: 10, fontSize: 14 }}>
          {success}
        </div>
      )}

      <div className="card">
        <form onSubmit={handleAddApartment}>
          <h3>Dodaj stan</h3>
          <input
            placeholder="Broj stana (npr. 12 ili 3a)"
            value={apartmentNumber}
            onChange={(e) => setApartmentNumber(e.target.value)}
            required
          />
          <input
            type="number"
            step="0.01"
            min="0"
            max="100"
            placeholder="Procenat vlasništva (npr. 2.5)"
            value={ownershipPercentage}
            onChange={(e) => setOwnershipPercentage(e.target.value)}
            required
          />
          <input
            type="email"
            placeholder="Email vlasnika (opciono - može se dodati kasnije)"
            value={ownerEmail}
            onChange={(e) => setOwnerEmail(e.target.value)}
          />
          <button type="submit">Dodaj stan</button>
        </form>
      </div>

      <h3>
        Postojeći stanovi ({apartments.length})
        {apartments.length > 0 && (
          <span style={{ fontWeight: 400, fontSize: 14, color: totalOwnership > 100 ? "#dc2626" : "#666" }}>
            {" "}— ukupno vlasništvo: {totalOwnership.toFixed(2)}%
            {totalOwnership > 100 && " (⚠️ prelazi 100%, proveri unos)"}
          </span>
        )}
      </h3>

      {apartments.map((a) => (
        <div key={a.id} className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>Stan {a.apartment_number}</strong>
            <p style={{ margin: "4px 0 0 0", fontSize: 13, color: "#666" }}>
              {a.ownership_percentage}% vlasništva
            </p>
          </div>
          <span className={`badge ${a.owner_id ? "active" : "scheduled"}`}>
            {a.owner_id ? "Vlasnik dodeljen" : "Bez vlasnika"}
          </span>
        </div>
      ))}

      {apartments.length === 0 && <p>Još nema dodatih stanova.</p>}

      <Link href="/dashboard">
        <button className="secondary">← Nazad na sastanke</button>
      </Link>
    </div>
  );
}
