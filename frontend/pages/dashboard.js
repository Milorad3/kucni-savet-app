import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api, logout, isLoggedIn } from "../lib/api";

export default function Dashboard() {
  const [meetings, setMeetings] = useState([]);
  const [user, setUser] = useState(null);
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
      const me = await api.me();
      setUser(me);

      // company_admin ima svoj poseban dashboard sa svim zgradama
      if (me.role === "company_admin" && me.company_id) {
        router.replace(`/companies/${me.company_id}`);
        return;
      }

      const meetingsList = await api.listMeetings();
      setMeetings(meetingsList);
    } catch (err) {
      setError(err.message);
    }
  }

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <div className="container">
      <h1>Sastanci</h1>
      {user && <p>Zdravo, {user.full_name} ({user.role === "admin" ? "predsednik saveta" : "stanar"})</p>}
      {error && <div className="error">{error}</div>}

      {!user?.building_id && !user?.company_id && (
        <div className="card">
          <p>Niste pridruženi nijednoj zgradi ili firmi.</p>
          <Link href="/buildings/new"><button>Vodim jednu zgradu</button></Link>
          <br />
          <Link href="/companies/new"><button className="secondary">Vodim firmu koja upravlja sa više zgrada</button></Link>
        </div>
      )}

      {user?.role === "admin" && (
        <Link href="/meetings/new">
          <button style={{ marginBottom: 16 }}>+ Novi sastanak</button>
        </Link>
      )}

      {meetings.map((m) => (
        <Link key={m.id} href={`/meetings/${m.id}`}>
          <div className="card">
            <span className={`badge ${m.status}`}>{m.status}</span>
            <h3>{m.title}</h3>
            <p>{new Date(m.scheduled_at).toLocaleString("sr-RS")}</p>
          </div>
        </Link>
      ))}

      {meetings.length === 0 && <p>Nema zakazanih sastanaka.</p>}

      <button className="secondary" onClick={handleLogout}>Odjavi se</button>
    </div>
  );
}
