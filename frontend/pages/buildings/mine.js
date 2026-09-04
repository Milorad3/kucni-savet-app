import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api, isLoggedIn } from "../../lib/api";

export default function MyBuildings() {
  const [buildings, setBuildings] = useState([]);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    load();
  }, []);

  async function load() {
    try {
      const list = await api.listMyBuildings();
      setBuildings(list);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Moje zgrade</h1>
      <p>Sve zgrade koje vodite kao predsednik/predsednica saveta.</p>
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
          <Link href={`/buildings/${b.id}/apartments`}>
            <button className="secondary">Upravljaj stanovima</button>
          </Link>
        </div>
      ))}

      <Link href="/buildings/new">
        <button className="secondary">+ Dodaj još jednu zgradu</button>
      </Link>
    </div>
  );
}
