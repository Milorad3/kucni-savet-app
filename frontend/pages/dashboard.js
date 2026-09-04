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

      // admin (predsednik) koji vodi VISE zgrada takodje ide na pregled liste,
      // isto kao company_admin - ako vodi samo jednu, ostaje na ovom (jednostavnijem) ekranu
      if (me.role === "admin") {
        const myBuildings = await api.listMyBuildings();
        if (myBuildings.length > 1) {
          router.replace("/buildings/mine");
          return;
        }
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
      {user && (
        <p>
          Zdravo, {user.full_name}
          {user.role === "admin" && " (predsednik saveta)"}
          {user.role === "resident" && user.building_id && " (stanar)"}
        </p>
      )}
      {error && <div className="error">{error}</div>}

      {!user?.building_id && !user?.company_id && (
        <div className="card">
          <p>
            <strong>Još niste dodati ni u jednu zgradu.</strong><br />
            Ako čekate da vas predsednik ili upravnik doda kao vlasnika stana, javite im svoj email
            (<em>{user?.email}</em>) da vas povežu. Ili, ako ste vi taj koji vodi zgradu/firmu:
          </p>
          <Link href="/buildings/new"><button>Vodim jednu zgradu</button></Link>
          <br />
          <Link href="/companies/new"><button className="secondary">Vodim firmu koja upravlja sa više zgrada</button></Link>
        </div>
      )}

      {user?.role === "admin" && (
        <Link href="/meetings/new">
          <button style={{ marginBottom: 8 }}>+ Novi sastanak</button>
        </Link>
      )}
      {user?.role === "admin" && (
        <Link href="/buildings/new">
          <button className="secondary" style={{ marginBottom: 16 }}>+ Vodim još jednu zgradu</button>
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
