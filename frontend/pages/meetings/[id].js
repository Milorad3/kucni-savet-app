import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { api } from "../../lib/api";

export default function MeetingDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [meeting, setMeeting] = useState(null);
  const [results, setResults] = useState(null);
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [myVotes, setMyVotes] = useState({});

  useEffect(() => {
    if (!id) return;
    load();
  }, [id]);

  async function load() {
    try {
      const [m, me] = await Promise.all([api.getMeeting(id), api.me()]);
      setMeeting(m);
      setUser(me);
      if (m.status === "closed" || m.status === "active") {
        const res = await api.getResults(id);
        setResults(res);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleVote(agendaItemId, choice) {
    setError("");
    try {
      await api.vote(agendaItemId, choice);
      setMyVotes({ ...myVotes, [agendaItemId]: choice });
      const res = await api.getResults(id);
      setResults(res);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleActivate() {
    await api.activateMeeting(id);
    load();
  }

  async function handleClose() {
    if (!confirm("Sigurno zatvoriti glasanje? Ovo se ne može poništiti.")) return;
    await api.closeMeeting(id);
    load();
  }

  if (!meeting) return <div className="container">Učitavanje...</div>;

  const resultsByItem = {};
  (results || []).forEach((r) => (resultsByItem[r.agenda_item_id] = r));

  return (
    <div className="container">
      <span className={`badge ${meeting.status}`}>{meeting.status}</span>
      <h1>{meeting.title}</h1>
      <p>{new Date(meeting.scheduled_at).toLocaleString("sr-RS")}</p>
      {meeting.description && <p>{meeting.description}</p>}
      {error && <div className="error">{error}</div>}

      {user?.role === "admin" && meeting.status === "scheduled" && (
        <button onClick={handleActivate}>Otvori glasanje</button>
      )}
      {user?.role === "admin" && meeting.status === "active" && (
        <button className="danger" onClick={handleClose}>Zatvori glasanje i finalizuj</button>
      )}

      <h3>Dnevni red</h3>
      {meeting.agenda_items.map((item) => {
        const r = resultsByItem[item.id];
        return (
          <div key={item.id} className="card">
            <h4>{item.title}</h4>
            {item.description && <p>{item.description}</p>}

            {meeting.status === "active" && (
              <div className="vote-buttons">
                <button
                  onClick={() => handleVote(item.id, "for")}
                  style={{ background: myVotes[item.id] === "for" ? "#16a34a" : "#2563eb" }}
                >
                  Za
                </button>
                <button
                  onClick={() => handleVote(item.id, "against")}
                  style={{ background: myVotes[item.id] === "against" ? "#dc2626" : "#2563eb" }}
                >
                  Protiv
                </button>
                <button
                  onClick={() => handleVote(item.id, "abstain")}
                  className="secondary"
                >
                  Uzdržan
                </button>
              </div>
            )}

            {r && (
              <div style={{ marginTop: 10, fontSize: 14 }}>
                <p>Za: {r.for_percentage}% | Protiv: {r.against_percentage}% | Uzdržan: {r.abstain_percentage}%</p>
                <p>Kvorum: {r.quorum_reached ? "✅ Postignut" : "❌ Nije postignut"}</p>
                {meeting.status === "closed" && (
                  <p><strong>{r.passed ? "✅ ODLUKA JE DONETA" : "❌ Odluka nije doneta"}</strong></p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
